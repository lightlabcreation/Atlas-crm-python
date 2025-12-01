"""
Examples of how to use the new permission denied system.

This file contains examples and demonstrations of the various ways
to implement permission checking and show the permission denied page.
"""

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .views import permission_denied_authenticated, access_denied
from .decorators import permission_required, role_required, any_role_required, module_access_required


# Example 1: Manual permission checking with custom message
@login_required
def manual_permission_check_example(request):
    """Example of manually checking permissions and showing custom message."""
    if not request.user.has_permission('view_financial_reports', 'finance'):
        return permission_denied_authenticated(
            request,
            message="You need 'view_financial_reports' permission in the finance module to access this page."
        )
    
    # User has permission, continue with view logic
    return render(request, 'finance/reports.html', {'reports': []})


# Example 2: Using the permission_required decorator
@login_required
@permission_required('create_orders', 'orders')
def create_order_example(request):
    """Example using the permission_required decorator."""
    # This view will automatically redirect to permission denied page
    # if user doesn't have 'create_orders' permission in 'orders' module
    return render(request, 'orders/create.html', {})


# Example 3: Using the role_required decorator
@login_required
@role_required('Admin')
def admin_only_example(request):
    """Example using the role_required decorator."""
    # This view will automatically redirect to permission denied page
    # if user doesn't have Admin role
    return render(request, 'admin/dashboard.html', {})


# Example 4: Using the any_role_required decorator
@login_required
@any_role_required(['Manager', 'Supervisor', 'Team Lead'])
def management_example(request):
    """Example using the any_role_required decorator."""
    # This view will automatically redirect to permission denied page
    # if user doesn't have any of the specified roles
    return render(request, 'management/dashboard.html', {})


# Example 5: Using the module_access_required decorator
@login_required
@module_access_required('inventory')
def inventory_access_example(request):
    """Example using the module_access_required decorator."""
    # This view will automatically redirect to permission denied page
    # if user doesn't have access to the inventory module
    return render(request, 'inventory/dashboard.html', {})


# Example 6: Different types of access restrictions
@login_required
def different_access_types_example(request):
    """Example showing different types of access restrictions."""
    
    # Check if user is trying to access a specific resource
    resource_id = request.GET.get('resource_id')
    
    if resource_id:
        # Check if user owns this resource
        if not request.user.owns_resource(resource_id):
            return access_denied(
                request,
                message="You don't have access to this specific resource."
            )
    
    # Check if user has module access
    if not request.user.has_module_access('advanced_features'):
        return permission_denied_authenticated(
            request,
            message="You need access to the advanced features module to use this functionality."
        )
    
    return render(request, 'advanced/features.html', {})


# Example 7: Conditional permission checking
@login_required
def conditional_permission_example(request):
    """Example of conditional permission checking."""
    
    # Check user's role for different permission levels
    if request.user.has_role('Super Admin'):
        # Super admins can see everything
        return render(request, 'admin/super_dashboard.html', {})
    
    elif request.user.has_role('Admin'):
        # Regular admins can see most things
        if request.user.has_permission('view_sensitive_data'):
            return render(request, 'admin/dashboard.html', {})
        else:
            return permission_denied_authenticated(
                request,
                message="You need 'view_sensitive_data' permission to access this dashboard."
            )
    
    else:
        # Regular users need specific permissions
        return permission_denied_authenticated(
            request,
            message="This dashboard is only available to administrators."
        )


# Example 8: API-style permission checking
@login_required
def api_permission_example(request):
    """Example of API-style permission checking."""
    
    # Check multiple permissions
    required_permissions = ['read_data', 'export_data']
    missing_permissions = []
    
    for permission in required_permissions:
        if not request.user.has_permission(permission, 'api'):
            missing_permissions.append(permission)
    
    if missing_permissions:
        return permission_denied_authenticated(
            request,
            message=f"You need the following permissions: {', '.join(missing_permissions)}"
        )
    
    # User has all required permissions
    return render(request, 'api/dashboard.html', {})


# Example 9: Time-based access control
@login_required
def time_based_access_example(request):
    """Example of time-based access control."""
    from django.utils import timezone
    
    current_time = timezone.now().time()
    start_time = timezone.datetime.strptime('09:00', '%H:%M').time()
    end_time = timezone.datetime.strptime('17:00', '%H:%M').time()
    
    # Check if current time is within allowed hours
    if not (start_time <= current_time <= end_time):
        return access_denied(
            request,
            message="This feature is only available during business hours (9:00 AM - 5:00 PM)."
        )
    
    # Check if user has the required permission
    if not request.user.has_permission('access_business_hours_feature'):
        return permission_denied_authenticated(
            request,
            message="You need 'access_business_hours_feature' permission to use this functionality."
        )
    
    return render(request, 'business_hours/feature.html', {})


# Example 10: Resource ownership checking
@login_required
def resource_ownership_example(request, resource_id):
    """Example of checking resource ownership."""
    
    # Get the resource
    try:
        resource = Resource.objects.get(id=resource_id)
    except Resource.DoesNotExist:
        return render(request, '404.html', {}, status=404)
    
    # Check if user owns this resource or has admin access
    if not (request.user == resource.owner or 
            request.user.has_role('Admin') or 
            request.user.has_role('Super Admin')):
        return access_denied(
            request,
            message="You can only access resources that you own."
        )
    
    return render(request, 'resource/detail.html', {'resource': resource}) 