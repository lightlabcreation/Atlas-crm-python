from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction

User = get_user_model()

class Command(BaseCommand):
    help = 'Deactivate user accounts'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            help='Email of the user to deactivate'
        )
        parser.add_argument(
            '--user-id',
            type=int,
            help='ID of the user to deactivate'
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Deactivate all active users (except superusers)'
        )
        parser.add_argument(
            '--list-active',
            action='store_true',
            help='List all active users'
        )
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Confirm the action (required for --all)'
        )

    def handle(self, *args, **options):
        if options['list_active']:
            self.list_active_users()
            return

        if options['all']:
            if not options['confirm']:
                self.stdout.write(
                    self.style.ERROR('Use --confirm flag when using --all option!')
                )
                return
            self.deactivate_all_users()
            return

        if options['email']:
            self.deactivate_user_by_email(options['email'])
            return

        if options['user_id']:
            self.deactivate_user_by_id(options['user_id'])
            return

        # If no specific option provided, show help
        self.stdout.write(
            self.style.ERROR('Please specify --email, --user-id, --all, or --list-active')
        )
        self.stdout.write('Use --help for more information')

    def list_active_users(self):
        """List all active users"""
        active_users = User.objects.filter(is_active=True)
        
        if not active_users.exists():
            self.stdout.write(
                self.style.WARNING('No active users found!')
            )
            return

        self.stdout.write(
            self.style.SUCCESS(f'Found {active_users.count()} active users:')
        )
        
        for user in active_users:
            user_type = "Superuser" if user.is_superuser else "Regular User"
            self.stdout.write(
                f'  - ID: {user.id}, Email: {user.email}, Name: {user.get_full_name() or "N/A"} ({user_type})'
            )

    def deactivate_user_by_email(self, email):
        """Deactivate user by email"""
        try:
            user = User.objects.get(email=email)
            self.deactivate_user(user)
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'User with email "{email}" not found!')
            )

    def deactivate_user_by_id(self, user_id):
        """Deactivate user by ID"""
        try:
            user = User.objects.get(id=user_id)
            self.deactivate_user(user)
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'User with ID "{user_id}" not found!')
            )

    def deactivate_all_users(self):
        """Deactivate all active users except superusers"""
        active_users = User.objects.filter(is_active=True, is_superuser=False)
        
        if not active_users.exists():
            self.stdout.write(
                self.style.SUCCESS('No regular active users found!')
            )
            return

        count = 0
        with transaction.atomic():
            for user in active_users:
                user.is_active = False
                user.save()
                count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Deactivated user: {user.email}')
                )

        self.stdout.write(
            self.style.SUCCESS(f'Successfully deactivated {count} users!')
        )

    def deactivate_user(self, user):
        """Deactivate a single user"""
        if not user.is_active:
            self.stdout.write(
                self.style.WARNING(f'User "{user.email}" is already inactive!')
            )
            return

        if user.is_superuser:
            self.stdout.write(
                self.style.ERROR(f'Cannot deactivate superuser "{user.email}"!')
            )
            return

        user.is_active = False
        user.save()
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully deactivated user: {user.email}')
        )
        self.stdout.write(f'  - Name: {user.get_full_name() or "N/A"}')
        self.stdout.write(f'  - Email: {user.email}')
        self.stdout.write(f'  - ID: {user.id}')
