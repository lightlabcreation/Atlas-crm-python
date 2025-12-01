from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from sellers.models import Product
from decimal import Decimal

User = get_user_model()

class Command(BaseCommand):
    help = 'Create test products for sellers'

    def add_arguments(self, parser):
        parser.add_argument('--seller-email', type=str, help='Email of the seller to create products for')
        parser.add_argument('--count', type=int, default=5, help='Number of products to create')

    def handle(self, *args, **options):
        seller_email = options['seller_email']
        count = options['count']
        
        try:
            seller = User.objects.get(email=seller_email)
            if not seller.has_role('Seller'):
                self.stdout.write(
                    self.style.ERROR(f'User {seller_email} does not have Seller role')
                )
                return
                
            # Create test products
            for i in range(count):
                product = Product.objects.create(
                    name_en=f'Test Product {i+1}',
                    name_ar=f'منتج تجريبي {i+1}',
                    description=f'This is a test product number {i+1}',
                    selling_price=Decimal('99.99'),
                    purchase_price=Decimal('50.00'),
                    stock_quantity=100 + i * 10,
                    seller=seller,
                    is_approved=True  # Auto-approve for testing
                )
                self.stdout.write(
                    self.style.SUCCESS(f'Created product: {product.name_en} (ID: {product.id})')
                )
                
            self.stdout.write(
                self.style.SUCCESS(f'Successfully created {count} test products for {seller_email}')
            )
            
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'Seller with email {seller_email} not found')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error creating products: {str(e)}')
            )
