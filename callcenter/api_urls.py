# callcenter/api_urls.py
from django.urls import path
from . import api_views

app_name = 'callcenter_api'

urlpatterns = [
    # Dashboard APIs
    path('dashboard/stats/', api_views.dashboard_stats, name='dashboard_stats'),
    path('agent/dashboard/stats/', api_views.agent_dashboard_stats, name='agent_dashboard_stats'),
    path('manager/dashboard/stats/', api_views.manager_dashboard_stats, name='manager_dashboard_stats'),
    
    # Order Management APIs
    path('orders/', api_views.order_list, name='order_list'),
    path('orders/<int:order_id>/', api_views.order_detail, name='order_detail'),
    path('orders/<int:order_id>/update-status/', api_views.update_order_status, name='update_order_status'),
    path('orders/<int:order_id>/log-call/', api_views.log_call, name='log_call'),
    path('orders/<int:order_id>/assign/', api_views.assign_order, name='assign_order'),
    path('orders/distribute/', api_views.distribute_orders, name='distribute_orders'),
    
    # Agent Session Management
    path('agent/status/', api_views.update_agent_status, name='update_agent_status'),
    
    # Reports APIs
    path('reports/agent-performance/', api_views.agent_performance_report, name='agent_performance_report'),
]


