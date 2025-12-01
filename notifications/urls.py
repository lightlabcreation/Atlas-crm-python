from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    # Main notifications page
    path('', views.notifications_list, name='index'),
    
    # AJAX endpoints for navbar
    path('get/', views.get_notifications_ajax, name='get_notifications'),
    path('mark-read/<int:notification_id>/', views.mark_notification_read, name='mark_read'),
    path('mark-all-read/', views.mark_all_notifications_read, name='mark_all_read'),
    
    # Detailed views
    path('detail/<int:notification_id>/', views.notification_detail, name='detail'),
    path('archived/', views.archived_notifications, name='archived'),
    path('settings/', views.notification_settings, name='settings'),
]
