from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Get item from dictionary by key"""
    return dictionary.get(key, 0)

@register.filter
def div(value, arg):
    """Divide value by argument"""
    try:
        return float(value) / float(arg)
    except (ValueError, ZeroDivisionError):
        return 0

@register.filter
def mul(value, arg):
    """Multiply value by argument"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def is_seller(user):
    """Check if user is a seller"""
    if not user or not hasattr(user, 'has_role'):
        return False
    return user.has_role('Seller') 