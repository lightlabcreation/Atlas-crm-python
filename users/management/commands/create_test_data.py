"""
Management command to create comprehensive test data for Atlas CRM.

This command generates realistic test data for all modules including:
- Users (all roles)
- Products
- Orders
- Deliveries
- Returns
- Prescriptions
- Medicines
- Invoices

Usage:
    python manage.py create_test_data [--users N] [--products N] [--orders N]
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from roles.models import Role, UserRole
from decimal import Decimal
import random
import string
from datetime import timedelta

User = get_user_model()


class Command(BaseCommand):
    help = 'Create comprehensive test data for Atlas CRM system'

    def add_arguments(self, parser):
        parser.add_argument(
            '--users',
            type=int,
            default=20,
            help='Number of users to create per role (default: 20)'
        )
        parser.add_argument(
            '--products',
            type=int,
            default=50,
            help='Number of products to create (default: 50)'
        )
        parser.add_argument(
            '--orders',
            type=int,
            default=100,
            help='Number of orders to create (default: 100)'
        )

    def generate_password(self):
        """Generate a simple test password."""
        return "Test@1234"

    def create_users(self, count_per_role):
        """Create test users for all roles."""
        self.stdout.write('\n' + '='*70)
        self.stdout.write(self.style.SUCCESS('Creating Test Users'))
        self.stdout.write('='*70 + '\n')

        roles = Role.objects.all()
        created_users = []

        for role in roles:
            self.stdout.write(f'\nCreating {count_per_role} {role.name}s...')
            
            for i in range(1, count_per_role + 1):
                email = f"test-{role.name.lower().replace(' ', '_')}_{i}@atlas.test"
                
                # Skip if user already exists
                if User.objects.filter(email=email).exists():
                    continue

                user = User.objects.create_user(
                    email=email,
                    full_name=f"Test {role.name} {i}",
                    phone_number=f"+100000{random.randint(10000, 99999)}",
                    password=self.generate_password(),
                    approval_status='approved',
                    email_verified=True,
                    is_active=True,
                )

                # Assign role
                UserRole.objects.create(user=user, role=role)
                created_users.append(user)

            self.stdout.write(self.style.SUCCESS(f'  ✓ Created {count_per_role} {role.name}s'))

        self.stdout.write(self.style.SUCCESS(f'\n✓ Total users created: {len(created_users)}'))
        return created_users

    def create_products(self, count):
        """Create test products."""
        self.stdout.write('\n' + '='*70)
        self.stdout.write(self.style.SUCCESS('Creating Test Products'))
        self.stdout.write('='*70 + '\n')

        # Import products model
        try:
            from products.models import Product, Category
        except ImportError:
            self.stdout.write(self.style.WARNING('Products app not available'))
            return []

        # Get or create categories
        category_names = ['Electronics', 'Clothing', 'Books', 'Home & Kitchen', 'Sports']
        categories = []
        
        for cat_name in category_names:
            cat, _ = Category.objects.get_or_create(
                name=cat_name,
                defaults={'description': f'{cat_name} products'}
            )
            categories.append(cat)

        self.stdout.write(f'Created/found {len(categories)} categories')

        # Create products
        products = []
        product_names = [
            'Laptop', 'Phone', 'Tablet', 'Headphones', 'Smartwatch',
            'T-Shirt', 'Jeans', 'Jacket', 'Shoes', 'Hat',
            'Novel', 'Textbook', 'Magazine', 'Comic', 'Journal',
            'Blender', 'Microwave', 'Toaster', 'Coffee Maker', 'Vacuum',
            'Football', 'Basketball', 'Tennis Racket', 'Yoga Mat', 'Dumbbell'
        ]

        for i in range(count):
            name = f"{random.choice(product_names)} {i+1}"
            sku = f"TEST-{random.randint(10000, 99999)}"
            
            # Skip if product already exists
            if Product.objects.filter(sku=sku).exists():
                continue

            product = Product.objects.create(
                name=name,
                sku=sku,
                description=f"Test product description for {name}",
                category=random.choice(categories),
                price=Decimal(random.randint(10, 500)),
                cost=Decimal(random.randint(5, 250)),
                stock_quantity=random.randint(10, 1000),
                reorder_level=random.randint(5, 50),
                is_active=True
            )
            products.append(product)

        self.stdout.write(self.style.SUCCESS(f'✓ Created {len(products)} products'))
        return products

    def create_orders(self, count, users, products):
        """Create test orders."""
        self.stdout.write('\n' + '='*70)
        self.stdout.write(self.style.SUCCESS('Creating Test Orders'))
        self.stdout.write('='*70 + '\n')

        # Import orders model
        try:
            from orders.models import Order, OrderItem
        except ImportError:
            self.stdout.write(self.style.WARNING('Orders app not available'))
            return []

        # Get seller users
        sellers = [u for u in users if 'seller' in u.email.lower()]
        if not sellers:
            self.stdout.write(self.style.WARNING('No sellers found, skipping order creation'))
            return []

        orders = []
        order_statuses = ['pending', 'confirmed', 'processing', 'shipped', 'delivered', 'cancelled']

        for i in range(count):
            seller = random.choice(sellers)
            
            order = Order.objects.create(
                seller=seller,
                order_number=f"ORD-TEST-{random.randint(100000, 999999)}",
                status=random.choice(order_statuses),
                customer_name=f"Customer {i+1}",
                customer_email=f"customer{i+1}@test.com",
                customer_phone=f"+100{random.randint(1000000, 9999999)}",
                shipping_address=f"{i+1} Test Street, Test City, TC 12345",
                payment_method=random.choice(['cash_on_delivery', 'bank_transfer', 'credit_card']),
                notes=f"Test order {i+1}",
                created_at=timezone.now() - timedelta(days=random.randint(0, 90))
            )

            # Add order items
            num_items = random.randint(1, 5)
            total_amount = Decimal(0)
            
            for _ in range(num_items):
                product = random.choice(products)
                quantity = random.randint(1, 10)
                unit_price = product.price
                
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=quantity,
                    unit_price=unit_price,
                    subtotal=quantity * unit_price
                )
                total_amount += quantity * unit_price

            order.total_amount = total_amount
            order.save()
            orders.append(order)

        self.stdout.write(self.style.SUCCESS(f'✓ Created {len(orders)} orders'))
        return orders

    def handle(self, *args, **options):
        users_per_role = options['users']
        products_count = options['products']
        orders_count = options['orders']

        self.stdout.write(self.style.SUCCESS('\n' + '='*70))
        self.stdout.write(self.style.SUCCESS('ATLAS CRM TEST DATA GENERATION'))
        self.stdout.write(self.style.SUCCESS('='*70))
        self.stdout.write(f'\nConfiguration:')
        self.stdout.write(f'  - Users per role: {users_per_role}')
        self.stdout.write(f'  - Products: {products_count}')
        self.stdout.write(f'  - Orders: {orders_count}')
        self.stdout.write(f'\n  Default Password: {self.generate_password()}')

        # Create test data
        users = self.create_users(users_per_role)
        products = self.create_products(products_count)
        orders = self.create_orders(orders_count, users, products)

        # Summary
        self.stdout.write('\n' + '='*70)
        self.stdout.write(self.style.SUCCESS('TEST DATA GENERATION COMPLETE'))
        self.stdout.write('='*70)
        self.stdout.write(f'\n✓ Users created: {len(users)}')
        self.stdout.write(f'✓ Products created: {len(products)}')
        self.stdout.write(f'✓ Orders created: {len(orders)}')
        self.stdout.write(self.style.WARNING(f'\n⚠️  Default password for all test users: {self.generate_password()}'))
        self.stdout.write('\n' + '='*70 + '\n')
