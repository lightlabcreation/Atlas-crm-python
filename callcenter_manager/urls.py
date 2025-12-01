from django.urls import path
from . import views

app_name = 'callcenter_manager'

urlpatterns = [
    # Call Center Manager Dashboard
    path('', views.dashboard, name='dashboard'),
    
    # Orders Management
    path('orders-management/', views.orders_management, name='orders_management'),
    path('orders/<int:order_id>/', views.order_detail, name='order_detail'),
    path('orders/<int:order_id>/edit/', views.order_edit, name='order_edit'),
    path('orders/<int:order_id>/add-note/', views.add_note, name='add_note'),
    
    # Agents Management
    path('agents/', views.agent_list, name='agents'),
    path('agents/<int:agent_id>/', views.agent_detail, name='agent_detail'),
    path('agents/<int:agent_id>/edit/', views.agent_edit, name='agent_edit'),
    
    path('reports/agent-performance/', views.agent_performance, name='agent_performance'),
    path('reports/order-statistics/', views.order_statistics, name='order_statistics'),
    
    # Settings
    path('settings/', views.settings, name='settings'),
]


