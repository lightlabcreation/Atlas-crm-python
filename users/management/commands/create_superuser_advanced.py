from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.db import transaction
from django.core.exceptions import ValidationError
from roles.models import Role, UserRole
import getpass
import sys
import re

User = get_user_model()

class Command(BaseCommand):
    help = 'Create a Super Admin user with advanced UI, colors, and password strength checking'

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

    def __init__(self):
        super().__init__()
        self.colors = self.init_colors()

    def init_colors(self):
        """Initialize color codes if terminal supports them"""
        try:
            # Check if colors are supported
            if sys.stdout.isatty() and 'NO_COLOR' not in os.environ and os.environ.get('TERM') != 'dumb':
                return {
                    'red': '\033[91m',
                    'green': '\033[92m',
                    'yellow': '\033[93m',
                    'blue': '\033[94m',
                    'magenta': '\033[95m',
                    'cyan': '\033[96m',
                    'white': '\033[97m',
                    'bold': '\033[1m',
                    'underline': '\033[4m',
                    'end': '\033[0m',
                }
        except:
            pass
        
        # Return empty colors if not supported
        return {key: '' for key in ['red', 'green', 'yellow', 'blue', 'magenta', 'cyan', 'white', 'bold', 'underline', 'end']}

    def colorize(self, text, color):
        """Apply color to text"""
        return f"{self.colors.get(color, '')}{text}{self.colors.get('end', '')}"

    def print_header(self):
        """Print beautiful header"""
        header = """
╔══════════════════════════════════════════════════════════════╗
║                    🚀 SUPER ADMIN WIZARD 🚀                  ║
║                                                              ║
║  Create a Super Admin with full system permissions          ║
║  and enhanced security features                              ║
╚══════════════════════════════════════════════════════════════╝
        """
        print(self.colorize(header, 'cyan'))

    def print_section(self, title, color='blue'):
        """Print a section header"""
        print(f"\n{self.colorize('─' * 60, color)}")
        print(f"{self.colorize(f'  {title}', color)}")
        print(f"{self.colorize('─' * 60, color)}")

    def print_success(self, message):
        """Print success message"""
        print(f"{self.colorize('✅', 'green')} {self.colorize(message, 'green')}")

    def print_error(self, message):
        """Print error message"""
        print(f"{self.colorize('❌', 'red')} {self.colorize(message, 'red')}")

    def print_warning(self, message):
        """Print warning message"""
        print(f"{self.colorize('⚠️', 'yellow')} {self.colorize(message, 'yellow')}")

    def print_info(self, message):
        """Print info message"""
        print(f"{self.colorize('ℹ️', 'blue')} {self.colorize(message, 'blue')}")

    def check_password_strength(self, password):
        """Check password strength and return score and feedback"""
        score = 0
        feedback = []
        
        # Length check
        if len(password) >= 8:
            score += 1
        else:
            feedback.append("At least 8 characters")
        
        # Uppercase check
        if re.search(r'[A-Z]', password):
            score += 1
        else:
            feedback.append("At least one uppercase letter")
        
        # Lowercase check
        if re.search(r'[a-z]', password):
            score += 1
        else:
            feedback.append("At least one lowercase letter")
        
        # Number check
        if re.search(r'\d', password):
            score += 1
        else:
            feedback.append("At least one number")
        
        # Special character check
        if re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            score += 1
        else:
            feedback.append("At least one special character")
        
        return score, feedback

    def display_password_strength(self, password):
        """Display password strength indicator"""
        score, feedback = self.check_password_strength(password)
        
        strength_levels = [
            (0, 1, "Very Weak", "red"),
            (1, 2, "Weak", "red"),
            (2, 3, "Fair", "yellow"),
            (3, 4, "Good", "blue"),
            (4, 5, "Strong", "green"),
        ]
        
        strength_text = "Very Weak"
        strength_color = "red"
        
        for min_score, max_score, level, color in strength_levels:
            if min_score <= score < max_score:
                strength_text = level
                strength_color = color
                break
        
        # Create strength bar
        bar_length = 20
        filled_length = int((score / 5) * bar_length)
        bar = "█" * filled_length + "░" * (bar_length - filled_length)
        
        print(f"\n{self.colorize('Password Strength:', 'bold')} {self.colorize(strength_text, strength_color)}")
        print(f"{self.colorize(bar, strength_color)} ({score}/5)")
        
        if feedback:
            print(f"{self.colorize('Suggestions:', 'yellow')}")
            for suggestion in feedback:
                print(f"  • {suggestion}")

    def handle(self, *args, **options):
        import os
        
        self.print_header()
        
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
            self.print_error('Operation cancelled by user.')
            sys.exit(1)
        except Exception as e:
            self.print_error(f'Error: {str(e)}')
            sys.exit(1)

    def get_user_data(self, options):
        """Get user data from command line options or interactive input"""
        user_data = {}
        
        self.print_section("👤 USER INFORMATION", "blue")
        
        # Username
        if options['username']:
            user_data['username'] = options['username']
            self.print_info(f"Username: {user_data['username']}")
        else:
            while True:
                username = input(f"{self.colorize('👤 Username', 'bold')}: ").strip()
                if username:
                    if User.objects.filter(username=username).exists():
                        self.print_error('A user with that username already exists.')
                        continue
                    user_data['username'] = username
                    break
                else:
                    self.print_error('Username cannot be blank.')

        # Email
        if options['email']:
            user_data['email'] = options['email']
            self.print_info(f"Email: {user_data['email']}")
        else:
            while True:
                email = input(f"{self.colorize('📧 Email address', 'bold')}: ").strip()
                if email:
                    if User.objects.filter(email=email).exists():
                        self.print_error('A user with that email already exists.')
                        continue
                    user_data['email'] = email
                    break
                else:
                    self.print_error('Email cannot be blank.')

        # First name
        if options['first_name']:
            user_data['first_name'] = options['first_name']
            self.print_info(f"First Name: {user_data['first_name']}")
        else:
            first_name = input(f"{self.colorize('👨‍💼 First name', 'bold')} (optional): ").strip()
            user_data['first_name'] = first_name

        # Last name
        if options['last_name']:
            user_data['last_name'] = options['last_name']
            self.print_info(f"Last Name: {user_data['last_name']}")
        else:
            last_name = input(f"{self.colorize('👨‍💼 Last name', 'bold')} (optional): ").strip()
            user_data['last_name'] = last_name

        # Phone
        if options['phone']:
            user_data['phone'] = options['phone']
            self.print_info(f"Phone: {user_data['phone']}")
        else:
            phone = input(f"{self.colorize('📱 Phone number', 'bold')} (optional): ").strip()
            user_data['phone'] = phone

        # Password
        self.print_section("🔒 SECURITY SETTINGS", "magenta")
        user_data['password'] = self.get_password()

        return user_data

    def get_password(self):
        """Get password with confirmation and strength checking"""
        while True:
            password = getpass.getpass(f"{self.colorize('🔒 Password', 'bold')}: ")
            if not password:
                self.print_error('Password cannot be blank.')
                continue
            
            if len(password) < 8:
                self.print_error('Password must be at least 8 characters long.')
                continue

            # Display password strength
            self.display_password_strength(password)
            
            # Ask for confirmation
            password_confirm = getpass.getpass(f"{self.colorize('🔒 Password (again)', 'bold')}: ")
            if password != password_confirm:
                self.print_error('Passwords do not match.')
                continue

            # Ask if user wants to continue with weak password
            score, _ = self.check_password_strength(password)
            if score < 3:
                continue_anyway = input(f"{self.colorize('⚠️  Password is weak. Continue anyway? (y/N)', 'yellow')}: ").strip().lower()
                if continue_anyway not in ['y', 'yes']:
                    continue

            return password

    def create_user(self, user_data, database):
        """Create the user"""
        self.print_section("🔄 CREATING USER", "blue")
        
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
            
            self.print_success('User created successfully!')
            return user
            
        except Exception as e:
            raise CommandError(f'Failed to create user: {str(e)}')

    def assign_super_admin_role(self, user):
        """Assign Super Admin role to the user"""
        self.print_section("🛡️ ASSIGNING PERMISSIONS", "green")
        
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
                self.print_success('Super Admin role created!')
            else:
                self.print_info('Super Admin role found!')
            
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
                self.print_success('Super Admin role assigned!')
            else:
                # Update existing role to be primary
                user_role.is_primary = True
                user_role.is_active = True
                user_role.save()
                self.print_success('Super Admin role updated!')
                
        except Exception as e:
            raise CommandError(f'Failed to assign Super Admin role: {str(e)}')

    def display_success_message(self, user):
        """Display success message with user details"""
        self.print_section("🎉 SUCCESS!", "green")
        
        success_box = f"""
╔══════════════════════════════════════════════════════════════╗
║                    🎉 SUPER ADMIN CREATED! 🎉                ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  👤 Username: {user.username:<47} ║
║  📧 Email: {user.email:<49} ║
║  👨‍💼 Name: {(user.get_full_name() or "N/A"):<48} ║
║  📱 Phone: {(getattr(user, 'phone', '') or 'N/A'):<48} ║
║  🔑 Type: Super Admin (Full Access)                         ║
║  ✅ Status: Active                                          ║
║  🛡️ Permissions: All system permissions                     ║
║                                                              ║
║  🚀 You can now login with these credentials!               ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
        """
        
        print(self.colorize(success_box, 'green'))