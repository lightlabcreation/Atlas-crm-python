from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    # Main Dashboard
    path('', views.index, name='index'),
    
    
    # Audit Log
    path('audit-log/', views.audit_log, name='audit_log'),
    path('audit-log/export/', views.export_audit_log, name='export_audit_log'),
    
    # Help Center
    path('help/', views.help, name='help'),
    
    # System Status
    path('system-status/', views.system_status, name='system_status'),
    
    # Alerts
    path('alerts/', views.alerts, name='alerts'),
    
]