from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth import get_user_model

User = get_user_model()

@receiver(post_save, sender=User)
def create_welcome_notification(sender, instance, created, **kwargs):
    """Create welcome notification for new users"""
    if created:
        from .models import Notification
        Notification.create_notification(
            user=instance,
            title="Welcome to Atlas Fulfillment!",
            message="Thank you for joining our platform. We're excited to have you on board!",
            notification_type='system',
            priority='low'
        )
        
        # Create notification for all admin users about new user registration
        admin_users = User.objects.filter(
            user_roles__role__name__in=['Admin', 'Super Admin'],
            is_active=True
        ).exclude(id=instance.id).distinct()
        
        for admin_user in admin_users:
            Notification.create_notification(
                user=admin_user,
                title="New User Registration",
                message=f"New user {instance.full_name or instance.email} has registered and is waiting for approval.",
                notification_type='system',
                priority='medium',
                target_role='Admin',
                related_object_type='user',
                related_object_id=instance.id,
                related_url=f"/users/pending-approvals/"
            )

# Note: Product notifications are now handled by sellers/signals.py to avoid duplication

@receiver(post_save, sender='orders.Order')
def create_order_notification(sender, instance, created, **kwargs):
    """Create notification when order status changes"""
    from .models import Notification
    if created:
        # New order notification for seller
        if instance.seller:
            Notification.create_notification(
                user=instance.seller,
                title="New Order Received",
                message=f"You have received a new order #{instance.order_code}.",
                notification_type='new_order',
                priority='high',
                related_object_type='order',
                related_object_id=instance.id,
                related_url=f"/sellers/orders/{instance.id}/"
            )
            
            # Create notification for all admin users
            from users.models import User
            admin_users = User.objects.filter(
                user_roles__role__name__in=['Admin', 'Super Admin'],
                is_active=True
            ).distinct()
            
            for admin_user in admin_users:
                Notification.create_notification(
                    user=admin_user,
                    title="New Order Received",
                    message=f"New order #{instance.order_code} has been received from seller {instance.seller.full_name or instance.seller.email}.",
                    notification_type='new_order',
                    priority='medium',
                    target_role='Admin',
                    related_object_type='order',
                    related_object_id=instance.id,
                    related_url=f"/orders/{instance.id}/"
                )
    
    # Order status change notification
    if hasattr(instance, '_previous_workflow_status'):
        if instance._previous_workflow_status != instance.workflow_status:
            if instance.seller:
                Notification.create_notification(
                    user=instance.seller,
                    title="Order Status Updated",
                    message=f"Order #{instance.order_code} status has been updated to {instance.get_workflow_status_display()}.",
                    notification_type='order_status_changed',
                    priority='medium',
                    related_object_type='order',
                    related_object_id=instance.id,
                    related_url=f"/sellers/orders/{instance.id}/"
                )

@receiver(post_save, sender='inventory.InventoryRecord')
def create_inventory_notification(sender, instance, created, **kwargs):
    """Create notification for low inventory"""
    from .models import Notification
    if not created and instance.quantity <= 10:
        # Low inventory notification
        Notification.create_notification(
            user=instance.product.seller,
            title="Low Inventory Alert",
            message=f"Product '{instance.product.name_en}' is running low on stock. Current quantity: {instance.quantity}",
            notification_type='inventory_low',
            priority='high',
            related_object_type='product',
            related_object_id=instance.product.id,
            related_url=f"/sellers/products/{instance.product.id}/"
        )

@receiver(post_save, sender='users.User')
def create_user_approval_notification(sender, instance, created, **kwargs):
    """Create notification when user account is approved/rejected"""
    from .models import Notification
    if hasattr(instance, '_previous_is_active'):
        if instance._previous_is_active != instance.is_active:
            if instance.is_active:
                Notification.create_notification(
                    user=instance,
                    title="Account Approved",
                    message="Your account has been approved and is now active.",
                    notification_type='account_approved',
                    priority='high'
                )
            else:
                Notification.create_notification(
                    user=instance,
                    title="Account Deactivated",
                    message="Your account has been deactivated. Please contact support for assistance.",
                    notification_type='account_deactivated',
                    priority='high'
                )

# Store previous values for comparison
def store_previous_values(sender, instance, **kwargs):
    """Store previous values for comparison in post_save"""
    if instance.pk:
        try:
            old_instance = sender.objects.get(pk=instance.pk)
            
            # Store workflow_status only for Order model
            if hasattr(instance, 'workflow_status'):
                instance._previous_workflow_status = old_instance.workflow_status
            
            # Store is_active only for User model
            if hasattr(instance, 'is_active'):
                instance._previous_is_active = old_instance.is_active
                
        except sender.DoesNotExist:
            pass

# Connect the signal
post_save.connect(store_previous_values, sender='orders.Order')
post_save.connect(store_previous_values, sender='users.User')
