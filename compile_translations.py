#!/usr/bin/env python
"""
Script to compile Django translation files (.po to .mo) without requiring gettext tools.
This uses Python's built-in libraries to compile .po files to .mo format.
"""
import os
import sys
from pathlib import Path

try:
    from babel.messages import catalog
    from babel.messages import mofile
    HAS_BABEL = True
except ImportError:
    HAS_BABEL = False
    print("Warning: Babel not found. Trying alternative method...")

def compile_po_to_mo_using_babel(po_file, mo_file):
    """Compile .po to .mo using Babel"""
    try:
        with open(po_file, 'rb') as f:
            cat = catalog.read_po(f)
        
        with open(mo_file, 'wb') as f:
            mofile.write_mo(f, cat)
        return True
    except Exception as e:
        print(f"Error compiling {po_file}: {e}")
        return False

def compile_po_to_mo_manual(po_file, mo_file):
    """Manual compilation using polib if available"""
    try:
        import polib
        po = polib.pofile(po_file)
        po.save_as_mofile(mo_file)
        return True
    except ImportError:
        print("polib not installed. Install it with: pip install polib")
        return False
    except Exception as e:
        print(f"Error compiling {po_file}: {e}")
        return False

def find_po_files(base_dir):
    """Find all .po files in locale directories"""
    po_files = []
    locale_dir = Path(base_dir) / 'locale'
    
    if not locale_dir.exists():
        print(f"Locale directory not found: {locale_dir}")
        return po_files
    
    for po_file in locale_dir.rglob('*.po'):
        po_files.append(po_file)
    
    return po_files

def main():
    # Get project base directory
    base_dir = Path(__file__).parent
    
    # Find all .po files
    po_files = find_po_files(base_dir)
    
    if not po_files:
        print("No .po files found in locale directory")
        return
    
    print(f"Found {len(po_files)} .po file(s)")
    
    compiled = 0
    failed = 0
    
    for po_file in po_files:
        mo_file = po_file.with_suffix('.mo')
        print(f"Compiling {po_file.name}...")
        
        success = False
        if HAS_BABEL:
            success = compile_po_to_mo_using_babel(po_file, mo_file)
        else:
            success = compile_po_to_mo_manual(po_file, mo_file)
        
        if success:
            print(f"  ✓ Created {mo_file.name}")
            compiled += 1
        else:
            print(f"  ✗ Failed to compile {po_file.name}")
            failed += 1
    
    print(f"\nSummary: {compiled} compiled, {failed} failed")
    
    if failed > 0 and not HAS_BABEL:
        print("\nTo fix compilation issues, install Babel:")
        print("  pip install Babel")
        print("\nOr install polib:")
        print("  pip install polib")

if __name__ == '__main__':
    main()

