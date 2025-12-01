from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from roles.models import Role, UserRole

User = get_user_model()

class Command(BaseCommand):
    help = 'Assign stock keeper role to users'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user-id',
            type=int,
            help='Specific user ID to assign role to'
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Assign to all users'
        )

    def handle(self, *args, **options):
        # Get the stock keeper role
        stock_keeper_role, created = Role.objects.get_or_create(
            name='Stock Keeper',
            defaults={
                'description': 'Stock keeper role for warehouse operations',
                'role_type': 'custom'
            }
        )

        if options['user_id']:
            # Assign to specific user
            try:
                user = User.objects.get(id=options['user_id'])
                self.assign_role_to_user(user, stock_keeper_role)
            except User.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'User with ID {options["user_id"]} does not exist')
                )
        elif options['all']:
            # Assign to all users
            users = User.objects.all()
            for user in users:
                self.assign_role_to_user(user, stock_keeper_role)
        else:
            # Assign to first user (for testing)
            user = User.objects.first()
            if user:
                self.assign_role_to_user(user, stock_keeper_role)
            else:
                self.stdout.write(
                    self.style.ERROR('No users found in the system')
                )

    def assign_role_to_user(self, user, role):
        # Check if user already has this role
        existing_role = UserRole.objects.filter(user=user, role=role).first()
        
        if existing_role:
            self.stdout.write(
                self.style.WARNING(f'User {user.username} already has Stock Keeper role')
            )
        else:
            # Create user role
            user_role, created = UserRole.objects.get_or_create(
                user=user,
                role=role,
                defaults={
                    'is_primary': False  # Don't make it primary by default
                }
            )
            self.stdout.write(
                self.style.SUCCESS(f'Successfully assigned Stock Keeper role to {user.username}')
            ) 