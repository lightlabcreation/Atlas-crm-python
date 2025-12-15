from django.urls import path
from . import views

app_name = 'settings'

urlpatterns = [
    path('', views.settings_dashboard, name='dashboard'),
    path('countries/', views.countries_management, name='countries'),
    path('delivery-companies/', views.delivery_companies_management, name='delivery_companies'),
    path('fees/', views.fees_management, name='fees'),
    path('fee-management/', views.fees_management, name='fee_management'),
    path('delete-account/', views.delete_own_account, name='delete_account'),
    path('audit-logs/', views.audit_logs, name='audit_logs'),
] 