"""
Database Export Script for Railway Deployment
यह script आपके local database को export करेगा Railway पर import करने के लिए
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
import json
from datetime import datetime

def export_database():
    """Export database data to JSON file"""
    print("=" * 60)
    print("Database Export Script for Railway")
    print("=" * 60)
    
    # Get database info
    db_config = settings.DATABASES['default']
    print(f"\nDatabase Engine: {db_config.get('ENGINE', 'N/A')}")
    print(f"Database Name: {db_config.get('NAME', 'N/A')}")
    
    # Create export directory
    export_dir = BASE_DIR / 'database_exports'
    export_dir.mkdir(exist_ok=True)
    
    # Generate filename with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    export_file = export_dir / f'atlas_crm_export_{timestamp}.json'
    
    print(f"\nExporting database to: {export_file}")
    print("This may take a few minutes...\n")
    
    try:
        # Export all data
        with open(export_file, 'w', encoding='utf-8') as f:
            call_command('dumpdata', 
                        exclude=['contenttypes', 'auth.Permission', 'sessions'],
                        natural_foreign=True,
                        natural_primary=True,
                        indent=2,
                        stdout=f)
        
        file_size = export_file.stat().st_size / (1024 * 1024)  # Size in MB
        print(f"✅ Export successful!")
        print(f"📁 File: {export_file}")
        print(f"📊 Size: {file_size:.2f} MB")
        print(f"\nअब आप इस file को Railway पर import कर सकते हैं:")
        print(f"  python import_database.py {export_file.name}")
        
        return str(export_file)
        
    except Exception as e:
        print(f"❌ Error during export: {e}")
        return None

if __name__ == '__main__':
    export_database()

