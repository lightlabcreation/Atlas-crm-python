from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from roles.models import Role, UserRole

User = get_user_model()

class Command(BaseCommand):
    help = 'Comprehensive user management command'

    def add_arguments(self, parser):
        parser.add_argument(
            'action',
            choices=['list', 'activate', 'deactivate', 'assign-role', 'remove-role', 'info'],
            help='Action to perform'
        )
        parser.add_argument(
            '--email',
            type=str,
            help='Email of the user'
        )
        parser.add_argument(
            '--user-id',
            type=int,
            help='ID of the user'
        )
        parser.add_argument(
            '--role',
            type=str,
            help='Role name to assign/remove'
        )
        parser.add_argument(
            '--primary',
            action='store_true',
            help='Make role primary (for assign-role)'
        )
        parser.add_argument(
            '--status',
            choices=['active', 'inactive', 'all'],
            default='all',
            help='Filter by user status (for list action)'
        )

    def handle(self, *args, **options):
        action = options['action']
        
        if action == 'list':
            self.list_users(options)
        elif action == 'activate':
            self.activate_user(options)
        elif action == 'deactivate':
            self.deactivate_user(options)
        elif action == 'assign-role':
            self.assign_role(options)
        elif action == 'remove-role':
            self.remove_role(options)
        elif action == 'info':
            self.show_user_info(options)

    def list_users(self, options):
        """List users with optional filtering"""
        status = options['status']
        
        if status == 'active':
            users = User.objects.filter(is_active=True)
        elif status == 'inactive':
            users = User.objects.filter(is_active=False)
        else:
            users = User.objects.all()
        
        if not users.exists():
            self.stdout.write(
                self.style.WARNING(f'No {status} users found!')
            )
            return

        self.stdout.write(
            self.style.SUCCESS(f'Found {users.count()} {status} users:')
        )
        self.stdout.write('-' * 80)
        
        for user in users:
            user_type = "Superuser" if user.is_superuser else "Regular User"
            status_text = "Active" if user.is_active else "Inactive"
            roles = [ur.role.name for ur in user.user_roles.all()]
            roles_text = ", ".join(roles) if roles else "No roles"
            
            self.stdout.write(f'ID: {user.id}')
            self.stdout.write(f'  Email: {user.email}')
            self.stdout.write(f'  Name: {user.get_full_name() or "N/A"}')
            self.stdout.write(f'  Type: {user_type}')
            self.stdout.write(f'  Status: {status_text}')
            self.stdout.write(f'  Roles: {roles_text}')
            self.stdout.write(f'  Last Login: {user.last_login or "Never"}')
            self.stdout.write('-' * 80)

    def activate_user(self, options):
        """Activate a user"""
        user = self.get_user(options)
        if not user:
            return

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

    def deactivate_user(self, options):
        """Deactivate a user"""
        user = self.get_user(options)
        if not user:
            return

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

    def assign_role(self, options):
        """Assign a role to a user"""
        user = self.get_user(options)
        if not user:
            return

        role_name = options['role']
        if not role_name:
            self.stdout.write(
                self.style.ERROR('Please specify --role for assign-role action!')
            )
            return

        try:
            role = Role.objects.get(name=role_name)
        except Role.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'Role "{role_name}" not found!')
            )
            return

        is_primary = options['primary']

        # Check if user already has this role
        existing_user_role = UserRole.objects.filter(user=user, role=role).first()
        if existing_user_role:
            existing_user_role.is_primary = is_primary
            existing_user_role.is_active = True
            existing_user_role.save()
            self.stdout.write(
                self.style.SUCCESS(f'Updated role "{role_name}" for user "{user.email}" (Primary: {is_primary})')
            )
        else:
            # If this is a primary role, remove primary from other roles
            if is_primary:
                UserRole.objects.filter(user=user, is_primary=True).update(is_primary=False)

            UserRole.objects.create(
                user=user,
                role=role,
                is_primary=is_primary,
                is_active=True
            )
            self.stdout.write(
                self.style.SUCCESS(f'Assigned role "{role_name}" to user "{user.email}" (Primary: {is_primary})')
            )

    def remove_role(self, options):
        """Remove a role from a user"""
        user = self.get_user(options)
        if not user:
            return

        role_name = options['role']
        if not role_name:
            self.stdout.write(
                self.style.ERROR('Please specify --role for remove-role action!')
            )
            return

        try:
            role = Role.objects.get(name=role_name)
        except Role.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'Role "{role_name}" not found!')
            )
            return

        try:
            user_role = UserRole.objects.get(user=user, role=role)
            user_role.delete()
            self.stdout.write(
                self.style.SUCCESS(f'Removed role "{role_name}" from user "{user.email}"')
            )
        except UserRole.DoesNotExist:
            self.stdout.write(
                self.style.WARNING(f'User "{user.email}" does not have role "{role_name}"!')
            )

    def show_user_info(self, options):
        """Show detailed information about a user"""
        user = self.get_user(options)
        if not user:
            return

        self.stdout.write(
            self.style.SUCCESS(f'User Information for: {user.email}')
        )
        self.stdout.write('=' * 50)
        self.stdout.write(f'ID: {user.id}')
        self.stdout.write(f'Email: {user.email}')
        self.stdout.write(f'First Name: {user.first_name or "N/A"}')
        self.stdout.write(f'Last Name: {user.last_name or "N/A"}')
        self.stdout.write(f'Full Name: {user.get_full_name() or "N/A"}')
        self.stdout.write(f'Is Active: {user.is_active}')
        self.stdout.write(f'Is Superuser: {user.is_superuser}')
        self.stdout.write(f'Is Staff: {user.is_staff}')
        self.stdout.write(f'Date Joined: {user.date_joined}')
        self.stdout.write(f'Last Login: {user.last_login or "Never"}')
        
        # Show roles
        user_roles = user.user_roles.all()
        if user_roles.exists():
            self.stdout.write('\nRoles:')
            for ur in user_roles:
                primary_text = " (Primary)" if ur.is_primary else ""
                active_text = " (Active)" if ur.is_active else " (Inactive)"
                self.stdout.write(f'  - {ur.role.name}{primary_text}{active_text}')
        else:
            self.stdout.write('\nRoles: None')

    def get_user(self, options):
        """Get user by email or ID"""
        email = options.get('email')
        user_id = options.get('user_id')

        if not email and not user_id:
            self.stdout.write(
                self.style.ERROR('Please specify --email or --user-id!')
            )
            return None

        try:
            if email:
                return User.objects.get(email=email)
            else:
                return User.objects.get(id=user_id)
        except User.DoesNotExist:
            identifier = email or user_id
            self.stdout.write(
                self.style.ERROR(f'User "{identifier}" not found!')
            )
            return None
