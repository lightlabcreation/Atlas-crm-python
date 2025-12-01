import os
import xml.etree.ElementTree as ET
from django.conf import settings

AREAS_DIR = os.path.join(settings.BASE_DIR, 'Areas Docs')

# Mapping of Arabic city names to English names with codes
CITY_MAPPING = {
    'ابوظبي': ('Abu Dhabi', 'AD'),
    'دبي': ('Dubai', 'DXB'),
    'الشارقة': ('Sharjah', 'SHJ'),
    'عجمان': ('Ajman', 'AJM'),
    'راس الخيمة': ('Ras Al Khaimah', 'RAK'),
    'الفجيرة': ('Fujairah', 'FJR'),
    'ام القيوين': ('Umm Al Quwain', 'UAQ'),
    'العين': ('Al Ain', 'AIN'),
    'المناطق النائية': ('Remote Areas', 'REM'),
}

def get_cities_list():
    """Get list of cities with English names and codes."""
    cities = []
    if os.path.exists(AREAS_DIR):
        for filename in os.listdir(AREAS_DIR):
            if filename.endswith('.xml') and filename.startswith('vertopal.com_'):
                city_name_ar = filename.replace('vertopal.com_', '').replace('.xml', '')
                # Get English name and code from mapping
                if city_name_ar in CITY_MAPPING:
                    city_name_en, city_code = CITY_MAPPING[city_name_ar]
                    # Format: "Dubai (DXB)" for display, but store Arabic name as value
                    display_name = f"{city_name_en} ({city_code})"
                    cities.append((city_name_ar, display_name))
                else:
                    # Fallback to Arabic name if not in mapping
                    cities.append((city_name_ar, city_name_ar))
    return sorted(cities, key=lambda x: x[1])  # Sort by display name

def get_states_for_city(city_name):
    """Get list of areas/states for a city with city code included."""
    states = []
    filename = f'vertopal.com_{city_name}.xml'
    filepath = os.path.join(AREAS_DIR, filename)
    
    # Get city code from mapping
    city_code = ''
    if city_name in CITY_MAPPING:
        _, city_code = CITY_MAPPING[city_name]
    
    if os.path.exists(filepath):
        try:
            tree = ET.parse(filepath)
            root = tree.getroot()
            
            namespace = {'text': 'urn:oasis:names:tc:opendocument:xmlns:text:1.0'}
            
            for text_p in root.findall('.//text:p', namespace):
                text_span = text_p.find('.//text:span', namespace)
                if text_span is not None:
                    continue
                
                text_parts = []
                if text_p.text:
                    text_parts.append(text_p.text.strip())
                
                for child in text_p:
                    if child.text:
                        text_parts.append(child.text.strip())
                
                text_content = ' '.join(text_parts).strip().replace('\n', ' ').replace('\r', '').replace('  ', ' ')
                
                if text_content:
                    state_values = [s[0] for s in states]
                    if text_content not in state_values:
                        # Include city code in the display text: "Area Name (CITY_CODE)"
                        display_text = f"{text_content} ({city_code})" if city_code else text_content
                        states.append((text_content, display_text))
        except Exception as e:
            print(f"Error parsing XML file {filename}: {e}")
    
    return sorted(states)

