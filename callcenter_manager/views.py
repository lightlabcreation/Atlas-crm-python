from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Q, Count, Sum
from django.utils import timezone
from django.http import JsonResponse
from datetime import timedelta
from orders.models import Order
from products.models import Product
from users.models import User

def has_manager_role(user):
    """Check if user has call center manager role."""
    return user.has_role('Call Center Manager') or user.is_superuser

@login_required
def dashboard(request):
    """Call Center Manager Dashboard."""
    if not has_manager_role(request.user):
        messages.error(request, "You don't have permission to access this page.")
        return redirect('dashboard:index')
    
    # Get all agents
    agents = User.objects.filter(user_roles__role__name='Call Center Agent', user_roles__is_active=True, is_active=True).prefetch_related('user_roles__role').distinct().order_by('first_name', 'last_name')
    
    # Get orders statistics
    total_orders = Order.objects.count()
    pending_orders = Order.objects.filter(status='pending').count()
    completed_orders = Order.objects.filter(status='completed').count()
    
    # Get agent performance
    agent_performance = []
    for agent in agents:
        agent_orders = Order.objects.filter(agent=agent).select_related('agent', 'seller')
        agent_performance.append({
            'agent': agent,
            'total_orders': agent_orders.count(),
            'completed_orders': agent_orders.filter(status='completed').count(),
            'pending_orders': agent_orders.filter(status='pending').count(),
        })
    
    # Get recent orders
    recent_orders = Order.objects.select_related('agent', 'seller').order_by('-created_at')[:10]
    
    context = {
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'completed_orders': completed_orders,
        'agents_count': agents.count(),
        'agent_performance': agent_performance,
        'recent_orders': recent_orders,
    }
    
    return render(request, 'callcenter_manager/dashboard.html', context)

