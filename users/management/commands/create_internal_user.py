"""
Management command to create internal users with temporary passwords.

Usage:
    python manage.py create_internal_user <email> <full_name> <role>

Example:
    python manage.py create_internal_user admin@atlas.com "John Admin" "admin"
    python manage.py create_internal_user manager@atlas.com "Jane Manager" "delivery_manager"
"""
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from roles.models import Role, UserRole
import random
import string

User = get_user_model()


class Command(BaseCommand):
    help = 'Create an internal user with a temporary password that must be changed on first login'

    def add_arguments(self, parser):
        parser.add_argument('email', type=str, help='Email address for the user')
        parser.add_argument('full_name', type=str, help='Full name of the user')
        parser.add_argument('role', type=str, help='Role slug (e.g., admin, delivery_manager, staff)')
        parser.add_argument(
            '--phone',
            type=str,
            default='+00000000000',
            help='Phone number (optional, defaults to placeholder)'
        )

    def generate_temp_password(self, length=12):
        """Generate a secure temporary password."""
        characters = string.ascii_letters + string.digits + "!@#$%&*"
        password = ''.join(random.choice(characters) for i in range(length))
        # Ensure it meets requirements
        if not any(c.isupper() for c in password):
            password = password[0].upper() + password[1:]
        if not any(c.islower() for c in password):
            password = password[:-1] + random.choice(string.ascii_lowercase)
        if not any(c.isdigit() for c in password):
            password = password[:-1] + random.choice(string.digits)
        return password

    def handle(self, *args, **options):
        email = options['email']
        full_name = options['full_name']
        role_slug = options['role']
        phone_number = options['phone']

        # Check if user already exists
        if User.objects.filter(email=email).exists():
            raise CommandError(f'User with email "{email}" already exists')

        # Check if role exists (by name or ID)
        try:
            # Try to get by ID first
            if role_slug.isdigit():
                role = Role.objects.get(id=int(role_slug))
            else:
                # Try case-insensitive name match
                role = Role.objects.get(name__iexact=role_slug)
        except Role.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Role "{role_slug}" does not exist'))
            self.stdout.write(self.style.WARNING('\nAvailable roles:'))
            for r in Role.objects.all():
                self.stdout.write(f'  - {r.id}: {r.name} ({r.role_type})')
            raise CommandError('Invalid role specified')

        # Generate temporary password
        temp_password = self.generate_temp_password()

        # Create user
        user = User.objects.create_user(
            email=email,
            full_name=full_name,
            phone_number=phone_number,
            password=temp_password,
            approval_status='approved',  # Internal users are pre-approved
            email_verified=True,  # Internal users don't need email verification
            is_active=True,
            is_staff=True,  # Internal users are staff
            password_change_required=True  # Force password change on first login
        )

        # Assign role
        UserRole.objects.create(user=user, role=role)

        # Display success message
        self.stdout.write(self.style.SUCCESS('\n' + '=' * 70))
        self.stdout.write(self.style.SUCCESS('Internal User Created Successfully'))
        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write(f'\nEmail:              {email}')
        self.stdout.write(f'Full Name:          {full_name}')
        self.stdout.write(f'Role:               {role.name} (ID: {role.id})')
        self.stdout.write(f'Phone:              {phone_number}')
        self.stdout.write(self.style.WARNING(f'\nTemporary Password: {temp_password}'))
        self.stdout.write(self.style.WARNING('\n⚠️  IMPORTANT: Save this password! It cannot be retrieved later.'))
        self.stdout.write(self.style.WARNING('⚠️  User will be forced to change password on first login.'))
        self.stdout.write('\n' + '=' * 70 + '\n')
