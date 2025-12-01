"""
Django management command to compile .po files to .mo files using babel.
This is a workaround for Windows when gettext tools are not installed.
"""
from django.core.management.base import BaseCommand
from django.core.management.utils import find_command
from pathlib import Path
from babel.messages import pofile, mofile
import os


class Command(BaseCommand):
    help = 'Compiles .po files to .mo files for use with builtin gettext support (using babel)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--locale', '-l',
            dest='locale',
            action='append',
            help='Locale(s) to process (e.g. de_AT). Default is to process all.',
        )
        parser.add_argument(
            '--exclude', '-x',
            dest='exclude',
            action='append',
            default=[],
            help='Locales to exclude. Default is none.',
        )
        parser.add_argument(
            '--use-fuzzy', '-f',
            dest='fuzzy',
            action='store_true',
            help='Use fuzzy translations.',
        )

    def handle(self, *args, **options):
        locale = options.get('locale')
        exclude = options.get('exclude')
        fuzzy = options.get('fuzzy', False)
        
        # Use babel-based compilation directly
        self.stdout.write('Using babel-based compilation (gettext tools not found)...')
        
        base_dir = Path(__file__).resolve().parent.parent.parent.parent
        locale_dir = base_dir / 'locale'
        
        if not locale_dir.exists():
            self.stdout.write(self.style.ERROR(f'Locale directory not found: {locale_dir}'))
            return
        
        compiled_count = 0
        
        # Find all .po files
        for po_file in locale_dir.rglob('*.po'):
            # Check locale filter
            po_locale = po_file.parent.parent.name
            if locale and po_locale not in locale:
                continue
            if exclude and po_locale in exclude:
                continue
            
            mo_file = po_file.with_suffix('.mo')
            
            try:
                # Read the .po file
                with open(po_file, 'rb') as f:
                    catalog_obj = pofile.read_po(f, locale=po_locale)
                
                # Filter out fuzzy translations if not requested
                if not fuzzy:
                    catalog_obj.fuzzy = False
                
                # Write the .mo file
                with open(mo_file, 'wb') as f:
                    mofile.write_mo(f, catalog_obj)
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Compiled: {po_file.relative_to(base_dir)} -> {mo_file.relative_to(base_dir)}'
                    )
                )
                compiled_count += 1
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error compiling {po_file}: {e}')
                )
        
        if compiled_count > 0:
            self.stdout.write(
                self.style.SUCCESS(f'\nSuccessfully compiled {compiled_count} message file(s).')
            )
        else:
            self.stdout.write('No message files found to compile.')

