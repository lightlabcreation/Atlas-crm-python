from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from roles.models import Role, UserRole

User = get_user_model()

class Command(BaseCommand):
    help = 'Assign Admin role to superusers'

    def handle(self, *args, **options):
        # Get or create Admin role
        admin_role, created = Role.objects.get_or_create(
            name='Admin',
            defaults={
                'description': 'Administrator role with full access',
                'is_active': True
            }
        )
        
        if created:
            self.stdout.write(
                self.style.SUCCESS(f'Created Admin role')
            )
        
        # Get all superusers
        superusers = User.objects.filter(is_superuser=True)
        
        for user in superusers:
            # Check if user already has Admin role
            if not user.has_role('Admin'):
                # Create UserRole for Admin
                UserRole.objects.get_or_create(
                    user=user,
                    role=admin_role,
                    defaults={
                        'is_active': True
                    }
                )
                self.stdout.write(
                    self.style.SUCCESS(f'Assigned Admin role to: {user.email}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'User {user.email} already has Admin role')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'Processed {superusers.count()} superuser(s)')
        ) 