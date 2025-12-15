from django.shortcuts import render
from django.http import Http404
from django.contrib.auth.decorators import login_required
from django.db import models


def custom_404(request, exception):
    """Custom 404 page handler."""
    return render(request, '404.html', status=404)

def custom_500(request):
    """Custom 500 page handler."""
    return render(request, '500.html', status=500)


def test_simple_permission_denied(request):
    """
    Simple test view to verify the permission denied system is working.
    """
    context = {
        'custom_message': 'This is a test message from the simple permission denied view.',
        'error_type': 'permission_denied',
        'page_title': 'Test Permission Denied'
    }
    
    return render(request, 'simple_permission_denied.html', context, status=403)


@login_required
def reports_dashboard(request):
    """Reports dashboard with export options."""
    from django.utils import timezone
    from orders.models import Order
    from finance.models import Payment

    # Get date range filters
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')

    # Calculate stats
    total_orders = Order.objects.count()
    total_revenue = Payment.objects.filter(payment_status='completed').aggregate(
        total=models.Sum('amount')
    )['total'] or 0

    context = {
        'total_orders': total_orders,
        'total_revenue': total_revenue,
        'date_from': date_from,
        'date_to': date_to,
        'report_types': [
            {'name': 'Sales Report', 'description': 'Comprehensive sales data by date range'},
            {'name': 'Order Report', 'description': 'Detailed order information and status'},
            {'name': 'Inventory Report', 'description': 'Stock levels and movement analysis'},
            {'name': 'Finance Report', 'description': 'Payment and revenue breakdown'},
            {'name': 'Delivery Report', 'description': 'Delivery performance metrics'},
            {'name': 'User Activity Report', 'description': 'User actions and audit logs'},
        ]
    }

    return render(request, 'reports/dashboard.html', context) 