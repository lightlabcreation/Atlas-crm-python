from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Q, Count, Avg, Sum, F
from django.contrib.auth import get_user_model
from datetime import datetime, timedelta
import json
import math

from .models import (
    DeliveryCompany, Courier, DeliveryRecord, DeliveryStatusHistory,
    DeliveryAttempt, CourierSession, CourierLocation, DeliveryProof,
    DeliveryRoute, DeliveryPerformance
)
from orders.models import Order
from users.models import User
from products.models import Product

User = get_user_model()

def calculate_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the distance between two points using Haversine formula
    Returns distance in kilometers
    """
    try:
        # Convert decimal degrees to radians
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        
        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        # Radius of earth in kilometers
        r = 6371
        
        return c * r
    except:
        return 0

def calculate_delivery_distance(delivery):
    """
    Calculate delivery distance based on courier locations
    """
    try:
        if not delivery.courier:
            return 0
            
        # Get courier locations for this delivery
        locations = CourierLocation.objects.filter(
            courier=delivery.courier,
            timestamp__range=[delivery.picked_up_at or delivery.assigned_at, delivery.delivered_at or timezone.now()]
        ).order_by('timestamp')
        
        if locations.count() < 2:
            return 0
            
        total_distance = 0
        prev_location = None
        
        for location in locations:
            if prev_location:
                distance = calculate_distance(
                    prev_location.latitude, prev_location.longitude,
                    location.latitude, location.longitude
                )
                total_distance += distance
            prev_location = location
            
        return total_distance
    except:
        return 0

@csrf_exempt
@require_http_methods(["GET"])
def delivery_dashboard_stats(request):
    """API endpoint for delivery dashboard statistics"""
    try:
        today = timezone.now().date()
        start_date = request.GET.get('start_date', today)
        end_date = request.GET.get('end_date', today)
        
        # Parse dates
        try:
            if isinstance(start_date, str):
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            if isinstance(end_date, str):
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        except ValueError:
            start_date = today
            end_date = today
        
        # Get delivery statistics from DeliveryRecord model
        deliveries = DeliveryRecord.objects.all()
        date_range_deliveries = deliveries.filter(assigned_at__date__range=[start_date, end_date])
        
        # Calculate real statistics
        total_deliveries = date_range_deliveries.count()
        successful_deliveries = date_range_deliveries.filter(status='delivered').count()
        failed_deliveries = date_range_deliveries.filter(status='failed').count()
        success_rate = (successful_deliveries / total_deliveries * 100) if total_deliveries > 0 else 0
        
        # Get active deliveries
        active_deliveries = date_range_deliveries.filter(
            status__in=['assigned', 'accepted', 'picked_up', 'in_transit', 'out_for_delivery']
        ).count()
        
        # Get completed today
        completed_today = date_range_deliveries.filter(status='delivered').count()
        
        # Get average rating across all couriers
        avg_rating = Courier.objects.aggregate(avg_rating=Avg('rating'))['avg_rating'] or 0
        
        # Get performance data from DeliveryPerformance model
        try:
            performance_data = DeliveryPerformance.objects.filter(
                date__range=[start_date, end_date]
            ).aggregate(
                total_distance=Sum('total_distance'),
                total_time=Sum('total_time'),
                avg_delivery_time=Avg('average_delivery_time')
            )
            
            avg_delivery_time = performance_data['avg_delivery_time'] or 0
            total_distance = performance_data['total_distance'] or 0
        except:
            # Fallback: calculate from DeliveryRecord model
            try:
                # Calculate average delivery time from actual delivery records
                completed_deliveries = DeliveryRecord.objects.filter(
                    status='delivered',
                    assigned_at__date__range=[start_date, end_date],
                    picked_up_at__isnull=False,
                    delivered_at__isnull=False
                )
                
                if completed_deliveries.exists():
                    total_time_minutes = 0
                    total_calculated_distance = 0
                    
                    for delivery in completed_deliveries:
                        # Calculate delivery time
                        delivery_time = delivery.delivered_at - delivery.picked_up_at
                        total_time_minutes += delivery_time.total_seconds() / 60
                        
                        # Calculate delivery distance
                        delivery_distance = calculate_delivery_distance(delivery)
                        total_calculated_distance += delivery_distance
                    
                    avg_delivery_time = total_time_minutes / completed_deliveries.count()
                    
                    # Use calculated distance if available, otherwise fallback to route data
                    if total_calculated_distance > 0:
                        total_distance = total_calculated_distance
                    else:
                        # Calculate total distance from DeliveryRoute model
                        try:
                            route_distance = DeliveryRoute.objects.filter(
                                route_date__range=[start_date, end_date]
                            ).aggregate(total=Sum('total_distance'))['total'] or 0
                            total_distance = route_distance
                        except:
                            # If no route data, estimate from delivery count
                            total_distance = total_deliveries * 10.0  # Estimate 10km per delivery
                else:
                    avg_delivery_time = 0
                    total_distance = 0
                    
            except:
                avg_delivery_time = 0
                total_distance = 0
        
        # Get order statistics from Order model
        total_orders = Order.objects.count()
        pending_orders = Order.objects.filter(status='pending').count()
        confirmed_orders = Order.objects.filter(status='confirmed').count()
        processing_orders = Order.objects.filter(status='processing').count()
        delivered_orders = Order.objects.filter(status='delivered').count()
        shipped_orders = Order.objects.filter(status='shipped').count()
        
        # Get delivery companies and couriers
        delivery_companies_count = DeliveryCompany.objects.filter(is_active=True).count()
        active_couriers_count = Courier.objects.filter(status='active').count()
        
        # Get recent deliveries from DeliveryRecord model
        recent_deliveries = list(DeliveryRecord.objects.select_related(
            'order', 'courier'
        ).order_by('-assigned_at')[:10].values(
            'id', 'status', 'assigned_at', 'order__order_code', 'courier__user__full_name'
        ))
        
        # Get recent orders from Order model
        recent_orders = list(Order.objects.select_related('product').order_by('-date')[:5].values(
            'id', 'order_code', 'status', 'date', 'product__name_en'
        ))
        
        # Get current tasks for delivery agents from Order model
        try:
            orders_ready_for_delivery = Order.objects.filter(
                workflow_status='packaging_completed',
                status__in=['confirmed', 'processing']
            ).select_related('product').order_by('-date')[:5]
            
            orders_in_delivery = Order.objects.filter(
                workflow_status='delivery_in_progress'
            ).select_related('product').order_by('-date')[:5]
        except:
            # Fallback to status-based filtering
            orders_ready_for_delivery = Order.objects.filter(
                status__in=['confirmed', 'processing']
            ).select_related('product').order_by('-date')[:5]
            
            orders_in_delivery = Order.objects.filter(
                status='processing'
            ).select_related('product').order_by('-date')[:5]
        
        # Format current tasks
        current_task = None
        if orders_ready_for_delivery:
            first_order = orders_ready_for_delivery[0]
            current_task = {
                'id': first_order.id,
                'order_code': first_order.order_code,
                'status': first_order.status,
                'date': first_order.date.isoformat() if first_order.date else None,
                'product_name': first_order.product.name_en if first_order.product else 'N/A'
            }
        
        # Format next deliveries
        next_deliveries = []
        for order in orders_ready_for_delivery[:5]:
            next_deliveries.append({
                'id': order.id,
                'order_code': order.order_code,
                'status': order.status,
                'date': order.date.isoformat() if order.date else None,
                'product_name': order.product.name_en if order.product else 'N/A'
            })
        
        # Get delivery performance metrics from Order model
        try:
            orders_ready_for_delivery_count = Order.objects.filter(
                workflow_status='packaging_completed',
                status__in=['confirmed', 'processing']
            ).count()
            
            orders_in_delivery_count = Order.objects.filter(
                workflow_status='delivery_in_progress'
            ).count()
            
            orders_delivered_count = Order.objects.filter(
                workflow_status='delivery_completed'
            ).count()
        except:
            # Fallback to status-based counting
            orders_ready_for_delivery_count = Order.objects.filter(
                status__in=['confirmed', 'processing']
            ).count()
            
            orders_in_delivery_count = Order.objects.filter(
                status='processing'
            ).count()
            
            orders_delivered_count = Order.objects.filter(
                status='shipped'
            ).count()
        
        delivery_performance = {
            'orders_ready': orders_ready_for_delivery_count,
            'orders_in_progress': orders_in_delivery_count,
            'orders_completed': orders_delivered_count,
            'efficiency_rate': (orders_delivered_count / max(total_orders, 1)) * 100,
        }
        
        # Get recent activity from DeliveryStatusHistory model
        recent_activity = list(DeliveryStatusHistory.objects.select_related(
            'delivery', 'changed_by'
        ).order_by('-timestamp')[:10].values(
            'id', 'status', 'timestamp', 'delivery__order__order_code', 'changed_by__full_name'
        ))
        
        # If no real data exists, try to get data from other sources
        if total_deliveries == 0:
            # Try to get data from Order model for delivery-related orders
            delivery_orders = Order.objects.filter(
                status__in=['processing', 'shipped', 'delivered']
            )
            if delivery_orders.exists():
                total_deliveries = delivery_orders.count()
                successful_deliveries = delivery_orders.filter(status='delivered').count()
                failed_deliveries = delivery_orders.filter(status='cancelled').count()
                success_rate = (successful_deliveries / total_deliveries * 100) if total_deliveries > 0 else 0
                active_deliveries = delivery_orders.filter(status='processing').count()
                completed_today = delivery_orders.filter(
                    date__date=today,
                    status='delivered'
                ).count()
        
        response_data = {
            'success': True,
            'data': {
                'statistics': {
                    'total_deliveries': total_deliveries,
                    'successful_deliveries': successful_deliveries,
                    'failed_deliveries': failed_deliveries,
                    'success_rate': round(success_rate, 1),
                    'active_deliveries': active_deliveries,
                    'completed_today': completed_today,
                    'avg_rating': round(avg_rating, 1),
                    'avg_delivery_time': round(avg_delivery_time, 0),
                    'total_distance': round(total_distance, 1),
                },
                'orders': {
                    'total_orders': total_orders,
                    'pending_orders': pending_orders,
                    'confirmed_orders': confirmed_orders,
                    'processing_orders': processing_orders,
                    'delivered_orders': delivered_orders,
                    'shipped_orders': shipped_orders,
                },
                'system': {
                    'delivery_companies_count': delivery_companies_count,
                    'active_couriers_count': active_couriers_count,
                },
                'current_task': current_task,
                'next_deliveries': next_deliveries,
                'recent_deliveries': recent_deliveries,
                'recent_orders': recent_orders,
                'recent_activity': recent_activity,
                'delivery_performance': delivery_performance,
                'date_range': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat(),
                }
            }
        }
        
        return JsonResponse(response_data)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def delivery_orders_stats(request):
    """API endpoint for delivery orders statistics"""
    try:
        # Get filter parameters
        status_filter = request.GET.get('status', '')
        search_query = request.GET.get('search', '')
        date_filter = request.GET.get('date', '')
        
        # Get orders that need delivery from Order model
        orders = Order.objects.filter(
            status__in=['confirmed', 'processing', 'shipped']
        ).select_related('product', 'seller').order_by('-date')
        
        # Apply filters
        if status_filter:
            orders = orders.filter(status=status_filter)
        
        if search_query:
            orders = orders.filter(
                Q(order_code__icontains=search_query) |
                Q(customer__icontains=search_query) |
                Q(customer_phone__icontains=search_query) |
                Q(product__name_en__icontains=search_query)
            )
        
        if date_filter:
            today = timezone.now().date()
            if date_filter == 'today':
                orders = orders.filter(date__date=today)
            elif date_filter == 'week':
                week_ago = today - timedelta(days=7)
                orders = orders.filter(date__date__gte=week_ago)
            elif date_filter == 'month':
                orders = orders.filter(date__month=today.month, date__year=today.year)
        
        # Calculate statistics
        total_orders = orders.count()
        pending_orders = orders.filter(status='confirmed').count()
        processing_orders = orders.filter(status='processing').count()
        shipped_orders = orders.filter(status='shipped').count()
        
        # Get workflow-based statistics from Order model
        try:
            orders_ready_for_delivery = orders.filter(workflow_status='packaging_completed').count()
            orders_in_delivery = orders.filter(workflow_status='delivery_in_progress').count()
            orders_delivered = orders.filter(workflow_status='delivery_completed').count()
        except:
            # Fallback to status-based counting
            orders_ready_for_delivery = orders.filter(status='confirmed').count()
            orders_in_delivery = orders.filter(status='processing').count()
            orders_delivered = orders.filter(status='shipped').count()
        
        # Get delivery statistics from DeliveryRecord model
        delivery_stats = {
            'total_deliveries': DeliveryRecord.objects.count(),
            'completed_deliveries': DeliveryRecord.objects.filter(status='delivered').count(),
            'pending_deliveries': DeliveryRecord.objects.filter(status='assigned').count(),
            'failed_deliveries': DeliveryRecord.objects.filter(status='failed').count(),
            'orders_ready_for_delivery': orders_ready_for_delivery,
            'orders_in_delivery': orders_in_delivery,
            'orders_delivered': orders_delivered,
        }
        
        # Get additional data
        today = timezone.now().date()
        orders_today = orders.filter(date__date=today).count()
        orders_this_week = orders.filter(date__date__gte=today - timedelta(days=7)).count()
        orders_this_month = orders.filter(date__month=today.month, date__year=today.year).count()
        
        # Get top products from Order model
        top_products = list(orders.values('product__name_en').annotate(
            count=Count('id')
        ).order_by('-count')[:5])
        
        response_data = {
            'success': True,
            'data': {
                'orders': {
                    'total_orders': total_orders,
                    'pending_orders': pending_orders,
                    'processing_orders': processing_orders,
                    'shipped_orders': shipped_orders,
                },
                'delivery_stats': delivery_stats,
                'time_based': {
                    'orders_today': orders_today,
                    'orders_this_week': orders_this_week,
                    'orders_this_month': orders_this_month,
                },
                'top_products': top_products,
                'filters': {
                    'status': status_filter,
                    'search': search_query,
                    'date': date_filter,
                }
            }
        }
        
        return JsonResponse(response_data)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def delivery_performance_data(request):
    """API endpoint for delivery performance data"""
    try:
        today = timezone.now().date()
        start_date = request.GET.get('start_date', (today - timedelta(days=30)).isoformat())
        end_date = request.GET.get('end_date', today.isoformat())
        
        # Parse dates
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        except ValueError:
            start_date = today - timedelta(days=30)
            end_date = today
        
        # Get performance data from DeliveryPerformance model
        performance_data = DeliveryPerformance.objects.filter(
            date__range=[start_date, end_date]
        ).order_by('-date')
        
        # Calculate statistics
        total_deliveries = performance_data.aggregate(total=Sum('total_deliveries'))['total'] or 0
        total_distance = performance_data.aggregate(total=Sum('total_distance'))['total'] or 0
        avg_delivery_time = performance_data.aggregate(avg=Avg('average_delivery_time'))['avg'] or 0
        success_rate = performance_data.aggregate(rate=Avg('successful_deliveries'))['avg'] or 0
        
        # If no performance data exists, calculate from other sources
        if total_deliveries == 0 or total_distance == 0 or avg_delivery_time == 0:
            # Calculate from DeliveryRecord model
            try:
                completed_deliveries = DeliveryRecord.objects.filter(
                    status='delivered',
                    assigned_at__date__range=[start_date, end_date],
                    picked_up_at__isnull=False,
                    delivered_at__isnull=False
                )
                
                if completed_deliveries.exists():
                    # Calculate average delivery time
                    total_time_minutes = 0
                    total_calculated_distance = 0
                    
                    for delivery in completed_deliveries:
                        # Calculate delivery time
                        delivery_time = delivery.delivered_at - delivery.picked_up_at
                        total_time_minutes += delivery_time.total_seconds() / 60
                        
                        # Calculate delivery distance
                        delivery_distance = calculate_delivery_distance(delivery)
                        total_calculated_distance += delivery_distance
                    
                    avg_delivery_time = total_time_minutes / completed_deliveries.count()
                    
                    # Use calculated distance if available, otherwise fallback to route data
                    if total_calculated_distance > 0:
                        total_distance = total_calculated_distance
                    else:
                        # Calculate total distance from DeliveryRoute
                        try:
                            route_distance = DeliveryRoute.objects.filter(
                                route_date__range=[start_date, end_date]
                            ).aggregate(total=Sum('total_distance'))['total'] or 0
                            total_distance = route_distance
                        except:
                            # Estimate distance based on delivery count
                            total_distance = completed_deliveries.count() * 10.0  # 10km per delivery
                        
                else:
                    avg_delivery_time = 0
                    total_distance = 0
                    
            except:
                avg_delivery_time = 0
                total_distance = 0
        
        # Get recent performance records
        recent_performance = list(performance_data[:7].values(
            'date', 'total_deliveries', 'successful_deliveries', 'total_distance', 'average_delivery_time'
        ))
        
        # Get delivery statistics from DeliveryRecord model
        delivery_stats = {
            'total_deliveries': DeliveryRecord.objects.count(),
            'completed_deliveries': DeliveryRecord.objects.filter(status='delivered').count(),
            'pending_deliveries': DeliveryRecord.objects.filter(status='assigned').count(),
            'failed_deliveries': DeliveryRecord.objects.filter(status='failed').count(),
        }
        
        # Get courier statistics from Courier model
        courier_stats = {
            'total_couriers': Courier.objects.count(),
            'active_couriers': Courier.objects.filter(status='active').count(),
            'avg_courier_rating': Courier.objects.aggregate(avg=Avg('rating'))['avg'] or 0,
        }
        
        # If no real data exists, try to get data from other sources
        if total_deliveries == 0:
            # Try to get data from Order model for delivery-related orders
            delivery_orders = Order.objects.filter(
                status__in=['processing', 'shipped', 'delivered']
            )
            if delivery_orders.exists():
                total_deliveries = delivery_orders.count()
                successful_deliveries = delivery_orders.filter(status='delivered').count()
                success_rate = (successful_deliveries / total_deliveries * 100) if total_deliveries > 0 else 0
                
                # Generate sample performance data based on real orders
                recent_performance = []
                for i in range(7):
                    sample_date = today - timedelta(days=i)
                    daily_orders = delivery_orders.filter(date__date=sample_date)
                    daily_total = daily_orders.count()
                    daily_successful = daily_orders.filter(status='delivered').count()
                    
                    recent_performance.append({
                        'date': sample_date.isoformat(),
                        'total_deliveries': daily_total,
                        'successful_deliveries': daily_successful,
                        'total_distance': daily_total * 10.0,  # Estimate distance
                        'average_delivery_time': 2.5  # Estimate time
                    })
                
                # Update total statistics
                total_deliveries = delivery_orders.count()
                total_distance = total_deliveries * 10.0  # Estimate total distance
                avg_delivery_time = 2.5  # Estimate average time
                success_rate = (successful_deliveries / total_deliveries * 100) if total_deliveries > 0 else 0
        
        response_data = {
            'success': True,
            'data': {
                'performance': {
                    'total_deliveries': total_deliveries,
                    'total_distance': total_distance,
                    'avg_delivery_time': avg_delivery_time,
                    'success_rate': success_rate,
                    'recent_performance': recent_performance,
                },
                'delivery_stats': delivery_stats,
                'courier_stats': courier_stats,
                'date_range': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat(),
                }
            }
        }
        
        return JsonResponse(response_data)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def delivery_integrated_stats(request):
    """API endpoint for integrated delivery statistics from multiple sources"""
    try:
        today = timezone.now().date()
        start_date = request.GET.get('start_date', today)
        end_date = request.GET.get('end_date', today)
        
        # Parse dates
        try:
            if isinstance(start_date, str):
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            if isinstance(end_date, str):
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        except ValueError:
            start_date = today
            end_date = today
        
        # Get data from Order model (orders app)
        orders = Order.objects.all()
        date_range_orders = orders.filter(date__date__range=[start_date, end_date])
        
        # Get data from Product model (sellers app)
        products = Product.objects.all()
        
        # Get data from DeliveryRecord model (delivery app)
        deliveries = DeliveryRecord.objects.all()
        date_range_deliveries = deliveries.filter(assigned_at__date__range=[start_date, end_date])
        
        # Get data from DeliveryPerformance model for performance metrics
        try:
            performance_data = DeliveryPerformance.objects.filter(
                date__range=[start_date, end_date]
            ).aggregate(
                total_distance=Sum('total_distance'),
                avg_delivery_time=Avg('average_delivery_time')
            )
            
            total_distance = performance_data['total_distance'] or 0
            avg_delivery_time = performance_data['avg_delivery_time'] or 0
        except:
            # Fallback: calculate from DeliveryRecord model
            try:
                completed_deliveries = deliveries.filter(
                    status='delivered',
                    picked_up_at__isnull=False,
                    delivered_at__isnull=False
                )
                
                if completed_deliveries.exists():
                    # Calculate average delivery time
                    total_time_minutes = 0
                    total_calculated_distance = 0
                    
                    for delivery in completed_deliveries:
                        # Calculate delivery time
                        delivery_time = delivery.delivered_at - delivery.picked_up_at
                        total_time_minutes += delivery_time.total_seconds() / 60
                        
                        # Calculate delivery distance
                        delivery_distance = calculate_delivery_distance(delivery)
                        total_calculated_distance += delivery_distance
                    
                    avg_delivery_time = total_time_minutes / completed_deliveries.count()
                    
                    # Use calculated distance if available, otherwise fallback to route data
                    if total_calculated_distance > 0:
                        total_distance = total_calculated_distance
                    else:
                        # Calculate total distance from DeliveryRoute
                        try:
                            route_distance = DeliveryRoute.objects.filter(
                                route_date__range=[start_date, end_date]
                            ).aggregate(total=Sum('total_distance'))['total'] or 0
                            total_distance = route_distance
                        except:
                            # Estimate distance based on delivery count
                            total_distance = completed_deliveries.count() * 10.0  # 10km per delivery
                            
                else:
                    avg_delivery_time = 0
                    total_distance = 0
                    
            except:
                avg_delivery_time = 0
                total_distance = 0
        
        # Calculate integrated statistics
        total_orders = orders.count()
        total_products = products.count()
        total_deliveries = deliveries.count()
        
        # Order status breakdown
        order_statuses = {
            'pending': orders.filter(status='pending').count(),
            'confirmed': orders.filter(status='confirmed').count(),
            'processing': orders.filter(status='processing').count(),
            'shipped': orders.filter(status='shipped').count(),
            'delivered': orders.filter(status='delivered').count(),
            'cancelled': orders.filter(status='cancelled').count(),
        }
        
        # Workflow status breakdown
        workflow_statuses = {}
        try:
            workflow_statuses = {
                'seller_submitted': orders.filter(workflow_status='seller_submitted').count(),
                'callcenter_approved': orders.filter(workflow_status='callcenter_approved').count(),
                'stockkeeper_approved': orders.filter(workflow_status='stockkeeper_approved').count(),
                'packaging_in_progress': orders.filter(workflow_status='packaging_in_progress').count(),
                'packaging_completed': orders.filter(workflow_status='packaging_completed').count(),
                'delivery_in_progress': orders.filter(workflow_status='delivery_in_progress').count(),
                'delivery_completed': orders.filter(workflow_status='delivery_completed').count(),
            }
        except:
            pass
        
        # Delivery statistics
        delivery_statuses = {
            'assigned': deliveries.filter(status='assigned').count(),
            'accepted': deliveries.filter(status='accepted').count(),
            'picked_up': deliveries.filter(status='picked_up').count(),
            'in_transit': deliveries.filter(status='in_transit').count(),
            'out_for_delivery': deliveries.filter(status='out_for_delivery').count(),
            'delivered': deliveries.filter(status='delivered').count(),
            'failed': deliveries.filter(status='failed').count(),
        }
        
        # Product statistics
        product_stats = {
            'total_products': total_products,
            'approved_products': products.filter(is_approved=True).count(),
            'pending_products': products.filter(is_approved=False).count(),
            'products_with_orders': products.filter(orders__isnull=False).distinct().count(),
        }
        
        # Calculate success rates
        delivery_success_rate = (delivery_statuses['delivered'] / max(total_deliveries, 1)) * 100 if total_deliveries > 0 else 0
        order_completion_rate = (order_statuses['delivered'] / max(total_orders, 1)) * 100 if total_orders > 0 else 0
        
        # Get recent activity from multiple sources
        recent_orders = list(orders.select_related('product', 'seller').order_by('-date')[:5].values(
            'id', 'order_code', 'status', 'date', 'product__name_en', 'customer'
        ))
        
        recent_deliveries = list(deliveries.select_related('order', 'courier').order_by('-assigned_at')[:5].values(
            'id', 'status', 'assigned_at', 'order__order_code', 'courier__user__full_name'
        ))
        
        recent_products = list(products.select_related('seller').order_by('-created_at')[:5].values(
            'id', 'name_en', 'code', 'selling_price', 'stock_quantity', 'is_approved'
        ))
        
        # Get top performing products
        top_products = list(orders.values('product__name_en').annotate(
            order_count=Count('id'),
            total_revenue=Sum(F('quantity') * F('price_per_unit'))
        ).order_by('-order_count')[:5])
        
        # Get delivery performance metrics
        delivery_performance = {
            'orders_ready': workflow_statuses.get('packaging_completed', 0),
            'orders_in_progress': workflow_statuses.get('delivery_in_progress', 0),
            'orders_completed': workflow_statuses.get('delivery_completed', 0),
            'efficiency_rate': delivery_success_rate,
        }
        
        # Calculate revenue statistics
        revenue_stats = {
            'total_revenue': orders.aggregate(total=Sum(F('quantity') * F('price_per_unit')))['total'] or 0,
            'monthly_revenue': date_range_orders.aggregate(total=Sum(F('quantity') * F('price_per_unit')))['total'] or 0,
            'delivered_revenue': orders.filter(status='delivered').aggregate(total=Sum(F('quantity') * F('price_per_unit')))['total'] or 0,
        }
        
        response_data = {
            'success': True,
            'data': {
                'overview': {
                    'total_orders': total_orders,
                    'total_products': total_products,
                    'total_deliveries': total_deliveries,
                    'delivery_success_rate': round(delivery_success_rate, 1),
                    'order_completion_rate': round(order_completion_rate, 1),
                },
                'order_statuses': order_statuses,
                'workflow_statuses': workflow_statuses,
                'delivery_statuses': delivery_statuses,
                'product_stats': product_stats,
                'delivery_performance': delivery_performance,
                'revenue_stats': revenue_stats,
                'recent_orders': recent_orders,
                'recent_deliveries': recent_deliveries,
                'recent_products': recent_products,
                'top_products': top_products,
                'date_range': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat(),
                }
            }
        }
        
        return JsonResponse(response_data)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
