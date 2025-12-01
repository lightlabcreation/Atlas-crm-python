"""
Management command to fix email verification for admin-created users.

This command sets email_verified=True for all users who were approved by an admin
but still have email_verified=False. These are users created by admins who should
not need email verification.
"""

from django.core.management.base import BaseCommand
from users.models import User


class Command(BaseCommand):
    help = 'Fix email verification for admin-created users'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without actually updating',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        # Find all users who were approved by an admin but don't have email_verified=True
        # These are admin-created users who should not need email verification
        # Also include staff users and superusers who don't have email_verified=True
        from django.db.models import Q
        admin_created_users = User.objects.filter(
            Q(
                approval_status='approved',
                approved_by__isnull=False,
                email_verified=False
            ) | Q(
                is_staff=True,
                email_verified=False
            ) | Q(
                is_superuser=True,
                email_verified=False
            )
        ).distinct()
        
        count = admin_created_users.count()
        
        if count == 0:
            self.stdout.write(self.style.SUCCESS('No users need to be updated.'))
            return
        
        self.stdout.write(f'Found {count} users who need to be updated.')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN - No changes will be made'))
            
        for user in admin_created_users:
            self.stdout.write(
                f'User: {user.email} (Approved by: {user.approved_by.email if user.approved_by else "Unknown"})'
            )
            if not dry_run:
                user.email_verified = True
                user.save()
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f'\nDRY RUN complete. Would update {count} users.\n'
                    'Run without --dry-run to apply changes.'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f'\nSuccessfully updated {count} users.')
            )

