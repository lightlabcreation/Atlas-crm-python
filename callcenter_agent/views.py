from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Q, Count, Sum
from django.utils import timezone
from datetime import timedelta
from orders.models import Order
from products.models import Product

def has_agent_role(user):
    """Check if user has call center agent role."""
    return user.has_role('Call Center Agent') or user.is_superuser

@login_required
def dashboard(request):
    """Call Center Agent Dashboard."""
    if not has_agent_role(request.user):
        messages.error(request, "ليس لديك صلاحية للدخول لهذه الصفحة.")
        return redirect('dashboard:index')
    
    agent_orders = Order.objects.filter(agent=request.user).exclude(
        status__in=['confirmed', 'packaged', 'shipped', 'delivered']
    ).exclude(
        escalated_to_manager=True
    )
    
    # Get statistics
    total_orders = agent_orders.count()
    pending_orders = agent_orders.filter(status='pending').count()
    confirmed_orders = agent_orders.filter(status='confirmed').count()
    cancelled_orders = agent_orders.filter(status='cancelled').count()
    postponed_orders = agent_orders.filter(status='processing').count()  # Using processing as postponed
    
    # Get recent orders
    recent_orders = agent_orders.order_by('-date')[:10]
    
    # Get today's orders
    today = timezone.now().date()
    today_orders = agent_orders.filter(date__date=today)
    
    # Debug: Print orders info
    print(f"DEBUG DASHBOARD: Agent orders count: {agent_orders.count()}")
    print(f"DEBUG DASHBOARD: User: {request.user}")
    print(f"DEBUG DASHBOARD: User roles: {[ur.role.name for ur in request.user.user_roles.filter(is_active=True)]}")
    
    context = {
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'confirmed_orders': confirmed_orders,
        'cancelled_orders': cancelled_orders,
        'postponed_orders': postponed_orders,
        'today_orders': today_orders.count(),
        'recent_orders': recent_orders,
    }
    
    return render(request, 'callcenter_agent/dashboard.html', context)

@login_required
def order_list(request):
    """List agent's orders."""
    if not has_agent_role(request.user):
        messages.error(request, "ليس لديك صلاحية للدخول لهذه الصفحة.")
        return redirect('dashboard:index')
    
    # Get search and filter parameters
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    
    orders = Order.objects.filter(agent=request.user).exclude(
        status__in=['confirmed', 'packaged', 'shipped', 'delivered']
    ).exclude(
        escalated_to_manager=True
    ).order_by('-date')
    
    # Apply search filter
    if search_query:
        orders = orders.filter(
            Q(order_code__icontains=search_query) |
            Q(customer__icontains=search_query) |
            Q(customer_phone__icontains=search_query)
        )
    
    # Apply status filter
    if status_filter:
        orders = orders.filter(status=status_filter)
    
    # Debug: Print orders count
    print(f"DEBUG: Orders count: {orders.count()}")
    print(f"DEBUG: User: {request.user}")
    print(f"DEBUG: User roles: {[ur.role.name for ur in request.user.user_roles.filter(is_active=True)]}")
    print(f"DEBUG: Search query: '{search_query}'")
    print(f"DEBUG: Status filter: '{status_filter}'")
    
    context = {
        'orders': orders,
        'search_query': search_query,
        'status_filter': status_filter,
    }
    
    return render(request, 'callcenter_agent/orders.html', context)



