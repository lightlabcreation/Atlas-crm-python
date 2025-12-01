from django.urls import path
from . import views

app_name = 'callcenter_agent'

urlpatterns = [
    # Call Center Agent Dashboard
    path('', views.dashboard, name='dashboard'),
    
    # Orders Management
    path('orders/', views.order_list, name='orders'),
]


