from django.core.management.base import BaseCommand
from users.models import User
from roles.models import Role, UserRole
from sellers.models import Product

class Command(BaseCommand):
    help = 'Fix seller data and create test seller with products'

    def handle(self, *args, **options):
        self.stdout.write("=== Fixing Seller Products Issue ===")

        # Create or get seller user
        seller, created = User.objects.get_or_create(
            username='seller',
            defaults={
                'email': 'seller@example.com',
                'first_name': 'Test',
                'last_name': 'Seller',
                'is_active': True,
                'is_staff': True
            }
        )

        if created:
            seller.set_password('seller123')
            seller.save()
            self.stdout.write(self.style.SUCCESS(f"✅ Created seller user: {seller.username}"))
        else:
            self.stdout.write(f"✅ Seller user exists: {seller.username}")

        # Get or create Seller role
        seller_role, created = Role.objects.get_or_create(
            name='Seller',
            defaults={
                'description': 'Seller role for managing products',
                'is_active': True
            }
        )

        if created:
            self.stdout.write(self.style.SUCCESS(f"✅ Created Seller role"))
        else:
            self.stdout.write(f"✅ Seller role exists")

        # Assign role to user
        user_role, created = UserRole.objects.get_or_create(
            user=seller,
            role=seller_role,
            defaults={
                'is_primary': True,
                'is_active': True
            }
        )

        if created:
            self.stdout.write(self.style.SUCCESS(f"✅ Assigned Seller role to {seller.username}"))
        else:
            self.stdout.write(f"✅ User already has Seller role")

        # Create test product
        product, created = Product.objects.get_or_create(
            name_en='Test Product',
            defaults={
                'name_ar': 'منتج تجريبي',
                'description': 'This is a test product for demonstration',
                'selling_price': 100.00,
                'purchase_price': 80.00,
                'stock_quantity': 50,
                'seller': seller,
                'is_approved': True,
                'category': 'Electronics'
            }
        )

        if created:
            self.stdout.write(self.style.SUCCESS(f"✅ Created test product: {product.name_en}"))
        else:
            self.stdout.write(f"✅ Test product exists: {product.name_en}")

        # Create another test product
        product2, created = Product.objects.get_or_create(
            name_en='MacBook Air',
            defaults={
                'name_ar': 'ماك بوك إير',
                'description': 'Apple MacBook Air with M1 chip',
                'selling_price': 4500.00,
                'purchase_price': 4000.00,
                'stock_quantity': 25,
                'seller': seller,
                'is_approved': True,
                'category': 'Electronics'
            }
        )

        if created:
            self.stdout.write(self.style.SUCCESS(f"✅ Created test product: {product2.name_en}"))
        else:
            self.stdout.write(f"✅ Test product exists: {product2.name_en}")

        # Check user roles
        self.stdout.write(f"\n=== User Information ===")
        self.stdout.write(f"Username: {seller.username}")
        self.stdout.write(f"Email: {seller.email}")
        self.stdout.write(f"Has Seller role: {seller.has_role('Seller')}")
        self.stdout.write(f"Active roles: {[ur.role.name for ur in seller.user_roles.filter(is_active=True)]}")

        # Check products
        products = Product.objects.filter(seller=seller)
        self.stdout.write(f"\n=== Products for Seller ===")
        self.stdout.write(f"Products count: {products.count()}")
        for p in products:
            self.stdout.write(f"- {p.name_en} (Approved: {p.is_approved})")

        self.stdout.write(f"\n=== Login Information ===")
        self.stdout.write(f"Username: seller")
        self.stdout.write(f"Password: seller123")
        self.stdout.write(f"URL: http://127.0.0.1:8000/users/login/")
        
        self.stdout.write(self.style.SUCCESS('\n✅ All done! You can now login with seller account and see products.'))

