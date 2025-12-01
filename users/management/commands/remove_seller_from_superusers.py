from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from roles.models import Role, UserRole

User = get_user_model()

class Command(BaseCommand):
    help = 'Remove Seller role from superusers'

    def handle(self, *args, **options):
        # Get Seller role
        seller_role = Role.objects.filter(name='Seller', is_active=True).first()
        
        if not seller_role:
            self.stdout.write(
                self.style.WARNING('Seller role not found')
            )
            return
        
        # Get all superusers
        superusers = User.objects.filter(is_superuser=True)
        
        for user in superusers:
            # Remove Seller role from superusers
            seller_user_roles = UserRole.objects.filter(
                user=user, 
                role=seller_role
            )
            
            if seller_user_roles.exists():
                seller_user_roles.delete()
                self.stdout.write(
                    self.style.SUCCESS(f'Removed Seller role from: {user.email}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'User {user.email} does not have Seller role')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'Processed {superusers.count()} superuser(s)')
        ) 