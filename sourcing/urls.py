from django.urls import path
from . import views

app_name = 'sourcing'

urlpatterns = [
    # Sourcing Dashboard
    path('', views.sourcing_dashboard, name='dashboard'),
    
    # Requests
    path('requests/', views.sourcing_request_list, name='requests'),
    path('requests/create/', views.comprehensive_sourcing_create, name='comprehensive_create'),
    path('requests/create/', views.sourcing_request_create, name='create_request'),
    path('requests/<int:request_id>/', views.sourcing_request_detail, name='request_detail'),
    path('requests/<int:request_id>/edit/', views.sourcing_request_create, name='request_edit'),
    path('requests/<int:request_id>/approve/', views.approve_sourcing_request, name='approve_request'),
    path('requests/<int:request_id>/reject/', views.reject_sourcing_request, name='reject_request'),
    
    # Reports
    path('reports/', views.suppliers_list, name='reports'),
    
    # Suppliers
    path('suppliers/', views.suppliers_list, name='suppliers'),
]