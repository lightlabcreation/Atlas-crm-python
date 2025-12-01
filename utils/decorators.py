from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.urls import reverse
from .views import permission_denied_authenticated


def permission_required(permission_codename, module=None, redirect_to_permission_denied=True):
    """
    Decorator to check if user has a specific permission.
    If permission is denied and redirect_to_permission_denied is True,
    redirects to permission denied page instead of dashboard.
    
    Args:
        permission_codename: The permission codename to check
        module: The module to check permission in (optional)
        redirect_to_permission_denied: Whether to redirect to permission denied page
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if request.user.is_authenticated:
                if request.user.has_permission(permission_codename, module):
                    return view_func(request, *args, **kwargs)
                else:
                    if redirect_to_permission_denied:
                        # Redirect to permission denied page
                        return permission_denied_authenticated(
                            request, 
                            message=f"You don't have permission to access this page. Required permission: {permission_codename}"
                        )
                    else:
                        # Fallback to dashboard with error message
                        messages.error(
                            request, 
                            f"You don't have permission to access this page. Required permission: {permission_codename}"
                        )
                        return redirect('dashboard:index')
            else:
                # Redirect to login if not authenticated
                return redirect('users:login')
        return wrapper
    return decorator


def role_required(role_name, redirect_to_permission_denied=True):
    """
    Decorator to check if user has a specific role.
    If role is denied and redirect_to_permission_denied is True,
    redirects to permission denied page instead of dashboard.
    
    Args:
        role_name: The role name to check
        redirect_to_permission_denied: Whether to redirect to permission denied page
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if request.user.is_authenticated:
                if (request.user.is_superuser or 
                    request.user.has_role('Admin') or 
                    request.user.has_role(role_name)):
                    return view_func(request, *args, **kwargs)
                else:
                    if redirect_to_permission_denied:
                        # Redirect to permission denied page
                        return permission_denied_authenticated(
                            request, 
                            message=f"You don't have permission to access this page. Required role: {role_name}"
                        )
                    else:
                        # Fallback to dashboard with error message
                        messages.error(
                            request, 
                            f"You don't have permission to access this page. Required role: {role_name}"
                        )
                        return redirect('dashboard:index')
            else:
                # Redirect to login if not authenticated
                return redirect('users:login')
        return wrapper
    return decorator


def any_role_required(role_names, redirect_to_permission_denied=True):
    """
    Decorator to check if user has any of the specified roles.
    If no role is found and redirect_to_permission_denied is True,
    redirects to permission denied page instead of dashboard.
    
    Args:
        role_names: List of role names to check
        redirect_to_permission_denied: Whether to redirect to permission denied page
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if request.user.is_authenticated:
                has_role = (request.user.is_superuser or 
                           request.user.has_role('Admin') or
                           any(request.user.has_role(role) for role in role_names))
                
                if has_role:
                    return view_func(request, *args, **kwargs)
                else:
                    if redirect_to_permission_denied:
                        # Redirect to permission denied page
                        return permission_denied_authenticated(
                            request, 
                            message=f"You don't have permission to access this page. Required roles: {', '.join(role_names)}"
                        )
                    else:
                        # Fallback to dashboard with error message
                        messages.error(
                            request, 
                            f"You don't have permission to access this page. Required roles: {', '.join(role_names)}"
                        )
                        return redirect('dashboard:index')
            else:
                # Redirect to login if not authenticated
                return redirect('users:login')
        return wrapper
    return decorator


def module_access_required(module_name, redirect_to_permission_denied=True):
    """
    Decorator to check if user has access to a specific module.
    If access is denied and redirect_to_permission_denied is True,
    redirects to permission denied page instead of dashboard.
    
    Args:
        module_name: The module name to check access for
        redirect_to_permission_denied: Whether to redirect to permission denied page
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if request.user.is_authenticated:
                # Check if user has any permission in the module
                has_access = (request.user.is_superuser or 
                             request.user.has_role('Admin') or
                             request.user.user_roles.filter(
                                 role__role_permissions__permission__module=module_name,
                                 role__role_permissions__granted=True,
                                 is_active=True
                             ).exists())
                
                if has_access:
                    return view_func(request, *args, **kwargs)
                else:
                    if redirect_to_permission_denied:
                        # Redirect to permission denied page
                        return permission_denied_authenticated(
                            request, 
                            message=f"You don't have access to the {module_name} module."
                        )
                    else:
                        # Fallback to dashboard with error message
                        messages.error(
                            request, 
                            f"You don't have access to the {module_name} module."
                        )
                        return redirect('dashboard:index')
            else:
                # Redirect to login if not authenticated
                return redirect('users:login')
        return wrapper
    return decorator


def admin_only(redirect_to_permission_denied=True):
    """
    Decorator to restrict access to Admin and Super Admin only.
    Packaging Agent and other roles will be denied access.
    
    Args:
        redirect_to_permission_denied: Whether to redirect to permission denied page
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if request.user.is_authenticated:
                # Only allow Admin, Super Admin, and superuser
                # Explicitly deny Packaging Agent and other non-admin roles
                if (request.user.is_superuser or 
                    request.user.has_role('Super Admin') or 
                    request.user.has_role('Admin')):
                    return view_func(request, *args, **kwargs)
                else:
                    # If user is Packaging Agent, redirect to their dashboard
                    if request.user.has_role('Packaging Agent'):
                        if redirect_to_permission_denied:
                            return permission_denied_authenticated(
                                request, 
                                message="You don't have permission to access this page. This page is restricted to Admin and Super Admin only."
                            )
                        else:
                            messages.error(
                                request, 
                                "You don't have permission to access this page. This page is restricted to Admin and Super Admin only."
                            )
                            return redirect('packaging:dashboard')
                    else:
                        # For other roles, use standard permission denied
                        if redirect_to_permission_denied:
                            return permission_denied_authenticated(
                                request, 
                                message="You don't have permission to access this page. This page is restricted to Admin and Super Admin only."
                            )
                        else:
                            messages.error(
                                request, 
                                "You don't have permission to access this page. This page is restricted to Admin and Super Admin only."
                            )
                            return redirect('dashboard:index')
            else:
                # Redirect to login if not authenticated
                return redirect('users:login')
        return wrapper
    return decorator 