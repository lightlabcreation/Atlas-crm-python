from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = 'Check user roles and permissions'

    def add_arguments(self, parser):
        parser.add_argument('email', type=str, help='Email of the user to check')

    def handle(self, *args, **options):
        email = options['email']
        
        try:
            user = User.objects.get(email=email)
            
            self.stdout.write(
                self.style.SUCCESS(f'User: {user.email}')
            )
            self.stdout.write(f'Full Name: {user.full_name}')
            self.stdout.write(f'Is Superuser: {user.is_superuser}')
            self.stdout.write(f'Is Staff: {user.is_staff}')
            self.stdout.write(f'Is Active: {user.is_active}')
            self.stdout.write(f'Approval Status: {user.approval_status}')
            
            # Check roles
            self.stdout.write('\nRoles:')
            for user_role in user.user_roles.all():
                self.stdout.write(f'- {user_role.role.name} (Active: {user_role.is_active}, Primary: {user_role.is_primary})')
            
            # Check specific role properties
            self.stdout.write('\nRole Properties:')
            self.stdout.write(f'has_role_admin: {user.has_role_admin}')
            self.stdout.write(f'has_role_super_admin: {user.has_role_super_admin}')
            self.stdout.write(f'has_role_seller: {user.has_role_seller}')
            
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'User with email {email} not found')
            ) 