from django.urls import path
from . import views
from . import admin_views

app_name = 'sellers'

urlpatterns = [
    # Admin Management
    path('', views.seller_list, name='seller_list'),
    # Seller Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),
    path('orders/', views.order_list, name='orders'),
    path('inventory/', views.inventory, name='inventory'),
    path('products/', views.product_list, name='products'),
    path('finance/', views.finance, name='finance'),
    
    # Product Management
    path('products/create/', views.product_create, name='product_create'),
    path('products/<int:product_id>/', views.product_detail, name='product_detail'),
    path('products/<int:product_id>/edit/', views.product_edit, name='product_edit'),
    path('products/<int:product_id>/delete/', views.product_delete, name='product_delete'),
    path('products/<int:product_id>/delete-request/', views.product_delete_request, name='product_delete_request'),
    
    # Order Management
    path('orders/<int:order_id>/', views.order_detail, name='order_detail'),
    path('orders/<int:order_id>/edit/', views.order_update, name='order_update'),
    path('orders/import/', views.import_orders, name='import_orders'),
    
    # Sourcing Requests
    path('sourcing-requests/', views.sourcing_request_list, name='sourcing_requests'),
    path('sourcing-requests/create/', views.sourcing_request_create, name='sourcing_request_create'),
    path('sourcing-requests/<int:request_id>/', views.sourcing_request_detail, name='sourcing_request_detail'),
    
    # Warehouses
    path('warehouses/', views.warehouses, name='warehouses'),
    
    
    # API endpoints
    path('products/<int:seller_id>/', views.get_seller_products, name='get_seller_products'),
    
    # Admin Deletion Requests
    path('admin/deletion-requests/', admin_views.deletion_requests_list, name='deletion_requests_list'),
    path('admin/deletion-requests/<int:request_id>/', admin_views.deletion_request_detail, name='deletion_request_detail'),
    path('admin/deletion-requests/<int:request_id>/approve/', admin_views.approve_deletion_request, name='approve_deletion_request'),
    path('admin/deletion-requests/<int:request_id>/reject/', admin_views.reject_deletion_request, name='reject_deletion_request'),
    
]