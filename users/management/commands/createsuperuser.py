from django.core.management.base import BaseCommand
from django.core.management import call_command

class Command(BaseCommand):
    help = 'Create a superuser with enhanced UI (alias for create_superuser_enhanced)'

    def add_arguments(self, parser):
        # Add all the same arguments as the enhanced command
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
            '--noinput',
            '--no-input',
            action='store_true',
            help='Do not prompt for input',
        )
        parser.add_argument(
            '--database',
            help='Specifies the database to use. Default is "default".',
        )
        parser.add_argument(
            '--advanced',
            action='store_true',
            help='Use the advanced version with colors and password strength',
        )

    def handle(self, *args, **options):
        # Determine which command to call
        if options.get('advanced'):
            command_name = 'create_superuser_advanced'
        else:
            command_name = 'create_superuser_enhanced'
        
        # Remove the --advanced flag from options
        if 'advanced' in options:
            del options['advanced']
        
        # Call the appropriate command
        call_command(command_name, **options)
