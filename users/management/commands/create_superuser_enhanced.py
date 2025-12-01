from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.db import transaction
from django.core.exceptions import ValidationError
from roles.models import Role, UserRole
import getpass
import sys

User = get_user_model()

class Command(BaseCommand):
    help = 'Create a Super Admin user with enhanced UI and proper role assignment'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            help='Username for the superuser',
        )
        parser.add_argument(
            '--email',
            help='Email for the superuser',
        )
        parser.add_argument(
            '--first-name',
            help='First name for the superuser',
        )
        parser.add_argument(
            '--last-name',
            help='Last name for the superuser',
        )
        parser.add_argument(
            '--phone',
            help='Phone number for the superuser',
        )
        parser.add_argument(
            '--database',
            default='default',
            help='Database to use (default: default)',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🚀 Welcome to Super Admin Creation Wizard!'))
        self.stdout.write('=' * 60)
        
        try:
            with transaction.atomic():
                # Get user data
                user_data = self.get_user_data(options)
                
                # Create the user
                user = self.create_user(user_data, options['database'])
                
                # Assign Super Admin role
                self.assign_super_admin_role(user)
                
                # Display success message
                self.display_success_message(user)
                
        except KeyboardInterrupt:
            self.stdout.write(self.style.ERROR('\n❌ Operation cancelled by user.'))
            sys.exit(1)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error: {str(e)}'))
            sys.exit(1)

    def get_user_data(self, options):
        """Get user data from command line options or interactive input"""
        user_data = {}
        
        # Username
        if options['username']:
            user_data['username'] = options['username']
        else:
            while True:
                username = input('👤 Username: ').strip()
                if username:
                    if User.objects.filter(username=username).exists():
                        self.stdout.write(self.style.ERROR('❌ A user with that username already exists.'))
                        continue
                    user_data['username'] = username
                    break
                else:
                    self.stdout.write(self.style.ERROR('❌ Username cannot be blank.'))

        # Email
        if options['email']:
            user_data['email'] = options['email']
        else:
            while True:
                email = input('📧 Email address: ').strip()
                if email:
                    if User.objects.filter(email=email).exists():
                        self.stdout.write(self.style.ERROR('❌ A user with that email already exists.'))
                        continue
                    user_data['email'] = email
                    break
                else:
                    self.stdout.write(self.style.ERROR('❌ Email cannot be blank.'))

        # First name
        if options['first_name']:
            user_data['first_name'] = options['first_name']
        else:
            first_name = input('👨‍💼 First name (optional): ').strip()
            user_data['first_name'] = first_name

        # Last name
        if options['last_name']:
            user_data['last_name'] = options['last_name']
        else:
            last_name = input('👨‍💼 Last name (optional): ').strip()
            user_data['last_name'] = last_name

        # Phone
        if options['phone']:
            user_data['phone'] = options['phone']
        else:
            phone = input('📱 Phone number (optional): ').strip()
            user_data['phone'] = phone

        # Password
        user_data['password'] = self.get_password()

        return user_data

    def get_password(self):
        """Get password with confirmation"""
        while True:
            password = getpass.getpass('🔒 Password: ')
            if not password:
                self.stdout.write(self.style.ERROR('❌ Password cannot be blank.'))
                continue
            
            if len(password) < 8:
                self.stdout.write(self.style.ERROR('❌ Password must be at least 8 characters long.'))
                continue

            password_confirm = getpass.getpass('🔒 Password (again): ')
            if password != password_confirm:
                self.stdout.write(self.style.ERROR('❌ Passwords do not match.'))
                continue

            return password

    def create_user(self, user_data, database):
        """Create the user"""
        self.stdout.write('\n🔄 Creating Super Admin user...')
        
        try:
            user = User.objects.using(database).create_user(
                username=user_data['username'],
                email=user_data['email'],
                password=user_data['password'],
                first_name=user_data.get('first_name', ''),
                last_name=user_data.get('last_name', ''),
                is_staff=True,
                is_superuser=True,
                is_active=True
            )
            
            # Add phone if provided
            if user_data.get('phone'):
                if hasattr(user, 'phone'):
                    user.phone = user_data['phone']
                    user.save()
            
            self.stdout.write(self.style.SUCCESS('✅ User created successfully!'))
            return user
            
        except Exception as e:
            raise CommandError(f'Failed to create user: {str(e)}')

    def assign_super_admin_role(self, user):
        """Assign Super Admin role to the user"""
        self.stdout.write('🔄 Assigning Super Admin role...')
        
        try:
            # Get or create Super Admin role
            super_admin_role, created = Role.objects.get_or_create(
                name='Super Admin',
                defaults={
                    'role_type': 'admin',
                    'description': 'Full system access with all permissions',
                    'is_active': True,
                    'is_default': False,
                    'is_protected': True,
                }
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS('✅ Super Admin role created!'))
            else:
                self.stdout.write(self.style.SUCCESS('✅ Super Admin role found!'))
            
            # Assign role to user
            user_role, created = UserRole.objects.get_or_create(
                user=user,
                role=super_admin_role,
                defaults={
                    'is_primary': True,
                    'is_active': True,
                }
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS('✅ Super Admin role assigned!'))
            else:
                # Update existing role to be primary
                user_role.is_primary = True
                user_role.is_active = True
                user_role.save()
                self.stdout.write(self.style.SUCCESS('✅ Super Admin role updated!'))
                
        except Exception as e:
            raise CommandError(f'Failed to assign Super Admin role: {str(e)}')

    def display_success_message(self, user):
        """Display success message with user details"""
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(self.style.SUCCESS('🎉 Super Admin created successfully!'))
        self.stdout.write('=' * 60)
        
        self.stdout.write(f'👤 Username: {user.username}')
        self.stdout.write(f'📧 Email: {user.email}')
        self.stdout.write(f'👨‍💼 Name: {user.get_full_name() or "N/A"}')
        if hasattr(user, 'phone') and user.phone:
            self.stdout.write(f'📱 Phone: {user.phone}')
        self.stdout.write(f'🔑 Type: Super Admin (Full Access)')
        self.stdout.write(f'✅ Status: Active')
        self.stdout.write(f'🛡️ Permissions: All system permissions')
        
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(self.style.SUCCESS('🚀 You can now login with these credentials!'))
        self.stdout.write('=' * 60)