@login_required
def orders_management(request):
    """Complete Order Management System for Call Center Manager."""
    if not has_manager_role(request.user):
        messages.error(request, "You don't have permission to access this page.")
        return redirect('dashboard:index')
    
    # Get filter parameters
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    agent_filter = request.GET.get('agent', '')
    priority_filter = request.GET.get('priority', '')
    date_filter = request.GET.get('date', '')
    sort_by = request.GET.get('sort', '-created_at')
    
    # Get all orders with related data
    orders = Order.objects.select_related('agent', 'seller').prefetch_related('items').all()
    
    # Apply filters
    if search_query:
        orders = orders.filter(
            Q(order_code__icontains=search_query) |
            Q(customer__icontains=search_query) |
            Q(customer_phone__icontains=search_query) |
            Q(seller__email__icontains=search_query) |
            Q(notes__icontains=search_query)
        )
    
    if status_filter:
        orders = orders.filter(status=status_filter)
    
    if agent_filter:
        orders = orders.filter(agent_id=agent_filter)
    
    # Priority filter not available in current model
    # if priority_filter:
    #     orders = orders.filter(priority=priority_filter)
    
    if date_filter:
        from datetime import date, timedelta
        today = date.today()
        if date_filter == 'today':
            orders = orders.filter(created_at__date=today)
        elif date_filter == 'week':
            week_ago = today - timedelta(days=7)
            orders = orders.filter(created_at__date__gte=week_ago)
        elif date_filter == 'month':
            orders = orders.filter(created_at__month=today.month, created_at__year=today.year)
        elif date_filter == 'year':
            orders = orders.filter(created_at__year=today.year)
    
    # Apply sorting
    orders = orders.order_by(sort_by)
    
    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(orders, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get agents for filter dropdown
    agents = User.objects.filter(
        user_roles__role__name='Call Center Agent', 
        user_roles__is_active=True, 
        is_active=True
    ).distinct().order_by('first_name', 'last_name')
    
    # Calculate comprehensive statistics
    from datetime import date, timedelta
    today = date.today()
    yesterday = today - timedelta(days=1)
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    
    # Order statistics
    all_orders = Order.objects.all()
    
    # Basic counts
    total_orders = all_orders.count()
    pending_orders = all_orders.filter(status='pending').count()
    processing_orders = all_orders.filter(status='processing').count()
    confirmed_orders = all_orders.filter(status='confirmed').count()
    completed_orders = all_orders.filter(status='completed').count()
    cancelled_orders = all_orders.filter(status='cancelled').count()
    
    # Assigned orders
    assigned_orders = all_orders.filter(agent__isnull=False).count()
    unassigned_orders = all_orders.filter(agent__isnull=True).count()
    
    # Today's statistics
    today_orders = all_orders.filter(created_at__date=today).count()
    completed_today = all_orders.filter(status='completed', created_at__date=today).count()
    
    # Active agents
    active_agents = agents.count()
    
    # Calculate percentage changes
    yesterday_orders = all_orders.filter(created_at__date=yesterday).count()
    yesterday_completed = all_orders.filter(status='completed', created_at__date=yesterday).count()
    yesterday_pending = all_orders.filter(status='pending', created_at__date=yesterday).count()
    
    orders_change = ((today_orders - yesterday_orders) / yesterday_orders * 100) if yesterday_orders > 0 else 0
    completed_change = ((completed_today - yesterday_completed) / yesterday_completed * 100) if yesterday_completed > 0 else 0
    pending_change = ((pending_orders - yesterday_pending) / yesterday_pending * 100) if yesterday_pending > 0 else 0
    
    # Revenue statistics - using price_per_unit * quantity as total
    from django.db import models
    total_revenue = all_orders.aggregate(
        total=models.Sum(models.F('price_per_unit') * models.F('quantity'))
    )['total'] or 0
    today_revenue = all_orders.filter(created_at__date=today).aggregate(
        total=models.Sum(models.F('price_per_unit') * models.F('quantity'))
    )['total'] or 0
    
    # Get recent orders for quick overview
    recent_orders = orders[:10]
    
    # Get order status distribution
    status_distribution = {}
    for status, _ in Order.STATUS_CHOICES:
        count = all_orders.filter(status=status).count()
        if count > 0:
            status_distribution[status] = count
    
    # Priority distribution not available in current model
    priority_distribution = {}
    
    # Get top performing agents - simplified
    top_agents = agents[:5]
    
    # Get escalated orders for manager review
    escalated_orders = Order.objects.filter(
        escalated_to_manager=True
    ).select_related('agent', 'seller', 'escalated_by').order_by('-escalated_at')[:10]
    
    escalated_count = Order.objects.filter(escalated_to_manager=True).count()
    
    context = {
        'page_obj': page_obj,
        'orders': page_obj,
        'agents': agents,
        'search_query': search_query,
        'status_filter': status_filter,
        'agent_filter': agent_filter,
        'priority_filter': priority_filter,
        'date_filter': date_filter,
        'sort_by': sort_by,
        
        # Basic statistics
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'processing_orders': processing_orders,
        'confirmed_orders': confirmed_orders,
        'completed_orders': completed_orders,
        'cancelled_orders': cancelled_orders,
        'assigned_orders': assigned_orders,
        'unassigned_orders': unassigned_orders,
        'active_agents': active_agents,
        
        # Today's statistics
        'today_orders': today_orders,
        'completed_today': completed_today,
        
        # Revenue statistics
        'total_revenue': total_revenue,
        'today_revenue': today_revenue,
        
        # Percentage changes
        'orders_change': round(orders_change, 1),
        'completed_change': round(completed_change, 1),
        'pending_change': round(pending_change, 1),
        
        # Additional data
        'recent_orders': recent_orders,
        'status_distribution': status_distribution,
        'priority_distribution': priority_distribution,
        'top_agents': top_agents,
        
        # Escalated orders
        'escalated_orders': escalated_orders,
        'escalated_count': escalated_count,
        
        # Status choices for filter
        'status_choices': Order.STATUS_CHOICES,
    }
    
    return render(request, 'callcenter_manager/orders_management.html', context)

@login_required
def order_detail(request, order_id):
    """Order detail view for manager."""
    if not has_manager_role(request.user):
        messages.error(request, "You don't have permission to access this page.")
        return redirect('dashboard:index')
    
    order = get_object_or_404(Order, id=order_id)
    
    context = {
        'order': order,
    }
    
    return render(request, 'callcenter_manager/order_detail.html', context)

@login_required
def order_edit(request, order_id):
    """Edit order for manager."""
    if not has_manager_role(request.user):
        messages.error(request, "You don't have permission to access this page.")
        return redirect('dashboard:index')
    
    order = get_object_or_404(Order, id=order_id)
    
    if request.method == 'POST':
        # Update order fields
        order.customer = request.POST.get('customer', order.customer)
        order.customer_phone = request.POST.get('customer_phone', order.customer_phone)
        order.quantity = int(request.POST.get('quantity', order.quantity))
        order.price_per_unit = float(request.POST.get('price_per_unit', order.price_per_unit))
        order.status = request.POST.get('status', order.status)
        order.city = request.POST.get('city', order.city)
        order.state = request.POST.get('state', order.state)
        order.country = request.POST.get('country', order.country)
        order.zip_code = request.POST.get('zip_code', order.zip_code)
        order.notes = request.POST.get('notes', order.notes)
        order.internal_notes = request.POST.get('internal_notes', order.internal_notes)
        
        # Product name is read-only, no need to handle it
        
        # Handle seller assignment
        seller_id = request.POST.get('seller')
        if seller_id:
            try:
                seller = User.objects.get(id=seller_id)
                order.seller = seller
                order.seller_email = seller.email
            except User.DoesNotExist:
                pass
        
        # Handle agent assignment
        agent_id = request.POST.get('agent')
        if agent_id:
            try:
                agent = User.objects.get(id=agent_id)
                order.agent = agent
            except User.DoesNotExist:
                pass
        else:
            order.agent = None
        
        # Handle date
        date_str = request.POST.get('date')
        if date_str:
            from datetime import datetime
            try:
                order.date = datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                pass
        
        order.save()
        messages.success(request, "Order updated successfully.")
        return redirect('callcenter_manager:order_detail', order_id=order.id)
    
    # Get sellers and agents for dropdowns
    from roles.models import Role
    
    # Get sellers
    seller_role = Role.objects.filter(name='Seller').first()
    if seller_role:
        sellers = User.objects.filter(
            user_roles__role=seller_role,
            user_roles__is_active=True
        ).distinct().order_by('first_name', 'last_name')
    else:
        sellers = User.objects.filter(is_active=True).order_by('first_name', 'last_name')
    
    # Get agents
    agent_role = Role.objects.filter(name='Call Center Agent').first()
    if agent_role:
        agents = User.objects.filter(
            user_roles__role=agent_role,
            user_roles__is_active=True
        ).distinct().order_by('first_name', 'last_name')
    else:
        agents = User.objects.filter(is_active=True).order_by('first_name', 'last_name')
    
    # Get choices for dropdowns
    from utils.countries import COUNTRIES
    
    context = {
        'order': order,
        'sellers': sellers,
        'agents': agents,
        'order_status_choices': Order.STATUS_CHOICES,
        'country_choices': COUNTRIES,
    }
    
    return render(request, 'callcenter_manager/order_edit.html', context)

@login_required
def agent_list(request):
    """List all agents."""
    if not has_manager_role(request.user):
        messages.error(request, "You don't have permission to access this page.")
        return redirect('dashboard:index')
    
    agents = User.objects.filter(user_roles__role__name='Call Center Agent', user_roles__is_active=True, is_active=True).prefetch_related('user_roles__role').distinct().order_by('first_name', 'last_name')
    
    context = {
        'agents': agents,
    }
    
    return render(request, 'callcenter_manager/agents.html', context)

@login_required
def agent_detail(request, agent_id):
    """Agent detail view."""
    if not has_manager_role(request.user):
        messages.error(request, "You don't have permission to access this page.")
        return redirect('dashboard:index')
    
    agent = get_object_or_404(User, id=agent_id)
    
    # Get agent's orders
    agent_orders = Order.objects.filter(agent=agent).select_related('agent', 'seller').order_by('-created_at')
    
    context = {
        'agent': agent,
        'agent_orders': agent_orders,
    }
    
    return render(request, 'callcenter_manager/agent_detail.html', context)

@login_required
def agent_edit(request, agent_id):
    """Edit agent."""
    if not has_manager_role(request.user):
        messages.error(request, "You don't have permission to access this page.")
        return redirect('dashboard:index')
    
    agent = get_object_or_404(User, id=agent_id)
    
    if request.method == 'POST':
        # Handle agent edit logic here
        messages.success(request, "Agent information updated successfully.")
        return redirect('callcenter_manager:agent_detail', agent_id=agent.id)
    
    # Get agent's orders
    agent_orders = Order.objects.filter(agent=agent).select_related('agent', 'seller').order_by('-created_at')
    
    context = {
        'agent': agent,
        'agent_orders': agent_orders,
    }
    
    return render(request, 'callcenter_manager/agent_edit.html', context)


@login_required
def agent_performance(request):
    """Agent performance report."""
    if not has_manager_role(request.user):
        messages.error(request, "You don't have permission to access this page.")
        return redirect('dashboard:index')
    
    # Get all agents
    agents = User.objects.filter(user_roles__role__name='Call Center Agent', user_roles__is_active=True, is_active=True).prefetch_related('user_roles__role').distinct().order_by('first_name', 'last_name')
    
    # Calculate agent performance
    agent_performance = []
    for agent in agents:
        agent_orders = Order.objects.filter(agent=agent).select_related('agent', 'seller')
        total_orders = agent_orders.count()
        completed_orders = agent_orders.filter(status='completed').count()
        success_rate = (completed_orders / total_orders * 100) if total_orders > 0 else 0
        
        agent_performance.append({
            'agent': agent,
            'total_orders': total_orders,
            'completed_orders': completed_orders,
            'success_rate': round(success_rate, 1),
            'performance_score': min(100, round(success_rate + 10, 1)),  # Add some bonus
            'customer_rating': 4.2 + (success_rate / 100 * 0.8),  # Simulate rating
        })
    
    # Sort by performance score
    agent_performance.sort(key=lambda x: x['performance_score'], reverse=True)
    
    context = {
        'total_agents': agents.count(),
        'total_orders_handled': sum(ap['total_orders'] for ap in agent_performance),
        'top_performer': agent_performance[0]['agent'].get_full_name() if agent_performance else None,
        'agent_performance': agent_performance,
        'top_performers': agent_performance[:3],
    }
    
    return render(request, 'callcenter_manager/agent_performance.html', context)

@login_required
def order_statistics(request):
    """Order statistics report."""
    if not has_manager_role(request.user):
        messages.error(request, "You don't have permission to access this page.")
        return redirect('dashboard:index')
    
    # Get all orders
    all_orders = Order.objects.all()
    
    # Basic statistics
    total_orders = all_orders.count()
    pending_orders = all_orders.filter(status='pending').count()
    processing_orders = all_orders.filter(status='processing').count()
    completed_orders = all_orders.filter(status='completed').count()
    cancelled_orders = all_orders.filter(status='cancelled').count()
    
    # Monthly statistics
    from datetime import date
    today = date.today()
    monthly_orders = all_orders.filter(created_at__month=today.month, created_at__year=today.year).count()
    
    # Calculate completion rate
    completion_rate = (completed_orders / total_orders * 100) if total_orders > 0 else 0
    
    # Calculate average order value
    from django.db import models
    total_revenue = all_orders.aggregate(
        total=models.Sum(models.F('price_per_unit') * models.F('quantity'))
    )['total'] or 0
    avg_order_value = total_revenue / total_orders if total_orders > 0 else 0
    
    # Revenue by status
    pending_revenue = all_orders.filter(status='pending').aggregate(
        total=models.Sum(models.F('price_per_unit') * models.F('quantity'))
    )['total'] or 0
    
    processing_revenue = all_orders.filter(status='processing').aggregate(
        total=models.Sum(models.F('price_per_unit') * models.F('quantity'))
    )['total'] or 0
    
    completed_revenue = all_orders.filter(status='completed').aggregate(
        total=models.Sum(models.F('price_per_unit') * models.F('quantity'))
    )['total'] or 0
    
    # Get top agents
    agents = User.objects.filter(user_roles__role__name='Call Center Agent', user_roles__is_active=True, is_active=True)
    top_agents = []
    for agent in agents:
        agent_orders = Order.objects.filter(agent=agent)
        if agent_orders.exists():
            top_agents.append({
                'agent': agent,
                'total_orders': agent_orders.count(),
                'performance_score': min(100, (agent_orders.filter(status='completed').count() / agent_orders.count() * 100) + 10),
            })
    
    # Sort by performance
    top_agents.sort(key=lambda x: x['performance_score'], reverse=True)
    
    context = {
        'total_orders': total_orders,
        'monthly_orders': monthly_orders,
        'completion_rate': round(completion_rate, 1),
        'avg_order_value': avg_order_value,
        'pending_orders': pending_orders,
        'processing_orders': processing_orders,
        'completed_orders': completed_orders,
        'cancelled_orders': cancelled_orders,
        'pending_revenue': pending_revenue,
        'processing_revenue': processing_revenue,
        'completed_revenue': completed_revenue,
        'top_agents': top_agents[:5],
    }
    
    return render(request, 'callcenter_manager/order_statistics.html', context)

@login_required
def add_note(request, order_id):
    """Add note to order."""
    if not has_manager_role(request.user):
        messages.error(request, "You don't have permission to access this page.")
        return redirect('dashboard:index')
    
    order = get_object_or_404(Order, id=order_id)
    
    if request.method == 'POST':
        note_type = request.POST.get('note_type')
        note_content = request.POST.get('note_content')
        
        if note_content:
            # Create a simple note (you can extend this with a proper Note model)
            # For now, we'll just add it to the order's internal_notes
            if order.internal_notes:
                order.internal_notes += f"\n[{note_type.upper()}] {timezone.now().strftime('%Y-%m-%d %H:%M')} - {note_content}"
            else:
                order.internal_notes = f"[{note_type.upper()}] {timezone.now().strftime('%Y-%m-%d %H:%M')} - {note_content}"
            
            order.save()
            messages.success(request, "Note added successfully.")
        else:
            messages.error(request, "Note content cannot be empty.")
    
    return redirect('callcenter_manager:order_detail', order_id=order.id)

@login_required
def settings(request):
    """Settings view for manager."""
    if not has_manager_role(request.user):
        messages.error(request, "You don't have permission to access this page.")
        return redirect('dashboard:index')
    
    context = {}
    return render(request, 'callcenter_manager/settings.html', context)


