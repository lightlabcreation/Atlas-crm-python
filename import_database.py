"""
Database Import Script for Railway
यह script आपके exported database data को Railway पर import करेगा
"""

import os
import sys
import django
from pathlib import Path

# Setup Django
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_fulfillment.settings')
django.setup()

from django.core.management import call_command
from django.conf import settings

def import_database(export_file=None):
    """Import database data from JSON file"""
    print("=" * 60)
    print("Database Import Script for Railway")
    print("=" * 60)
    
    # Get database info
    db_config = settings.DATABASES['default']
    print(f"\nDatabase Engine: {db_config.get('ENGINE', 'N/A')}")
    print(f"Database Name: {db_config.get('NAME', 'N/A')}")
    
    # Check export directory
    export_dir = BASE_DIR / 'database_exports'
    
    if not export_file:
        # List available exports
        if not export_dir.exists():
            print(f"\n❌ Export directory not found: {export_dir}")
            print("Please run export_database.py first to create an export file.")
            return
        
        export_files = list(export_dir.glob('atlas_crm_export_*.json'))
        
        if not export_files:
            print(f"\n❌ No export files found in {export_dir}")
            print("Please run export_database.py first to create an export file.")
            return
        
        # Show available files
        print(f"\nAvailable export files:")
        for i, file in enumerate(export_files, 1):
            file_size = file.stat().st_size / (1024 * 1024)  # Size in MB
            print(f"  {i}. {file.name} ({file_size:.2f} MB)")
        
        # Ask user to select
        try:
            choice = int(input(f"\nSelect file number (1-{len(export_files)}): "))
            if 1 <= choice <= len(export_files):
                export_file = export_files[choice - 1]
            else:
                print("❌ Invalid choice")
                return
        except (ValueError, KeyboardInterrupt):
            print("\n❌ Import cancelled")
            return
    else:
        # Use provided file path
        export_file = Path(export_file)
        if not export_file.is_absolute():
            export_file = export_dir / export_file
        
        if not export_file.exists():
            print(f"❌ File not found: {export_file}")
            return
    
    print(f"\n📁 Importing from: {export_file}")
    print("⚠️  WARNING: This will overwrite existing data!")
    
    confirm = input("Are you sure you want to continue? (yes/no): ")
    if confirm.lower() != 'yes':
        print("❌ Import cancelled")
        return
    
    print("\nImporting data... This may take a few minutes...\n")
    
    try:
        # Import data
        call_command('loaddata', str(export_file), verbosity=2)
        
        print(f"\n✅ Import successful!")
        print(f"📊 Data imported from: {export_file.name}")
        print("\nअब आप Railway पर database data use कर सकते हैं!")
        
    except Exception as e:
        print(f"❌ Error during import: {e}")
        print("\nCommon issues:")
        print("  1. Database connection error - check DATABASE_URL")
        print("  2. Migration not run - run: python manage.py migrate")
        print("  3. File format error - ensure it's a valid JSON export")

if __name__ == '__main__':
    import sys
    export_file = sys.argv[1] if len(sys.argv) > 1 else None
    import_database(export_file)

