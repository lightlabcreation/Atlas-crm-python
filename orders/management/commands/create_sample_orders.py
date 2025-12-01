from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
import random
from orders.models import Order
from sellers.models import Product

User = get_user_model()

class Command(BaseCommand):
    help = 'Create sample orders for testing delivery orders list'

    def handle(self, *args, **options):
        self.stdout.write('Creating sample orders for delivery testing...')
        
        # Get or create a seller user
        seller, created = User.objects.get_or_create(
            email='seller@atlas.com',
            defaults={
                'full_name': 'Test Seller',
                'phone_number': '+971501234567',
                'is_active': True
            }
        )
        
        if created:
            seller.set_password('Atlas123!')
            seller.save()
            self.stdout.write(f'Created seller user: {seller.email}')
        
        # Get or create a test product
        product, created = Product.objects.get_or_create(
            name_en='Test Product for Delivery',
            defaults={
                'name_ar': 'منتج تجريبي للتوصيل',
                'description': 'Test product for delivery orders',
                'selling_price': 299.00,
                'purchase_price': 200.00,
                'stock_quantity': 100,
                'seller': seller,
                'is_approved': True,
                'category': 'Electronics'
            }
        )
        
        if created:
            self.stdout.write(f'Created test product: {product.name_en}')
        
        # Create sample orders with different statuses
        order_statuses = ['processing', 'confirmed', 'packaged', 'shipped', 'delivered']
        workflow_statuses = ['packaging_completed', 'ready_for_delivery', 'delivery_in_progress', 'delivery_completed']
        
        customers = [
            {'name': 'Ahmed Al Mansouri', 'phone': '+971501234567', 'city': 'Dubai', 'state': 'Dubai', 'country': 'UAE'},
            {'name': 'Fatima Al Zahra', 'phone': '+971502345678', 'city': 'Abu Dhabi', 'state': 'Abu Dhabi', 'country': 'UAE'},
            {'name': 'Omar Al Rashid', 'phone': '+971503456789', 'city': 'Sharjah', 'state': 'Sharjah', 'country': 'UAE'},
            {'name': 'Aisha Al Kuwaiti', 'phone': '+971504567890', 'city': 'Ajman', 'state': 'Ajman', 'country': 'UAE'},
            {'name': 'Khalid Al Fujairah', 'phone': '+971505678901', 'city': 'Fujairah', 'state': 'Fujairah', 'country': 'UAE'},
        ]
        
        orders_created = 0
        
        for i in range(10):
            customer = random.choice(customers)
            status = random.choice(order_statuses)
            workflow_status = random.choice(workflow_statuses)
            
            # Create order with different dates
            order_date = timezone.now() - timedelta(days=random.randint(0, 30))
            
            order, created = Order.objects.get_or_create(
                order_code=f"#{250122 + i:06d}",  # Shorter format: #250122001, #250122002, etc.
                defaults={
                    'customer': customer['name'],
                    'customer_phone': customer['phone'],
                    'date': order_date,
                    'product': product,
                    'quantity': random.randint(1, 5),
                    'price_per_unit': product.selling_price,
                    'status': status,
                    'workflow_status': workflow_status,
                    'seller': seller,
                    'store_link': 'https://example.com/product',
                    'shipping_address': f"Building {random.randint(1, 100)}, Street {random.randint(1, 50)}",
                    'city': customer['city'],
                    'state': customer['state'],
                    'country': customer['country'],
                    'emirate': customer['state'],
                    'notes': f'Sample order {i+1} for delivery testing',
                }
            )
            
            if created:
                orders_created += 1
                self.stdout.write(f'Created order: {order.order_code} - Status: {status} - Workflow: {workflow_status}')
            else:
                self.stdout.write(f'Order already exists: {order.order_code}')
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {orders_created} new orders for delivery testing!')
        )
        
        # Show summary
        total_orders = Order.objects.count()
        processing_orders = Order.objects.filter(status='processing').count()
        confirmed_orders = Order.objects.filter(status='confirmed').count()
        packaged_orders = Order.objects.filter(status='packaged').count()
        shipped_orders = Order.objects.filter(status='shipped').count()
        delivered_orders = Order.objects.filter(status='delivered').count()
        
        self.stdout.write(f'\n=== Order Summary ===')
        self.stdout.write(f'Total Orders: {total_orders}')
        self.stdout.write(f'Processing: {processing_orders}')
        self.stdout.write(f'Confirmed: {confirmed_orders}')
        self.stdout.write(f'Packaged: {packaged_orders}')
        self.stdout.write(f'Shipped: {shipped_orders}')
        self.stdout.write(f'Delivered: {delivered_orders}')
