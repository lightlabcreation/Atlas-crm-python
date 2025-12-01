from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = 'Test user roles and permissions'

    def add_arguments(self, parser):
        parser.add_argument('email', type=str, help='User email to test')

    def handle(self, *args, **options):
        email = options['email']
        
        try:
            user = User.objects.get(email=email)
            self.stdout.write(f"User: {user.email}")
            self.stdout.write(f"Is superuser: {user.is_superuser}")
            self.stdout.write(f"Is staff: {user.is_staff}")
            self.stdout.write(f"Is active: {user.is_active}")
            self.stdout.write(f"Approval status: {user.approval_status}")
            
            # Check roles using the correct method
            roles = user.get_all_roles()
            self.stdout.write(f"Roles: {[role.name for role in roles]}")
            
            # Check role methods
            self.stdout.write(f"has_role_admin: {user.has_role_admin}")
            self.stdout.write(f"has_role_super_admin: {user.has_role_super_admin}")
            self.stdout.write(f"has_role_seller: {user.has_role_seller}")
            
            # Check if user should see pending approvals
            should_see = user.has_role_super_admin or user.has_role_admin or user.is_superuser
            self.stdout.write(f"Should see pending approvals: {should_see}")
            
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'User with email {email} does not exist')
            ) 