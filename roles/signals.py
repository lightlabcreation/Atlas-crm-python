from django.db.models.signals import pre_delete
from django.dispatch import receiver
from django.core.exceptions import PermissionDenied
from .models import Role

@receiver(pre_delete, sender=Role)
def prevent_build_in_role_deletion(sender, instance, **kwargs):
    """Prevent deletion of build-in roles and default roles"""
    build_in_roles = [
        'Call Center Agent',
        'Call Center Manager',
        'Accountant', 
        'Stock Keeper',
        'Delivery Agent',
        'Delivery Manager',
        'Packaging Agent',
        'Seller',
        'Super Admin',
        'Admin',
    ]
    
    # Prevent deletion of build-in roles or default roles
    if instance.name in build_in_roles or instance.is_default:
        role_type = "build-in" if instance.name in build_in_roles else "default"
        raise PermissionDenied(
            f"Cannot delete {role_type} role '{instance.name}'. This role is required by the system."
        ) 