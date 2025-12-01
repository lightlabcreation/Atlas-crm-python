from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from .models import Product

@receiver(post_save, sender=Product)
def create_product_notification(sender, instance, created, **kwargs):
    """Create notification when a product is created or updated"""
    try:
        from notifications.models import Notification
        
        if created:
            # Product was just created
            if not instance.is_approved:
                # Create pending approval notification for seller
                Notification.create_notification(
                    user=instance.seller,
                    title='Product Pending Approval',
                    message=f'Your product "{instance.name_en}" has been submitted and is waiting for admin approval.',
                    notification_type='product_pending',
                    priority='medium',
                    related_object_type='product',
                    related_object_id=instance.id,
                    related_url=f"/sellers/products/{instance.id}/"
                )
                
                # Create notification for all admin users
                from users.models import User
                from roles.models import UserRole
                
                # Get all admin users
                admin_users = User.objects.filter(
                    user_roles__role__name__in=['Admin', 'Super Admin'],
                    is_active=True
                ).distinct()
                
                # Create notifications for each admin
                for admin_user in admin_users:
                    Notification.create_notification(
                        user=admin_user,
                        title='New Product Pending Approval',
                        message=f'Product "{instance.name_en}" from seller {instance.seller.full_name or instance.seller.email} is waiting for approval.',
                        notification_type='product_pending',
                        priority='high',
                        target_role='Admin',
                        related_object_type='product',
                        related_object_id=instance.id,
                        related_url=f"/inventory/product-approval/"
                    )
            else:
                # Product was auto-approved (created by admin) - only notify if seller is not an admin
                if (instance.seller and 
                    not instance.seller.is_superuser and 
                    not instance.seller.has_role('Admin') and 
                    not instance.seller.has_role('Super Admin')):
                    Notification.create_notification(
                        user=instance.seller,
                        title='Product Approved',
                        message=f'Your product "{instance.name_en}" has been automatically approved and is now live.',
                        notification_type='product_approved',
                        priority='medium',
                        related_object_type='product',
                        related_object_id=instance.id,
                        related_url=f"/sellers/products/{instance.id}/"
                    )
        else:
            # Product was updated
            if instance.is_approved and instance.approved_by:
                # Product was approved - only notify if seller is not an admin
                if (instance.seller and 
                    not instance.seller.is_superuser and 
                    not instance.seller.has_role('Admin') and 
                    not instance.seller.has_role('Super Admin')):
                    Notification.create_notification(
                        user=instance.seller,
                        title='Product Approved',
                        message=f'Your product "{instance.name_en}" has been approved and is now live.',
                        notification_type='product_approved',
                        priority='medium',
                        related_object_type='product',
                        related_object_id=instance.id,
                        related_url=f"/sellers/products/{instance.id}/"
                    )
            
            # Don't create notification for admin who approved the product
            # Admins don't need to be notified of their own actions
            elif not instance.is_approved and instance.approved_by is None:
                # Product approval was revoked
                Notification.create_notification(
                    user=instance.seller,
                    title='Product Re-approval Required',
                    message=f'Your product "{instance.name_en}" needs to be re-approved. Please review and resubmit.',
                    notification_type='product_pending',
                    priority='high',
                    related_object_type='product',
                    related_object_id=instance.id,
                    related_url=f"/sellers/products/{instance.id}/"
                )
                
                # Create notification for all admin users about re-approval needed
                from users.models import User
                
                admin_users = User.objects.filter(
                    user_roles__role__name__in=['Admin', 'Super Admin'],
                    is_active=True
                ).distinct()
                
                for admin_user in admin_users:
                    Notification.create_notification(
                        user=admin_user,
                        title='Product Re-approval Required',
                        message=f'Product "{instance.name_en}" from seller {instance.seller.full_name or instance.seller.email} needs re-approval.',
                        notification_type='product_pending',
                        priority='high',
                        target_role='Admin',
                        related_object_type='product',
                        related_object_id=instance.id,
                        related_url=f"/inventory/product-approval/"
                    )
    except ImportError:
        # Notifications app not available yet
        pass
