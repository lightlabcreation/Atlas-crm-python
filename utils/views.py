from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.utils.translation import gettext as _


def permission_denied(request, message=None, context=None):
    """
    Render a permission denied page with custom message and context.
    This view can be used across the entire system for consistent permission handling.
    
    Args:
        request: Django request object
        message: Custom message to display (optional)
        context: Additional context data (optional)
    """
    if context is None:
        context = {}
    
    if message:
        context['custom_message'] = message
    
    # Set default context
    context.update({
        'page_title': _('Permission Denied'),
        'error_type': 'permission_denied',
        'show_contact_admin': True,
    })
    
    return render(request, 'permission_denied.html', context, status=403)


@login_required
def permission_denied_authenticated(request, message=None, context=None):
    """
    Render a permission denied page for authenticated users.
    This view requires login and provides user-specific context.
    
    Args:
        request: Django request object
        message: Custom message to display (optional)
        context: Additional context data (optional)
    """
    if context is None:
        context = {}
    
    if message:
        context['custom_message'] = message
    
    # Add user-specific context
    context.update({
        'page_title': _('Permission Denied'),
        'error_type': 'permission_denied',
        'show_contact_admin': True,
        'user_role': getattr(request.user, 'get_primary_role', lambda: None)() if hasattr(request.user, 'get_primary_role') else None,
        'can_contact_admin': getattr(request.user, 'has_role', lambda x: False)('Admin') or getattr(request.user, 'has_role', lambda x: False)('Super Admin'),
    })
    
    return render(request, 'permission_denied.html', context, status=403)


def access_denied(request, message=None, context=None):
    """
    Render an access denied page for general access restrictions.
    This is different from permission denied as it's not role-based.
    
    Args:
        request: Django request object
        message: Custom message to display (optional)
        context: Additional context data (optional)
    """
    if context is None:
        context = {}
    
    if message:
        context['custom_message'] = message
    
    context.update({
        'page_title': _('Access Denied'),
        'error_type': 'access_denied',
        'show_contact_admin': False,
    })
    
    return render(request, 'permission_denied.html', context, status=403)


def test_simple_permission_denied(request):
    """
    Simple test view to verify the permission denied system is working.
    """
    context = {
        'custom_message': 'This is a test message from the simple permission denied view.',
        'error_type': 'permission_denied',
        'page_title': 'Test Permission Denied'
    }
    
    return render(request, 'simple_permission_denied.html', context, status=403) 