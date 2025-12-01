from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Order
from callcenter.services import AutoOrderDistributionService

@receiver(post_save, sender=Order)
def auto_assign_new_order(sender, instance, created, **kwargs):
    """Automatically assign new orders to call center agents"""
    if created and instance.status in ['pending', 'pending_confirmation']:
        # Auto-assign the new order
        success, result = AutoOrderDistributionService.auto_assign_new_order(instance)
        
        if success:
            print(f"Order {instance.order_code} automatically assigned to agent: {result.get_full_name()}")
        else:
            print(f"Failed to auto-assign order {instance.order_code}: {result}")
