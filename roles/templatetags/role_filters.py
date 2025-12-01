from django import template
from roles.models import UserRole

register = template.Library()

@register.filter
def has_role(user, role_name):
    """Check if user has a specific role"""
    if not user or not user.is_authenticated:
        return False
    
    return user.has_role(role_name)

@register.filter
def has_any_role(user, role_names):
    """Check if user has any of the specified roles"""
    if not user or not user.is_authenticated:
        return False
    
    roles = [role.strip() for role in role_names.split(',')]
    return any(user.has_role(role) for role in roles)

@register.filter
def has_admin_role(user):
    """Check if user has admin role (Admin, Super Admin, or is superuser)"""
    if not user or not user.is_authenticated:
        return False
    
    return user.has_role_admin

@register.filter
def has_callcenter_role(user):
    """Check if user has call center role"""
    if not user or not user.is_authenticated:
        return False
    
    return user.has_role_call_center_agent or user.has_role_call_center_manager

@register.filter
def is_admin(user):
    """Check if user is admin or superuser"""
    if not user or not hasattr(user, 'has_role'):
        return False
    return user.is_superuser or user.has_role('Admin') or user.has_role('Super Admin')

@register.filter
def is_seller(user):
    """Check if user is seller"""
    if not user or not hasattr(user, 'has_role'):
        return False
    return user.has_role('Seller')