from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = 'Check pending users for approval'

    def handle(self, *args, **options):
        pending_users = User.objects.filter(approval_status='pending')
        
        self.stdout.write(
            self.style.SUCCESS(f'Found {pending_users.count()} pending users')
        )
        
        for user in pending_users:
            self.stdout.write(
                f'- {user.email} ({user.full_name}) - {user.date_joined.strftime("%Y-%m-%d %H:%M")}'
            ) 