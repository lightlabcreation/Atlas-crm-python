from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = 'Fix existing superusers to be approved and active'

    def handle(self, *args, **options):
        # Get all superusers
        superusers = User.objects.filter(is_superuser=True)
        
        for user in superusers:
            user.is_active = True
            user.approval_status = 'approved'
            user.save()
            self.stdout.write(
                self.style.SUCCESS(f'Fixed superuser: {user.email}')
            )
        
        self.stdout.write(
            self.style.SUCCESS(f'Fixed {superusers.count()} superuser(s)')
        ) 