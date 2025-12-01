from django.core.management.base import BaseCommand
from orders.models import Order, OrderItem
from callcenter.models import OrderAssignment, CallLog, OrderStatusHistory
from django.db import transaction

class Command(BaseCommand):
    help = 'Clear all orders and related data from the database'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Confirm that you want to delete all orders',
        )
    
    def handle(self, *args, **options):
        if not options['confirm']:
            self.stdout.write(
                self.style.WARNING(
                    'This command will delete ALL orders and related data!\n'
                    'To proceed, run: python manage.py clear_all_orders --confirm'
                )
            )
            return
        
        with transaction.atomic():
            # Delete related data first
            self.stdout.write('Deleting call logs...')
            CallLog.objects.all().delete()
            
            self.stdout.write('Deleting order status history...')
            OrderStatusHistory.objects.all().delete()
            
            self.stdout.write('Deleting order assignments...')
            OrderAssignment.objects.all().delete()
            
            self.stdout.write('Deleting order items...')
            OrderItem.objects.all().delete()
            
            self.stdout.write('Deleting orders...')
            Order.objects.all().delete()
            
            self.stdout.write(
                self.style.SUCCESS(
                    'Successfully cleared all orders and related data!'
                )
            )
