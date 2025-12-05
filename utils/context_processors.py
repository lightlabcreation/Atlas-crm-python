"""
Context processors for adding global template variables.
"""
from django.urls import resolve, Resolver404
from django.utils.translation import gettext as _


def breadcrumbs(request):
    """
    Automatically generate breadcrumbs based on current URL path.

    Returns breadcrumb_items list that can be used in templates.

    Usage in view:
        context['breadcrumb_items'] = [
            {'label': 'Orders', 'url': '/orders/', 'icon': 'fas fa-shopping-cart'},
            {'label': 'Order Details', 'url': None, 'icon': 'fas fa-file-alt'},  # Current page (no URL)
        ]

    Or let it auto-generate from URL:
        /orders/123/edit/ becomes:
        Home > Orders > Order #123 > Edit
    """
    breadcrumb_items = []

    # Skip breadcrumbs for certain paths
    skip_paths = [
        '/admin/',
        '/static/',
        '/media/',
        '/api/',
        '/accounts/login/',
        '/accounts/logout/',
    ]

    if any(request.path.startswith(path) for path in skip_paths):
        return {'breadcrumb_items': []}

    # Try to resolve URL name for smarter breadcrumb generation
    try:
        resolved = resolve(request.path)
        url_name = resolved.url_name
        app_name = resolved.app_name

        # Module-specific breadcrumbs
        if app_name:
            module_config = {
                'orders': {'label': _('Orders'), 'icon': 'fas fa-shopping-cart'},
                'delivery': {'label': _('Delivery'), 'icon': 'fas fa-truck'},
                'finance': {'label': _('Finance'), 'icon': 'fas fa-dollar-sign'},
                'inventory': {'label': _('Inventory'), 'icon': 'fas fa-boxes'},
                'sellers': {'label': _('Sellers'), 'icon': 'fas fa-store'},
                'callcenter': {'label': _('Call Center'), 'icon': 'fas fa-phone'},
                'users': {'label': _('Users'), 'icon': 'fas fa-users'},
                'dashboard': {'label': _('Dashboard'), 'icon': 'fas fa-tachometer-alt'},
                'stock_keeper': {'label': _('Stock'), 'icon': 'fas fa-warehouse'},
                'order_packaging': {'label': _('Packaging'), 'icon': 'fas fa-box'},
                'analytics': {'label': _('Analytics'), 'icon': 'fas fa-chart-line'},
                'notifications': {'label': _('Notifications'), 'icon': 'fas fa-bell'},
            }

            if app_name in module_config:
                config = module_config[app_name]
                module_url = f'/{app_name}/'
                breadcrumb_items.append({
                    'label': config['label'],
                    'url': module_url,
                    'icon': config['icon']
                })

                # Add specific page breadcrumb if not just the module index
                if url_name and url_name != 'index':
                    # Format URL name into readable label
                    page_label = url_name.replace('_', ' ').replace('-', ' ').title()
                    breadcrumb_items.append({
                        'label': page_label,
                        'url': None,  # Current page
                        'icon': None
                    })

    except Resolver404:
        pass
    except Exception:
        pass

    return {'breadcrumb_items': breadcrumb_items}


def user_permissions(request):
    """
    Add user permissions to context for easy template access.
    """
    if request.user.is_authenticated:
        return {
            'is_superuser': request.user.is_superuser,
            'user_role': request.user.get_primary_role() if hasattr(request.user, 'get_primary_role') else None,
            'user_permissions': list(request.user.get_all_permissions()) if hasattr(request.user, 'get_all_permissions') else [],
        }
    return {
        'is_superuser': False,
        'user_role': None,
        'user_permissions': [],
    }
