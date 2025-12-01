from django.core.management.base import BaseCommand
from delivery.models import DeliveryCompany


class Command(BaseCommand):
    help = 'Create a default delivery company if none exists'

    def handle(self, *args, **options):
        # Check if any delivery company exists
        if DeliveryCompany.objects.exists():
            self.stdout.write(
                self.style.WARNING('Delivery companies already exist. Skipping creation.')
            )
            return

        # Create default delivery company
        delivery_company = DeliveryCompany.objects.create(
            name_en='Default Delivery Company',
            name_ar='شركة التوصيل الافتراضية',
            base_cost=10.00,
            is_active=True
        )

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created default delivery company: {delivery_company.name_en}'
            )
        )
