from django.urls import path
from . import views

app_name = 'stock_keeper'

urlpatterns = [
    # Stock Keeper Dashboard
    path('', views.dashboard, name='dashboard'),
    
    # Task Management
    path('tasks/', views.task_management, name='task_management'),
    path('tasks/<int:task_id>/start/', views.start_task, name='start_task'),
    path('tasks/<int:task_id>/complete/', views.complete_task, name='complete_task'),
    path('tasks/<int:task_id>/edit/', views.edit_task, name='edit_task'),
    path('tasks/<int:task_id>/', views.task_info, name='task_info'),
    path('tasks/<int:task_id>/delete/', views.delete_task, name='delete_task'),
    
    # Cycle Count
    path('cycle-count/', views.cycle_count, name='cycle_count'),
    path('cycle-count/start/', views.start_count_session, name='start_count_session'),
    path('cycle-count/sessions/', views.cycle_count_sessions, name='cycle_count_sessions'),
    path('cycle-count/session/<str:session_id>/', views.cycle_count_session, name='cycle_count_session'),
    path('cycle-count/session/<str:session_id>/details/', views.cycle_count_details, name='cycle_count_details'),
    path('cycle-count/record/', views.record_count, name='record_count'),
    path('cycle-count/submit/', views.submit_count, name='submit_count'),
    path('cycle-count/variance/', views.submit_count_variance, name='submit_count_variance'),
    path('cycle-count/complete/', views.complete_session, name='complete_session'),
    
    # Receive Stock
    path('receive/', views.receive_stock, name='receive_stock'),
    
    # Ship Orders
    path('ship/', views.ship_orders, name='ship_orders'),
    
    # Transfer Stock
    path('transfer/', views.transfer_stock, name='transfer_stock'),

    # Inventory Log
    path('log/', views.inventory_log, name='inventory_log'),
    path('movement-history/', views.movement_history, name='movement_history'),

    # Return Orders
    path('returns/', views.return_orders, name='return_orders'),
    
    # Warehouses
    path('warehouses/', views.warehouse_list, name='warehouses'),
    path('warehouses/<int:warehouse_id>/', views.warehouse_detail, name='warehouse_detail'),
    path('warehouses/<int:warehouse_id>/report/', views.warehouse_report, name='warehouse_report'),
    
    # Alerts
    path('alerts/', views.alerts, name='alerts'),
    path('alerts/<int:alert_id>/resolve/', views.resolve_alert, name='resolve_alert'),
    
    # Product Acceptance / Inventory Management
    path('acceptance/', views.product_acceptance, name='product_acceptance'),
    path('accept-product/<int:product_id>/', views.accept_product, name='accept_product'),
    path('inventory/<int:record_id>/view/', views.view_inventory_record, name='view_inventory_record'),
    path('inventory/<int:record_id>/edit/', views.edit_inventory_record, name='edit_inventory_record'),
    path('inventory/<int:record_id>/delete/', views.delete_inventory_record, name='delete_inventory_record'),
    path('inventory/add/', views.add_inventory_record, name='add_inventory_record'),
    
    
    # API Endpoints
    path('api/search-product/', views.api_search_product, name='api_search_product'),
    path('api/inventory/<int:product_id>/', views.api_get_inventory, name='api_get_inventory'),
    path('api/movement/<int:movement_id>/', views.api_get_movement, name='api_get_movement'),
    path('api/order/<int:order_id>/', views.api_get_order, name='api_get_order'),
    path('api/transfer/<int:transfer_id>/', views.api_get_transfer, name='api_get_transfer'),
    path('api/receive/', views.api_receive_stock, name='api_receive_stock'),
    path('api/pick-order/', views.api_pick_order, name='api_pick_order'),
    path('api/complete-transfer/', views.api_complete_transfer, name='api_complete_transfer'),
    path('api/warehouse/<int:warehouse_id>/products/', views.api_warehouse_products, name='api_warehouse_products'),
    path('api/product/<int:product_id>/warehouse/<int:warehouse_id>/', views.api_product_warehouse_details, name='api_product_warehouse_details'),
]