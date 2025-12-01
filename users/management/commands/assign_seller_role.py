from django.core.management.base import BaseCommand
from users.models import User
from roles.models import Role, UserRole

class Command(BaseCommand):
    help = 'Assign Seller role to a user'

    def add_arguments(self, parser):
        parser.add_argument('email', type=str, help='User email')

    def handle(self, *args, **options):
        email = options['email']
        
        try:
            # Get the user
            user = User.objects.get(email=email)
            self.stdout.write(f'Found user: {user.email}')
            
            # Get or create Seller role
            seller_role, created = Role.objects.get_or_create(
                name='Seller',
                defaults={
                    'description': 'Seller role for managing products and orders',
                    'is_active': True,
                    'is_protected': True
                }
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS('Created Seller role'))
            else:
                self.stdout.write('Seller role already exists')
            
            # Check if user already has this role
            existing_role = UserRole.objects.filter(user=user, role=seller_role).first()
            if existing_role:
                self.stdout.write(f'User already has role: {existing_role.role.name}')
            else:
                # Assign the role
                UserRole.objects.create(
                    user=user,
                    role=seller_role,
                    is_primary=True,
                    is_active=True
                )
                self.stdout.write(self.style.SUCCESS('Role assigned successfully!'))
            
            # Check user's roles
            self.stdout.write(f'User primary role: {user.primary_role}')
            all_roles = [r.role.name for r in user.user_roles.filter(is_active=True)]
            self.stdout.write(f'User all roles: {all_roles}')
            
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'User with email {email} not found!'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {e}'))
