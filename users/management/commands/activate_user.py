from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction

User = get_user_model()

class Command(BaseCommand):
    help = 'Activate user accounts'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            help='Email of the user to activate'
        )
        parser.add_argument(
            '--user-id',
            type=int,
            help='ID of the user to activate'
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Activate all inactive users'
        )
        parser.add_argument(
            '--list-inactive',
            action='store_true',
            help='List all inactive users'
        )

    def handle(self, *args, **options):
        if options['list_inactive']:
            self.list_inactive_users()
            return

        if options['all']:
            self.activate_all_users()
            return

        if options['email']:
            self.activate_user_by_email(options['email'])
            return

        if options['user_id']:
            self.activate_user_by_id(options['user_id'])
            return

        # If no specific option provided, show help
        self.stdout.write(
            self.style.ERROR('Please specify --email, --user-id, --all, or --list-inactive')
        )
        self.stdout.write('Use --help for more information')

    def list_inactive_users(self):
        """List all inactive users"""
        inactive_users = User.objects.filter(is_active=False)
        
        if not inactive_users.exists():
            self.stdout.write(
                self.style.SUCCESS('No inactive users found!')
            )
            return

        self.stdout.write(
            self.style.WARNING(f'Found {inactive_users.count()} inactive users:')
        )
        
        for user in inactive_users:
            self.stdout.write(
                f'  - ID: {user.id}, Email: {user.email}, Name: {user.get_full_name() or "N/A"}'
            )

    def activate_user_by_email(self, email):
        """Activate user by email"""
        try:
            user = User.objects.get(email=email)
            self.activate_user(user)
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'User with email "{email}" not found!')
            )

    def activate_user_by_id(self, user_id):
        """Activate user by ID"""
        try:
            user = User.objects.get(id=user_id)
            self.activate_user(user)
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'User with ID "{user_id}" not found!')
            )

    def activate_all_users(self):
        """Activate all inactive users"""
        inactive_users = User.objects.filter(is_active=False)
        
        if not inactive_users.exists():
            self.stdout.write(
                self.style.SUCCESS('No inactive users found!')
            )
            return

        count = 0
        with transaction.atomic():
            for user in inactive_users:
                user.is_active = True
                user.save()
                count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Activated user: {user.email}')
                )

        self.stdout.write(
            self.style.SUCCESS(f'Successfully activated {count} users!')
        )

    def activate_user(self, user):
        """Activate a single user"""
        if user.is_active:
            self.stdout.write(
                self.style.WARNING(f'User "{user.email}" is already active!')
            )
            return

        user.is_active = True
        user.save()
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully activated user: {user.email}')
        )
        self.stdout.write(f'  - Name: {user.get_full_name() or "N/A"}')
        self.stdout.write(f'  - Email: {user.email}')
        self.stdout.write(f'  - ID: {user.id}')
