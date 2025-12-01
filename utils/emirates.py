# utils/emirates.py
# UAE Emirates and Regions data

EMIRATES_CHOICES = [
    ('abu_dhabi', 'أبو ظبي - Abu Dhabi'),
    ('dubai', 'دبي - Dubai'),
    ('sharjah', 'الشارقة - Sharjah'),
    ('ajman', 'عجمان - Ajman'),
    ('ras_al_khaimah', 'رأس الخيمة - Ras Al Khaimah'),
    ('fujairah', 'الفجيرة - Fujairah'),
    ('umm_al_quwain', 'أم القيوين - Umm Al Quwain'),
]

EMIRATE_REGIONS = {
    'abu_dhabi': [
        ('abu_dhabi_city', 'مدينة أبو ظبي - Abu Dhabi City'),
        ('al_ain', 'العين - Al Ain'),
        ('al_dhafra', 'الظفرة - Al Dhafra'),
        ('western_region', 'المنطقة الغربية - Western Region'),
    ],
    'dubai': [
        ('dubai_city', 'مدينة دبي - Dubai City'),
        ('jebel_ali', 'جبل علي - Jebel Ali'),
        ('hatta', 'حتا - Hatta'),
        ('al_awir', 'العوير - Al Awir'),
    ],
    'sharjah': [
        ('sharjah_city', 'مدينة الشارقة - Sharjah City'),
        ('al_dhaid', 'الذيد - Al Dhaid'),
        ('kalba', 'كلباء - Kalba'),
        ('khor_fakkan', 'خورفكان - Khor Fakkan'),
    ],
    'ajman': [
        ('ajman_city', 'مدينة عجمان - Ajman City'),
        ('masfout', 'مسفوت - Masfout'),
        ('manama', 'المنامة - Manama'),
    ],
    'ras_al_khaimah': [
        ('ras_al_khaimah_city', 'مدينة رأس الخيمة - Ras Al Khaimah City'),
        ('al_hamra', 'الحمرا - Al Hamra'),
        ('jebel_jais', 'جبل جيس - Jebel Jais'),
    ],
    'fujairah': [
        ('fujairah_city', 'مدينة الفجيرة - Fujairah City'),
        ('dibba', 'دبا - Dibba'),
        ('masafi', 'مصفح - Masafi'),
    ],
    'umm_al_quwain': [
        ('umm_al_quwain_city', 'مدينة أم القيوين - Umm Al Quwain City'),
        ('falaj_al_mualla', 'فلج المعلا - Falaj Al Mualla'),
    ],
}

def get_emirate_regions(emirate_code):
    """Get regions for a specific emirate."""
    return EMIRATE_REGIONS.get(emirate_code, [])

def get_all_regions():
    """Get all regions from all emirates."""
    all_regions = []
    for emirate_code, regions in EMIRATE_REGIONS.items():
        for region_code, region_name in regions:
            all_regions.append((region_code, region_name))
    return all_regions
