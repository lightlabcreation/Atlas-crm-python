from django.urls import path
from . import api_views

app_name = 'users_api'

urlpatterns = [
    path('login/', api_views.api_login, name='api_login'),
    path('logout/', api_views.api_logout, name='api_logout'),
    path('profile/', api_views.api_profile, name='api_profile'),
]
