from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Main Dashboard
    path('', include('dashboard.urls')),
    
    # Role-based URLs
    path('seller/', include('sellers.urls')),
    path('admin/', include('admin.urls')),
    path('callcenter/manager/', include('callcenter_manager.urls')),
    path('callcenter/agent/', include('callcenter_agent.urls')),
    path('finance/', include('finance.urls')),
    path('stock-keeper/', include('stock_keeper.urls')),
    path('packaging/', include('packaging.urls')),
    path('delivery/', include('delivery.urls')),
    path('inventory/', include('inventory.urls')),
    path('sourcing/', include('sourcing.urls')),
    
    # Shared URLs
    path('users/', include('users.urls')),
    path('orders/', include('orders.urls')),
    path('products/', include('products.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
