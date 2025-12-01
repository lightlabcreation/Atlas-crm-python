from django.urls import path
from . import views

app_name = 'products'

urlpatterns = [
    # Products
    path('', views.product_list, name='list'),
    path('create/', views.product_create, name='create'),
    path('<int:product_id>/', views.product_detail, name='detail'),
    path('<int:product_id>/api/', views.product_detail_api, name='detail_api'),
    path('<int:product_id>/edit/', views.product_edit, name='edit'),
    path('<int:product_id>/delete/', views.product_delete, name='delete'),
]


