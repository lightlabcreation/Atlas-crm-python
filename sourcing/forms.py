from django import forms
from .models import SourcingRequest


class ComprehensiveSourcingForm(forms.Form):
    """Comprehensive sourcing form with all required and optional fields."""
    
    # Product Name (User writes the product name)
    product_name = forms.CharField(
        max_length=255,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'shadow-sm focus:ring-yellow-500 focus:border-yellow-500 block w-full sm:text-sm border-gray-300 rounded-md',
            'placeholder': 'Enter product name',
            'required': 'required'
        }),
        help_text='Enter the name of the product you want to source'
    )
    
    # Additional Product Info
    additional_product_info = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'shadow-sm focus:ring-yellow-500 focus:border-yellow-500 block w-full sm:text-sm border-gray-300 rounded-md',
            'placeholder': 'Additional product specifications (optional)',
        }),
        help_text='Additional product specifications or requirements (optional)'
    )
    
    carton_quantity = forms.IntegerField(
        min_value=1,
        max_value=10000,
        widget=forms.NumberInput(attrs={
            'class': 'shadow-sm focus:ring-yellow-500 focus:border-yellow-500 block w-full sm:text-sm border-gray-300 rounded-md',
            'placeholder': 'Enter quantity in cartons',
            'required': 'required'
        }),
        help_text='Specify quantity in cartons/boxes. Standard carton sizes vary by product.'
    )
    
    source_country = forms.ChoiceField(
        choices=[
            ('', 'Select source country'),
            ('UAE', 'UAE'),
            ('China', 'China'),
            ('USA', 'USA'),
            ('Turkey', 'Turkey'),
            ('Korea', 'Korea'),
            ('Japan', 'Japan'),
        ],
        widget=forms.Select(attrs={
            'class': 'shadow-sm focus:ring-yellow-500 focus:border-yellow-500 block w-full sm:text-sm border-gray-300 rounded-md',
            'required': 'required',
            'id': 'source_country_select'
        }),
        help_text='Select the country where you want the product to be sourced from'
    )
    
    destination_country = forms.ChoiceField(
        choices=[
            ('', 'Select destination country'),
            # Africa
            ('Algeria', 'Algeria (Algiers)'),
            ('Angola', 'Angola (Luanda)'),
            ('Benin', 'Benin (Porto-Novo)'),
            ('Botswana', 'Botswana (Gaborone)'),
            ('Burkina Faso', 'Burkina Faso (Ouagadougou)'),
            ('Burundi', 'Burundi (Gitega)'),
            ('Cabo Verde', 'Cabo Verde (Cape Verde) (Praia)'),
            ('Cameroon', 'Cameroon (Yaoundé)'),
            ('Central African Republic', 'Central African Republic (Bangui)'),
            ('Chad', 'Chad (N\'Djamena)'),
            ('Comoros', 'Comoros (Moroni)'),
            ('Democratic Republic of the Congo', 'Democratic Republic of the Congo (DRC) (Kinshasa)'),
            ('Republic of the Congo', 'Republic of the Congo (Brazzaville)'),
            ('Djibouti', 'Djibouti (Djibouti)'),
            ('Egypt', 'Egypt (Cairo)'),
            ('Equatorial Guinea', 'Equatorial Guinea (Malabo)'),
            ('Eritrea', 'Eritrea (Asmara)'),
            ('Eswatini', 'Eswatini (Swaziland) (Mbabane)'),
            ('Ethiopia', 'Ethiopia (Addis Ababa)'),
            ('Gabon', 'Gabon (Libreville)'),
            ('Gambia', 'Gambia (Banjul)'),
            ('Ghana', 'Ghana (Accra)'),
            ('Guinea', 'Guinea (Conakry)'),
            ('Guinea-Bissau', 'Guinea-Bissau (Bissau)'),
            ('Ivory Coast', 'Ivory Coast (Côte d\'Ivoire) (Yamoussoukro)'),
            ('Kenya', 'Kenya (Nairobi)'),
            ('Lesotho', 'Lesotho (Maseru)'),
            ('Liberia', 'Liberia (Monrovia)'),
            ('Libya', 'Libya (Tripoli)'),
            ('Madagascar', 'Madagascar (Antananarivo)'),
            ('Malawi', 'Malawi (Lilongwe)'),
            ('Mali', 'Mali (Bamako)'),
            ('Mauritania', 'Mauritania (Nouakchott)'),
            ('Mauritius', 'Mauritius (Port Louis)'),
            ('Morocco', 'Morocco (Rabat)'),
            ('Mozambique', 'Mozambique (Maputo)'),
            ('Namibia', 'Namibia (Windhoek)'),
            ('Niger', 'Niger (Niamey)'),
            ('Nigeria', 'Nigeria (Abuja)'),
            ('Rwanda', 'Rwanda (Kigali)'),
            ('São Tomé and Príncipe', 'São Tomé and Príncipe (São Tomé)'),
            ('Senegal', 'Senegal (Dakar)'),
            ('Seychelles', 'Seychelles (Victoria)'),
            ('Sierra Leone', 'Sierra Leone (Freetown)'),
            ('Somalia', 'Somalia (Mogadishu)'),
            ('South Africa', 'South Africa (Pretoria)'),
            ('South Sudan', 'South Sudan (Juba)'),
            ('Sudan', 'Sudan (Khartoum)'),
            ('Tanzania', 'Tanzania (Dodoma)'),
            ('Togo', 'Togo (Lomé)'),
            ('Tunisia', 'Tunisia (Tunis)'),
            ('Uganda', 'Uganda (Kampala)'),
            ('Zambia', 'Zambia (Lusaka)'),
            ('Zimbabwe', 'Zimbabwe (Harare)'),
            # Europe
            ('Albania', 'Albania (Tirana)'),
            ('Andorra', 'Andorra (Andorra la Vella)'),
            ('Armenia', 'Armenia (Yerevan)'),
            ('Austria', 'Austria (Vienna)'),
            ('Azerbaijan', 'Azerbaijan (Baku)'),
            ('Belarus', 'Belarus (Minsk)'),
            ('Belgium', 'Belgium (Brussels)'),
            ('Bosnia and Herzegovina', 'Bosnia and Herzegovina (Sarajevo)'),
            ('Bulgaria', 'Bulgaria (Sofia)'),
            ('Croatia', 'Croatia (Zagreb)'),
            ('Cyprus', 'Cyprus (Nicosia)'),
            ('Czech Republic', 'Czech Republic (Czechia) (Prague)'),
            ('Denmark', 'Denmark (Copenhagen)'),
            ('Estonia', 'Estonia (Tallinn)'),
            ('Finland', 'Finland (Helsinki)'),
            ('France', 'France (Paris)'),
            ('Georgia', 'Georgia (Tbilisi)'),
            ('Germany', 'Germany (Berlin)'),
            ('Greece', 'Greece (Athens)'),
            ('Hungary', 'Hungary (Budapest)'),
            ('Iceland', 'Iceland (Reykjavík)'),
            ('Ireland', 'Ireland (Dublin)'),
            ('Italy', 'Italy (Rome)'),
            ('Kazakhstan', 'Kazakhstan (Astana/Nur-Sultan)'),
            ('Kosovo', 'Kosovo (Pristina)'),
            ('Latvia', 'Latvia (Riga)'),
            ('Liechtenstein', 'Liechtenstein (Vaduz)'),
            ('Lithuania', 'Lithuania (Vilnius)'),
            ('Luxembourg', 'Luxembourg (Luxembourg City)'),
            ('Malta', 'Malta (Valletta)'),
            ('Moldova', 'Moldova (Chișinău)'),
            ('Monaco', 'Monaco (Monaco)'),
            ('Montenegro', 'Montenegro (Podgorica)'),
            ('Netherlands', 'Netherlands (Amsterdam)'),
            ('North Macedonia', 'North Macedonia (Skopje)'),
            ('Norway', 'Norway (Oslo)'),
            ('Poland', 'Poland (Warsaw)'),
            ('Portugal', 'Portugal (Lisbon)'),
            ('Romania', 'Romania (Bucharest)'),
            ('Russia', 'Russia (Moscow)'),
            ('San Marino', 'San Marino (San Marino)'),
            ('Serbia', 'Serbia (Belgrade)'),
            ('Slovakia', 'Slovakia (Bratislava)'),
            ('Slovenia', 'Slovenia (Ljubljana)'),
            ('Spain', 'Spain (Madrid)'),
            ('Sweden', 'Sweden (Stockholm)'),
            ('Switzerland', 'Switzerland (Bern)'),
            ('Turkey', 'Turkey (Ankara)'),
            ('Ukraine', 'Ukraine (Kyiv)'),
            ('United Kingdom', 'United Kingdom (London)'),
            ('Vatican City', 'Vatican City (Holy See) (Vatican City)'),
            # Latin America
            ('Argentina', 'Argentina (Buenos Aires)'),
            ('Belize', 'Belize (Belmopan)'),
            ('Bolivia', 'Bolivia (Sucre)'),
            ('Brazil', 'Brazil (Brasília)'),
            ('Chile', 'Chile (Santiago)'),
            ('Colombia', 'Colombia (Bogotá)'),
            ('Costa Rica', 'Costa Rica (San José)'),
            ('Cuba', 'Cuba (Havana)'),
            ('Dominican Republic', 'Dominican Republic (Santo Domingo)'),
            ('Ecuador', 'Ecuador (Quito)'),
            ('El Salvador', 'El Salvador (San Salvador)'),
            ('Guatemala', 'Guatemala (Guatemala City)'),
            ('Honduras', 'Honduras (Tegucigalpa)'),
            ('Mexico', 'Mexico (Mexico City)'),
            ('Nicaragua', 'Nicaragua (Managua)'),
            ('Panama', 'Panama (Panama City)'),
            ('Paraguay', 'Paraguay (Asunción)'),
            ('Peru', 'Peru (Lima)'),
            ('Puerto Rico', 'Puerto Rico (San Juan)'),
            ('Uruguay', 'Uruguay (Montevideo)'),
            ('Venezuela', 'Venezuela (Caracas)'),
            # GCC
            ('Saudi Arabia', 'Saudi Arabia (Riyadh)'),
            ('UAE', 'United Arab Emirates (UAE) (Abu Dhabi)'),
            ('Qatar', 'Qatar (Doha)'),
            ('Kuwait', 'Kuwait (Kuwait City)'),
            ('Bahrain', 'Bahrain (Manama)'),
            ('Oman', 'Oman (Muscat)'),
            # Asia
            ('Pakistan', 'Pakistan (Islamabad)'),
            ('India', 'India (New Delhi)'),
        ],
        widget=forms.Select(attrs={
            'class': 'shadow-sm focus:ring-yellow-500 focus:border-yellow-500 block w-full sm:text-sm border-gray-300 rounded-md',
            'required': 'required',
            'id': 'destination_country_select'
        }),
        help_text='Select the country where the product should be delivered'
    )
    
    funding_source = forms.ChoiceField(
        choices=[
            ('seller_funds', "Seller's Funds - I will finance this sourcing request"),
            ('crm_funding', 'CRM Funding Request - Request CRM to finance this sourcing'),
        ],
        widget=forms.RadioSelect(attrs={
            'class': 'focus:ring-yellow-500 h-4 w-4 text-yellow-600 border-gray-300'
        }),
        help_text='Choose how this sourcing request will be financed'
    )
    
    # Optional Form Fields
    supplier_name = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'shadow-sm focus:ring-yellow-500 focus:border-yellow-500 block w-full sm:text-sm border-gray-300 rounded-md',
            'placeholder': 'Enter preferred supplier name (optional)'
        }),
        help_text='If you have a preferred supplier, provide their company name'
    )
    
    supplier_phone = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'shadow-sm focus:ring-yellow-500 focus:border-yellow-500 block w-full sm:text-sm border-gray-300 rounded-md',
            'placeholder': '+971501234567'
        }),
        help_text='Include country code for international numbers'
    )
    
    product_description = forms.CharField(
        max_length=1000,
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'shadow-sm focus:ring-yellow-500 focus:border-yellow-500 block w-full sm:text-sm border-gray-300 rounded-md',
            'rows': '4',
            'placeholder': 'Enter detailed product specifications and requirements...'
        }),
        help_text='Detailed product specifications and requirements'
    )
    
    target_unit_price = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'shadow-sm focus:ring-yellow-500 focus:border-yellow-500 block w-full sm:text-sm border-gray-300 rounded-md',
            'step': '0.01',
            'placeholder': 'Enter target unit price'
        }),
        help_text='Help administrators understand pricing expectations'
    )
    
    currency = forms.ChoiceField(
        choices=[
            ('USD', 'USD'),
            ('AED', 'AED'),
            ('SAR', 'SAR'),
        ],
        required=False,
        initial='AED',
        widget=forms.Select(attrs={
            'class': 'shadow-sm focus:ring-yellow-500 focus:border-yellow-500 block w-full sm:text-sm border-gray-300 rounded-md'
        })
    )
    
    quality_requirements = forms.MultipleChoiceField(
        choices=[
            ('brand_new', 'Brand New Only'),
            ('original_packaging', 'Original Packaging Required'),
            ('warranty', 'Warranty Required'),
            ('certified', 'Certified Products Only'),
        ],
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'focus:ring-yellow-500 h-4 w-4 text-yellow-600 border-gray-300 rounded'
        }),
        help_text='Specify quality standards and requirements'
    )
    
    special_instructions = forms.CharField(
        max_length=500,
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'shadow-sm focus:ring-yellow-500 focus:border-yellow-500 block w-full sm:text-sm border-gray-300 rounded-md',
            'rows': '3',
            'placeholder': 'Enter additional requirements or special handling instructions...'
        }),
        help_text='Additional requirements or special handling instructions'
    )
    
    product_image = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-yellow-50 file:text-yellow-700 hover:file:bg-yellow-100',
            'accept': 'image/*'
        }),
        help_text='Upload a product image (optional but recommended)'
    )
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Validate that at least one funding source is selected
        funding_source = cleaned_data.get('funding_source')
        if not funding_source:
            raise forms.ValidationError('Please select a funding source.')
        
        # Validate carton quantity
        carton_quantity = cleaned_data.get('carton_quantity')
        if carton_quantity and carton_quantity < 1:
            raise forms.ValidationError('Carton quantity must be at least 1.')
        
        # Validate target unit price if provided
        target_unit_price = cleaned_data.get('target_unit_price')
        if target_unit_price and target_unit_price <= 0:
            raise forms.ValidationError('Target unit price must be greater than 0.')
        
        return cleaned_data


