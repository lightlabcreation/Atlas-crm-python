from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.apps import apps
from .models import DeliveryCompany


@receiver(post_migrate)
def create_default_delivery_company(sender, **kwargs):
    """Create a default delivery company after migrations if none exists"""
    if sender.name == 'delivery':
        # Check if any delivery company exists
        if not DeliveryCompany.objects.exists():
            DeliveryCompany.objects.create(
                name_en='Default Delivery Company',
                name_ar='شركة التوصيل الافتراضية',
                base_cost=10.00,
                is_active=True
            )
