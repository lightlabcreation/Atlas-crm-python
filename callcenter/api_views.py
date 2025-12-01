# callcenter/api_views.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Count, Sum, Avg, Q
from django.core.paginator import Paginator
from datetime import datetime, timedelta
import json

from .models import (
    CallLog, AgentPerformance, AgentSession, CustomerInteraction,
    OrderStatusHistory, OrderAssignment, ManagerNote, TeamPerformance
)
from .services import OrderDistributionService, AutoOrderDistributionService
from orders.models import Order, StatusLog
from users.models import User
from inventory.models import Stock

def is_call_center_agent(user):
    """Check if user is a call center agent."""
    return user.has_role('Call Center Agent') or user.is_superuser

def is_call_center_manager(user):
    """Check if user is a call center manager."""
    return user.has_role('Call Center Manager') or user.is_superuser

def has_callcenter_role(user):
    return (
        user.is_superuser or
        user.has_role('Super Admin') or
        user.has_role('Admin') or
        user.has_role('Call Center Manager') or
        user.has_role('Call Center Agent')
    )

# Dashboard APIs

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_stats(request):
    """Get dashboard statistics for call center."""
    if not has_callcenter_role(request.user):
        return Response({'error': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)
    
    today = timezone.now().date()
    
    # Get basic stats
    total_orders = Order.objects.count()
    pending_orders = Order.objects.filter(status='pending').count()
    confirmed_orders = Order.objects.filter(status='confirmed').count()
    cancelled_orders = Order.objects.filter(status='cancelled').count()
    
    # Get agent stats
    active_agents = AgentSession.objects.filter(status='available').count()
    total_agents = User.objects.filter(user_roles__role__name='Call Center Agent').count()
    
    # Get today's performance
    today_performance = AgentPerformance.objects.filter(date=today).aggregate(
        total_calls=Sum('total_calls_made'),
        successful_calls=Sum('successful_calls'),
        avg_satisfaction=Avg('customer_satisfaction_avg')
    )
    
    return Response({
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'confirmed_orders': confirmed_orders,
        'cancelled_orders': cancelled_orders,
        'active_agents': active_agents,
        'total_agents': total_agents,
        'today_calls': today_performance['total_calls'] or 0,
        'today_successful_calls': today_performance['successful_calls'] or 0,
        'avg_satisfaction': round(today_performance['avg_satisfaction'] or 0, 2)
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def agent_dashboard_stats(request):
    """Get agent dashboard statistics."""
    if not has_callcenter_role(request.user):
        return Response({'error': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)
    
    today = timezone.now().date()
    
    # Get or create agent session
    session, created = AgentSession.objects.get_or_create(
        agent=request.user,
        defaults={'status': 'available'}
    )
    
    # Get today's performance
    performance, created = AgentPerformance.objects.get_or_create(
        agent=request.user, 
        date=today,
        defaults={
            'total_calls_made': 0,
            'successful_calls': 0,
            'orders_confirmed': 0,
            'orders_cancelled': 0,
            'orders_postponed': 0,
            'total_orders_handled': 0,
        }
    )
    
    # Get assigned orders
    assignment_order_ids = list(OrderAssignment.objects.filter(
        agent=request.user
    ).values_list('order_id', flat=True))
    
    direct_order_ids = list(Order.objects.filter(
        agent=request.user
    ).values_list('id', flat=True))
    
    all_order_ids = list(set(assignment_order_ids + direct_order_ids))
    
    assigned_orders = Order.objects.filter(id__in=all_order_ids)
    
    # Get order counts
    pending_orders = assigned_orders.filter(status='pending').count()
    processing_orders = assigned_orders.filter(status='processing').count()
    confirmed_orders = assigned_orders.filter(status='confirmed').count()
    
    # Get recent calls
    recent_calls = CallLog.objects.filter(
        agent=request.user,
        call_time__date=today
    ).order_by('-call_time')[:5]
    
    # Get unread manager notes
    unread_notes = ManagerNote.objects.filter(
        agent=request.user,
        is_read_by_agent=False
    ).count()
    
    return Response({
        'session_status': session.status,
        'performance': {
            'total_calls_made': performance.total_calls_made,
            'successful_calls': performance.successful_calls,
            'orders_confirmed': performance.orders_confirmed,
            'orders_cancelled': performance.orders_cancelled,
            'orders_postponed': performance.orders_postponed,
            'total_orders_handled': performance.total_orders_handled,
            'average_call_duration': float(performance.average_call_duration),
            'resolution_rate': float(performance.resolution_rate),
            'customer_satisfaction_avg': float(performance.customer_satisfaction_avg)
        },
        'orders': {
            'pending': pending_orders,
            'processing': processing_orders,
            'confirmed': confirmed_orders,
            'total': assigned_orders.count()
        },
        'recent_calls': [
            {
                'id': str(call.id),
                'order_id': call.order.id,
                'call_time': call.call_time,
                'duration': call.duration,
                'status': call.status,
                'customer_satisfaction': call.customer_satisfaction
            } for call in recent_calls
        ],
        'unread_notes': unread_notes
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def manager_dashboard_stats(request):
    """Get manager dashboard statistics."""
    if not is_call_center_manager(request.user):
        return Response({'error': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)
    
    today = timezone.now().date()
    
    # Get team performance
    team_performance = TeamPerformance.objects.filter(date=today).first()
    
    # Get agent performance
    agent_performances = AgentPerformance.objects.filter(date=today)
    
    # Get order distribution stats
    total_assignments = OrderAssignment.objects.filter(assignment_date__date=today).count()
    unassigned_orders = Order.objects.filter(
        status='pending',
        agent__isnull=True
    ).count()
    
    # Get escalation stats
    escalated_orders = Order.objects.filter(
        status='escalated'
    ).count()
    
    return Response({
        'team_performance': {
            'total_agents': team_performance.total_agents if team_performance else 0,
            'orders_handled': team_performance.orders_handled if team_performance else 0,
            'orders_confirmed': team_performance.orders_confirmed if team_performance else 0,
            'orders_cancelled': team_performance.orders_cancelled if team_performance else 0,
            'average_handle_time': float(team_performance.average_handle_time) if team_performance else 0,
            'team_confirmation_rate': float(team_performance.team_confirmation_rate) if team_performance else 0,
            'team_satisfaction_avg': float(team_performance.team_satisfaction_avg) if team_performance else 0
        },
        'distribution': {
            'total_assignments': total_assignments,
            'unassigned_orders': unassigned_orders,
            'escalated_orders': escalated_orders
        },
        'agent_performances': [
            {
                'agent_id': perf.agent.id,
                'agent_name': perf.agent.get_full_name(),
                'total_calls_made': perf.total_calls_made,
                'successful_calls': perf.successful_calls,
                'orders_confirmed': perf.orders_confirmed,
                'resolution_rate': float(perf.resolution_rate),
                'customer_satisfaction_avg': float(perf.customer_satisfaction_avg)
            } for perf in agent_performances
        ]
    })

# Order Management APIs

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def order_list(request):
    """Get list of orders with pagination and filtering."""
    if not has_callcenter_role(request.user):
        return Response({'error': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)
    
    # Get query parameters
    page = request.GET.get('page', 1)
    status_filter = request.GET.get('status')
    priority_filter = request.GET.get('priority')
    search = request.GET.get('search')
    
    # Base queryset
    if is_call_center_manager(request.user):
        orders = Order.objects.all()
    else:
        # Agent can only see assigned orders
        assignment_order_ids = list(OrderAssignment.objects.filter(
            agent=request.user
        ).values_list('order_id', flat=True))
        
        direct_order_ids = list(Order.objects.filter(
            agent=request.user
        ).values_list('id', flat=True))
        
        all_order_ids = list(set(assignment_order_ids + direct_order_ids))
        orders = Order.objects.filter(id__in=all_order_ids)
    
    # Apply filters
    if status_filter:
        orders = orders.filter(status=status_filter)
    
    if priority_filter:
        orders = orders.filter(priority=priority_filter)
    
    if search:
        orders = orders.filter(
            Q(id__icontains=search) |
            Q(customer__first_name__icontains=search) |
            Q(customer__last_name__icontains=search) |
            Q(customer__email__icontains=search)
        )
    
    # Pagination
    paginator = Paginator(orders.order_by('-created_at'), 20)
    try:
        orders_page = paginator.page(page)
    except (PageNotAnInteger, EmptyPage):
        orders_page = paginator.page(1)
    
    return Response({
        'orders': [
            {
                'id': order.id,
                'customer_name': order.customer.get_full_name(),
                'customer_email': order.customer.email,
                'status': order.status,
                'priority': order.priority,
                'total_amount': float(order.total_amount),
                'created_at': order.created_at,
                'assigned_agent': order.agent.get_full_name() if order.agent else None,
                'assignment_date': order.assignments.first().assignment_date if order.assignments.exists() else None
            } for order in orders_page
        ],
        'pagination': {
            'current_page': orders_page.number,
            'total_pages': paginator.num_pages,
            'total_count': paginator.count,
            'has_next': orders_page.has_next(),
            'has_previous': orders_page.has_previous()
        }
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def order_detail(request, order_id):
    """Get detailed information about a specific order."""
    if not has_callcenter_role(request.user):
        return Response({'error': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)
    
    order = get_object_or_404(Order, id=order_id)
    
    # Check if agent can access this order
    if not is_call_center_manager(request.user):
        assignment_exists = OrderAssignment.objects.filter(
            order=order,
            agent=request.user
        ).exists()
        
        if not assignment_exists and order.agent != request.user:
            return Response({'error': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)
    
    # Get order details
    order_data = {
        'id': order.id,
        'customer': {
            'id': order.customer.id,
            'name': order.customer.get_full_name(),
            'email': order.customer.email,
            'phone': order.customer.phone
        },
        'status': order.status,
        'priority': order.priority,
        'total_amount': float(order.total_amount),
        'created_at': order.created_at,
        'updated_at': order.updated_at,
        'items': [
            {
                'id': item.id,
                'product_name': item.product.name,
                'quantity': item.quantity,
                'price': float(item.price),
                'total': float(item.total)
            } for item in order.items.all()
        ],
        'status_history': [
            {
                'id': log.id,
                'previous_status': log.previous_status,
                'new_status': log.new_status,
                'change_timestamp': log.change_timestamp,
                'changed_by': log.changed_by.get_full_name() if log.changed_by else None
            } for log in order.status_history.all()
        ],
        'call_logs': [
            {
                'id': str(log.id),
                'call_time': log.call_time,
                'duration': log.duration,
                'status': log.status,
                'notes': log.notes,
                'customer_satisfaction': log.customer_satisfaction,
                'resolution_status': log.resolution_status
            } for log in order.call_logs.all()
        ],
        'manager_notes': [
            {
                'id': note.id,
                'note_text': note.note_text,
                'note_type': note.note_type,
                'is_urgent': note.is_urgent,
                'created_at': note.created_at,
                'manager': note.manager.get_full_name()
            } for note in order.manager_notes.all()
        ]
    }
    
    return Response(order_data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_order_status(request, order_id):
    """Update order status."""
    if not has_callcenter_role(request.user):
        return Response({'error': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)
    
    order = get_object_or_404(Order, id=order_id)
    
    # Check permissions
    if not is_call_center_manager(request.user):
        assignment_exists = OrderAssignment.objects.filter(
            order=order,
            agent=request.user
        ).exists()
        
        if not assignment_exists and order.agent != request.user:
            return Response({'error': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)
    
    new_status = request.data.get('status')
    reason = request.data.get('reason', '')
    
    if not new_status:
        return Response({'error': 'Status is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    # Update order status
    previous_status = order.status
    order.status = new_status
    order.save()
    
    # Create status log
    StatusLog.objects.create(
        order=order,
        previous_status=previous_status,
        new_status=new_status,
        changed_by=request.user,
        reason=reason
    )
    
    return Response({
        'success': True,
        'message': 'Order status updated successfully',
        'order': {
            'id': order.id,
            'status': order.status
        }
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def log_call(request, order_id):
    """Log a call for an order."""
    if not has_callcenter_role(request.user):
        return Response({'error': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)
    
    order = get_object_or_404(Order, id=order_id)
    
    # Check permissions
    if not is_call_center_manager(request.user):
        assignment_exists = OrderAssignment.objects.filter(
            order=order,
            agent=request.user
        ).exists()
        
        if not assignment_exists and order.agent != request.user:
            return Response({'error': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)
    
    # Create call log
    call_log = CallLog.objects.create(
        order=order,
        agent=request.user,
        duration=request.data.get('duration', 0),
        status=request.data.get('status', 'completed'),
        notes=request.data.get('notes', ''),
        customer_satisfaction=request.data.get('customer_satisfaction'),
        resolution_status=request.data.get('resolution_status', 'pending'),
        escalation_reason=request.data.get('escalation_reason', ''),
        follow_up_date=request.data.get('follow_up_date')
    )
    
    return Response({
        'success': True,
        'message': 'Call logged successfully',
        'call_log': {
            'id': str(call_log.id),
            'call_time': call_log.call_time,
            'duration': call_log.duration,
            'status': call_log.status,
            'notes': call_log.notes,
            'customer_satisfaction': call_log.customer_satisfaction,
            'resolution_status': call_log.resolution_status
        }
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def assign_order(request, order_id):
    """Assign order to an agent (Manager only)."""
    if not is_call_center_manager(request.user):
        return Response({'error': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)
    
    order = get_object_or_404(Order, id=order_id)
    agent_id = request.data.get('agent_id')
    priority_level = request.data.get('priority_level', 'medium')
    manager_notes = request.data.get('manager_notes', '')
    
    if not agent_id:
        return Response({'error': 'Agent ID is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    agent = get_object_or_404(User, id=agent_id)
    
    # Check if agent has call center role
    if not agent.has_role('Call Center Agent'):
        return Response({'error': 'Selected user is not a call center agent'}, status=status.HTTP_400_BAD_REQUEST)
    
    # Create assignment
    assignment = OrderAssignment.objects.create(
        order=order,
        manager=request.user,
        agent=agent,
        priority_level=priority_level,
        manager_notes=manager_notes,
        assignment_reason=request.data.get('assignment_reason', '')
    )
    
    # Update order agent
    order.agent = agent
    order.save()
    
    return Response({
        'success': True,
        'message': 'Order assigned successfully',
        'assignment': {
            'id': assignment.id,
            'order_id': order.id,
            'agent_name': agent.get_full_name(),
            'priority_level': priority_level,
            'assignment_date': assignment.assignment_date
        }
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def distribute_orders(request):
    """Distribute orders to agents (Manager only)."""
    if not is_call_center_manager(request.user):
        return Response({'error': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)
    
    try:
        # Auto distribute orders
        service = AutoOrderDistributionService()
        result = service.distribute_orders()
        
        return Response({
            'success': True,
            'message': f'Successfully distributed {result["distributed_count"]} orders',
            'distributed_count': result['distributed_count']
        })
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Error distributing orders: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Agent Session Management

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_agent_status(request):
    """Update agent session status."""
    if not has_callcenter_role(request.user):
        return Response({'error': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)
    
    status = request.data.get('status')
    if not status:
        return Response({'error': 'Status is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    # Get or create session
    session, created = AgentSession.objects.get_or_create(
        agent=request.user,
        defaults={'status': status}
    )
    
    # Update status
    session.status = status
    session.save()
    
    return Response({
        'success': True,
        'message': 'Agent status updated successfully',
        'status': session.status
    })

# Reports APIs

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def agent_performance_report(request):
    """Get agent performance report."""
    if not is_call_center_manager(request.user):
        return Response({'error': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)
    
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    if not start_date or not end_date:
        return Response({'error': 'Start date and end date are required'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    except ValueError:
        return Response({'error': 'Invalid date format'}, status=status.HTTP_400_BAD_REQUEST)
    
    performances = AgentPerformance.objects.filter(
        date__range=[start_date, end_date]
    ).order_by('-date')
    
    return Response({
        'performances': [
            {
                'agent_id': perf.agent.id,
                'agent_name': perf.agent.get_full_name(),
                'date': perf.date,
                'total_calls_made': perf.total_calls_made,
                'successful_calls': perf.successful_calls,
                'orders_confirmed': perf.orders_confirmed,
                'orders_cancelled': perf.orders_cancelled,
                'orders_postponed': perf.orders_postponed,
                'total_orders_handled': perf.total_orders_handled,
                'average_call_duration': float(perf.average_call_duration),
                'resolution_rate': float(perf.resolution_rate),
                'first_call_resolution_rate': float(perf.first_call_resolution_rate),
                'customer_satisfaction_avg': float(perf.customer_satisfaction_avg),
                'total_work_time_minutes': perf.total_work_time_minutes,
                'break_time_minutes': perf.break_time_minutes
            } for perf in performances
        ]
    })