class SourcingRequestForm(forms.ModelForm):
    """Form for creating and editing sourcing requests."""
    
    # Additional fields for the form
    request_type = forms.ChoiceField(
        choices=[
            ('', 'Select a request type'),
            ('new_supplier', 'New Supplier'),
            ('replenishment', 'Inventory Replenishment'),
            ('new_product', 'New Product Sourcing'),
            ('sample', 'Sample Request'),
        ],
        widget=forms.Select(attrs={
            'class': 'shadow-sm focus:ring-yellow-500 focus:border-yellow-500 block w-full sm:text-sm border-gray-300 rounded-md',
            'required': 'required'
        })
    )
    
    quantity = forms.IntegerField(
        min_value=1,
        widget=forms.NumberInput(attrs={
            'class': 'shadow-sm focus:ring-yellow-500 focus:border-yellow-500 block w-full sm:text-sm border-gray-300 rounded-md',
            'required': 'required'
        })
    )
    
    target_date = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'shadow-sm focus:ring-yellow-500 focus:border-yellow-500 block w-full sm:text-sm border-gray-300 rounded-md',
            'type': 'date',
            'required': 'required'
        })
    )
    
    budget = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'shadow-sm focus:ring-yellow-500 focus:border-yellow-500 block w-full sm:text-sm border-gray-300 rounded-md',
            'step': '0.01',
            'min': '0',
            'placeholder': 'Enter budget in AED'
        })
    )
    
    product = forms.ChoiceField(
        choices=[('', 'Select a product')],
        required=False,
        widget=forms.Select(attrs={
            'class': 'shadow-sm focus:ring-yellow-500 focus:border-yellow-500 block w-full sm:text-sm border-gray-300 rounded-md'
        })
    )
    
    new_product_name = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'shadow-sm focus:ring-yellow-500 focus:border-yellow-500 block w-full sm:text-sm border-gray-300 rounded-md',
            'placeholder': 'Enter new product name'
        })
    )
    
    references = forms.FileField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'sr-only'
        })
    )
    
    class Meta:
        model = SourcingRequest
        fields = [
            'product_name', 'product_image', 'carton_quantity', 'unit_quantity',
            'source_country', 'destination_country', 'finance_source',
            'supplier_contact', 'supplier_phone', 'cost_per_unit',
            'shipping_cost', 'customs_fees', 'weight', 'dimensions',
            'priority', 'notes'
        ]
        widgets = {
            'product_image': forms.FileInput(attrs={
                'class': 'block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-yellow-50 file:text-yellow-700 hover:file:bg-yellow-100',
                'accept': 'image/*'
            }),
            'product_name': forms.TextInput(attrs={
                'class': 'shadow-sm focus:ring-yellow-500 focus:border-yellow-500 block w-full sm:text-sm border-gray-300 rounded-md',
                'placeholder': 'Enter product name (e.g., iPhone 15 Pro Max)'
            }),
            'carton_quantity': forms.NumberInput(attrs={
                'class': 'shadow-sm focus:ring-yellow-500 focus:border-yellow-500 block w-full sm:text-sm border-gray-300 rounded-md',
                'min': '1',
                'max': '10000'
            }),
            'unit_quantity': forms.NumberInput(attrs={
                'class': 'shadow-sm focus:ring-yellow-500 focus:border-yellow-500 block w-full sm:text-sm border-gray-300 rounded-md',
                'min': '1',
                'max': '1000'
            }),
            'source_country': forms.Select(attrs={
                'class': 'shadow-sm focus:ring-yellow-500 focus:border-yellow-500 block w-full sm:text-sm border-gray-300 rounded-md'
            }),
            'destination_country': forms.Select(attrs={
                'class': 'shadow-sm focus:ring-yellow-500 focus:border-yellow-500 block w-full sm:text-sm border-gray-300 rounded-md'
            }),
            'finance_source': forms.Select(attrs={
                'class': 'shadow-sm focus:ring-yellow-500 focus:border-yellow-500 block w-full sm:text-sm border-gray-300 rounded-md'
            }),
            'supplier_contact': forms.TextInput(attrs={
                'class': 'shadow-sm focus:ring-yellow-500 focus:border-yellow-500 block w-full sm:text-sm border-gray-300 rounded-md',
                'placeholder': 'Supplier contact person name'
            }),
            'supplier_phone': forms.TextInput(attrs={
                'class': 'shadow-sm focus:ring-yellow-500 focus:border-yellow-500 block w-full sm:text-sm border-gray-300 rounded-md',
                'placeholder': '+971501234567'
            }),
            'cost_per_unit': forms.NumberInput(attrs={
                'class': 'shadow-sm focus:ring-yellow-500 focus:border-yellow-500 block w-full sm:text-sm border-gray-300 rounded-md',
                'step': '0.01',
                'min': '0'
            }),
            'shipping_cost': forms.NumberInput(attrs={
                'class': 'shadow-sm focus:ring-yellow-500 focus:border-yellow-500 block w-full sm:text-sm border-gray-300 rounded-md',
                'step': '0.01',
                'min': '0'
            }),
            'customs_fees': forms.NumberInput(attrs={
                'class': 'shadow-sm focus:ring-yellow-500 focus:border-yellow-500 block w-full sm:text-sm border-gray-300 rounded-md',
                'step': '0.01',
                'min': '0'
            }),
            'weight': forms.NumberInput(attrs={
                'class': 'shadow-sm focus:ring-yellow-500 focus:border-yellow-500 block w-full sm:text-sm border-gray-300 rounded-md',
                'step': '0.01',
                'min': '0'
            }),
            'dimensions': forms.TextInput(attrs={
                'class': 'shadow-sm focus:ring-yellow-500 focus:border-yellow-500 block w-full sm:text-sm border-gray-300 rounded-md',
                'placeholder': 'LxWxH in cm (e.g., 30x20x10)'
            }),
            'priority': forms.Select(attrs={
                'class': 'shadow-sm focus:ring-yellow-500 focus:border-yellow-500 block w-full sm:text-sm border-gray-300 rounded-md'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'shadow-sm focus:ring-yellow-500 focus:border-yellow-500 block w-full sm:text-sm border-gray-300 rounded-md',
                'rows': '4',
                'placeholder': 'Add any additional specifications, requirements, or notes...'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Set choices for country fields
        source_countries = [
            ('', 'Select source country'),
            ('UAE', 'UAE'),
            ('China', 'China'),
            ('USA', 'USA'),
            ('Turkey', 'Turkey'),
            ('Korea', 'Korea'),
            ('Japan', 'Japan'),
        ]
        
        destination_countries = [
            ('', 'Select destination country'),
            # Africa
            ('Algeria', 'Algeria (Algiers)'),
            ('Angola', 'Angola (Luanda)'),
            ('Benin', 'Benin (Porto-Novo)'),
            ('Botswana', 'Botswana (Gaborone)'),
            ('Burkina Faso', 'Burkina Faso (Ouagadougou)'),
            ('Burundi', 'Burundi (Gitega)'),
            ('Cabo Verde', 'Cabo Verde (Cape Verde) (Praia)'),
            ('Cameroon', 'Cameroon (Yaoundé)'),
            ('Central African Republic', 'Central African Republic (Bangui)'),
            ('Chad', 'Chad (N\'Djamena)'),
            ('Comoros', 'Comoros (Moroni)'),
            ('Democratic Republic of the Congo', 'Democratic Republic of the Congo (DRC) (Kinshasa)'),
            ('Republic of the Congo', 'Republic of the Congo (Brazzaville)'),
            ('Djibouti', 'Djibouti (Djibouti)'),
            ('Egypt', 'Egypt (Cairo)'),
            ('Equatorial Guinea', 'Equatorial Guinea (Malabo)'),
            ('Eritrea', 'Eritrea (Asmara)'),
            ('Eswatini', 'Eswatini (Swaziland) (Mbabane)'),
            ('Ethiopia', 'Ethiopia (Addis Ababa)'),
            ('Gabon', 'Gabon (Libreville)'),
            ('Gambia', 'Gambia (Banjul)'),
            ('Ghana', 'Ghana (Accra)'),
            ('Guinea', 'Guinea (Conakry)'),
            ('Guinea-Bissau', 'Guinea-Bissau (Bissau)'),
            ('Ivory Coast', 'Ivory Coast (Côte d\'Ivoire) (Yamoussoukro)'),
            ('Kenya', 'Kenya (Nairobi)'),
            ('Lesotho', 'Lesotho (Maseru)'),
            ('Liberia', 'Liberia (Monrovia)'),
            ('Libya', 'Libya (Tripoli)'),
            ('Madagascar', 'Madagascar (Antananarivo)'),
            ('Malawi', 'Malawi (Lilongwe)'),
            ('Mali', 'Mali (Bamako)'),
            ('Mauritania', 'Mauritania (Nouakchott)'),
            ('Mauritius', 'Mauritius (Port Louis)'),
            ('Morocco', 'Morocco (Rabat)'),
            ('Mozambique', 'Mozambique (Maputo)'),
            ('Namibia', 'Namibia (Windhoek)'),
            ('Niger', 'Niger (Niamey)'),
            ('Nigeria', 'Nigeria (Abuja)'),
            ('Rwanda', 'Rwanda (Kigali)'),
            ('São Tomé and Príncipe', 'São Tomé and Príncipe (São Tomé)'),
            ('Senegal', 'Senegal (Dakar)'),
            ('Seychelles', 'Seychelles (Victoria)'),
            ('Sierra Leone', 'Sierra Leone (Freetown)'),
            ('Somalia', 'Somalia (Mogadishu)'),
            ('South Africa', 'South Africa (Pretoria)'),
            ('South Sudan', 'South Sudan (Juba)'),
            ('Sudan', 'Sudan (Khartoum)'),
            ('Tanzania', 'Tanzania (Dodoma)'),
            ('Togo', 'Togo (Lomé)'),
            ('Tunisia', 'Tunisia (Tunis)'),
            ('Uganda', 'Uganda (Kampala)'),
            ('Zambia', 'Zambia (Lusaka)'),
            ('Zimbabwe', 'Zimbabwe (Harare)'),
            # Europe
            ('Albania', 'Albania (Tirana)'),
            ('Andorra', 'Andorra (Andorra la Vella)'),
            ('Armenia', 'Armenia (Yerevan)'),
            ('Austria', 'Austria (Vienna)'),
            ('Azerbaijan', 'Azerbaijan (Baku)'),
            ('Belarus', 'Belarus (Minsk)'),
            ('Belgium', 'Belgium (Brussels)'),
            ('Bosnia and Herzegovina', 'Bosnia and Herzegovina (Sarajevo)'),
            ('Bulgaria', 'Bulgaria (Sofia)'),
            ('Croatia', 'Croatia (Zagreb)'),
            ('Cyprus', 'Cyprus (Nicosia)'),
            ('Czech Republic', 'Czech Republic (Czechia) (Prague)'),
            ('Denmark', 'Denmark (Copenhagen)'),
            ('Estonia', 'Estonia (Tallinn)'),
            ('Finland', 'Finland (Helsinki)'),
            ('France', 'France (Paris)'),
            ('Georgia', 'Georgia (Tbilisi)'),
            ('Germany', 'Germany (Berlin)'),
            ('Greece', 'Greece (Athens)'),
            ('Hungary', 'Hungary (Budapest)'),
            ('Iceland', 'Iceland (Reykjavík)'),
            ('Ireland', 'Ireland (Dublin)'),
            ('Italy', 'Italy (Rome)'),
            ('Kazakhstan', 'Kazakhstan (Astana/Nur-Sultan)'),
            ('Kosovo', 'Kosovo (Pristina)'),
            ('Latvia', 'Latvia (Riga)'),
            ('Liechtenstein', 'Liechtenstein (Vaduz)'),
            ('Lithuania', 'Lithuania (Vilnius)'),
            ('Luxembourg', 'Luxembourg (Luxembourg City)'),
            ('Malta', 'Malta (Valletta)'),
            ('Moldova', 'Moldova (Chișinău)'),
            ('Monaco', 'Monaco (Monaco)'),
            ('Montenegro', 'Montenegro (Podgorica)'),
            ('Netherlands', 'Netherlands (Amsterdam)'),
            ('North Macedonia', 'North Macedonia (Skopje)'),
            ('Norway', 'Norway (Oslo)'),
            ('Poland', 'Poland (Warsaw)'),
            ('Portugal', 'Portugal (Lisbon)'),
            ('Romania', 'Romania (Bucharest)'),
            ('Russia', 'Russia (Moscow)'),
            ('San Marino', 'San Marino (San Marino)'),
            ('Serbia', 'Serbia (Belgrade)'),
            ('Slovakia', 'Slovakia (Bratislava)'),
            ('Slovenia', 'Slovenia (Ljubljana)'),
            ('Spain', 'Spain (Madrid)'),
            ('Sweden', 'Sweden (Stockholm)'),
            ('Switzerland', 'Switzerland (Bern)'),
            ('Turkey', 'Turkey (Ankara)'),
            ('Ukraine', 'Ukraine (Kyiv)'),
            ('United Kingdom', 'United Kingdom (London)'),
            ('Vatican City', 'Vatican City (Holy See) (Vatican City)'),
            # Latin America
            ('Argentina', 'Argentina (Buenos Aires)'),
            ('Belize', 'Belize (Belmopan)'),
            ('Bolivia', 'Bolivia (Sucre)'),
            ('Brazil', 'Brazil (Brasília)'),
            ('Chile', 'Chile (Santiago)'),
            ('Colombia', 'Colombia (Bogotá)'),
            ('Costa Rica', 'Costa Rica (San José)'),
            ('Cuba', 'Cuba (Havana)'),
            ('Dominican Republic', 'Dominican Republic (Santo Domingo)'),
            ('Ecuador', 'Ecuador (Quito)'),
            ('El Salvador', 'El Salvador (San Salvador)'),
            ('Guatemala', 'Guatemala (Guatemala City)'),
            ('Honduras', 'Honduras (Tegucigalpa)'),
            ('Mexico', 'Mexico (Mexico City)'),
            ('Nicaragua', 'Nicaragua (Managua)'),
            ('Panama', 'Panama (Panama City)'),
            ('Paraguay', 'Paraguay (Asunción)'),
            ('Peru', 'Peru (Lima)'),
            ('Puerto Rico', 'Puerto Rico (San Juan)'),
            ('Uruguay', 'Uruguay (Montevideo)'),
            ('Venezuela', 'Venezuela (Caracas)'),
            # GCC
            ('Saudi Arabia', 'Saudi Arabia (Riyadh)'),
            ('UAE', 'United Arab Emirates (UAE) (Abu Dhabi)'),
            ('Qatar', 'Qatar (Doha)'),
            ('Kuwait', 'Kuwait (Kuwait City)'),
            ('Bahrain', 'Bahrain (Manama)'),
            ('Oman', 'Oman (Muscat)'),
            # Asia
            ('Pakistan', 'Pakistan (Islamabad)'),
            ('India', 'India (New Delhi)'),
        ]
        
        self.fields['source_country'].choices = source_countries
        self.fields['destination_country'].choices = destination_countries
        
        # Set default priority
        self.fields['priority'].initial = 'medium'
    
    def clean(self):
        cleaned_data = super().clean()
        request_type = cleaned_data.get('request_type')
        product = cleaned_data.get('product')
        new_product_name = cleaned_data.get('new_product_name')
        
        # Validate based on request type
        if request_type == 'new_product':
            if not new_product_name:
                raise forms.ValidationError('Product name is required for new product requests.')
        elif request_type in ['replenishment', 'sample']:
            if not product:
                raise forms.ValidationError('Product selection is required for replenishment or sample requests.')
        
        return cleaned_data 