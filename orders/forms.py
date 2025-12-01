from django import forms
from django.forms import inlineformset_factory
from .models import Order, OrderItem
from django.utils.translation import gettext_lazy as _
from sellers.models import Product
from utils.countries import COUNTRIES
from .area_utils import get_cities_list, get_states_for_city

class OrderForm(forms.ModelForm):
    """Form for creating and updating orders."""
    
    country = forms.ChoiceField(
        choices=[('AE', 'United Arab Emirates')],  # Only UAE available
        initial='AE',  # Default to UAE
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 pl-10 bg-slate-50 border border-slate-200 rounded-xl focus:ring-2 focus:ring-amber-500 focus:border-amber-500 transition-all duration-200 appearance-none relative z-0',
        })
    )
    
    class Meta:
        model = Order
        fields = [
            'customer', 'date', 'status', 'customer_phone', 
            'seller', 'agent', 'city', 'state', 
            'country', 'street_address', 'shipping_address', 'notes', 'internal_notes'
        ]
        exclude = ['order_code']
        widgets = {
            'customer': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 pl-10 bg-slate-50 border border-slate-200 rounded-xl focus:ring-2 focus:ring-amber-500 focus:border-amber-500 transition-all duration-200',
                'placeholder': 'Enter customer full name'
            }),
            'date': forms.DateTimeInput(attrs={
                'class': 'w-full px-4 py-3 pl-10 bg-slate-50 border border-slate-200 rounded-xl focus:ring-2 focus:ring-amber-500 focus:border-amber-500 transition-all duration-200',
                'type': 'datetime-local'
            }),
            'status': forms.Select(attrs={
                'class': 'w-full px-4 py-3 pl-10 bg-slate-50 border border-slate-200 rounded-xl focus:ring-2 focus:ring-amber-500 focus:border-amber-500 transition-all duration-200 appearance-none relative z-0'
            }),
            'customer_phone': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 pl-10 bg-slate-50 border border-slate-200 rounded-xl focus:ring-2 focus:ring-amber-500 focus:border-amber-500 transition-all duration-200',
                'placeholder': '+971501234567'
            }),
            'seller_email': forms.EmailInput(attrs={
                'class': 'w-full px-4 py-3 pl-10 bg-slate-50 border border-slate-200 rounded-xl focus:ring-2 focus:ring-amber-500 focus:border-amber-500 transition-all duration-200',
                'placeholder': 'seller@atlasfulfillment.ae'
            }),
            'seller': forms.Select(attrs={
                'class': 'w-full px-4 py-3 pl-10 bg-slate-50 border border-slate-200 rounded-xl focus:ring-2 focus:ring-amber-500 focus:border-amber-500 transition-all duration-200 appearance-none relative z-0',
                'placeholder': 'Select seller'
            }),
            'agent': forms.Select(attrs={
                'class': 'w-full px-4 py-3 pl-10 bg-slate-50 border border-slate-200 rounded-xl focus:ring-2 focus:ring-amber-500 focus:border-amber-500 transition-all duration-200 appearance-none relative z-0',
                'placeholder': 'Select call center agent'
            }),

            'city': forms.Select(attrs={
                'class': 'w-full px-4 py-3 pl-10 bg-slate-50 border border-slate-200 rounded-xl focus:ring-2 focus:ring-amber-500 focus:border-amber-500 transition-all duration-200 appearance-none relative z-0',
                'id': 'id_city'
            }),
            'state': forms.Select(attrs={
                'class': 'w-full px-4 py-3 pl-10 bg-slate-50 border border-slate-200 rounded-xl focus:ring-2 focus:ring-amber-500 focus:border-amber-500 transition-all duration-200 appearance-none relative z-0',
                'id': 'id_state'
            }),
            'street_address': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 pl-10 bg-slate-50 border border-slate-200 rounded-xl focus:ring-2 focus:ring-amber-500 focus:border-amber-500 transition-all duration-200',
                'placeholder': 'Enter street address and building number'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 pl-10 bg-slate-50 border border-slate-200 rounded-xl focus:ring-2 focus:ring-amber-500 focus:border-amber-500 transition-all duration-200 resize-none',
                'rows': '3',
                'placeholder': 'Customer notes or special instructions'
            }),
            'internal_notes': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 pl-10 bg-slate-50 border border-slate-200 rounded-xl focus:ring-2 focus:ring-amber-500 focus:border-amber-500 transition-all duration-200 resize-none',
                'rows': '3',
                'placeholder': 'Internal notes for team members'
            }),
            'shipping_address': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 pl-10 bg-slate-50 border border-slate-200 rounded-xl focus:ring-2 focus:ring-amber-500 focus:border-amber-500 transition-all duration-200 resize-none',
                'rows': '3',
                'placeholder': 'Enter complete shipping address'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Set initial date to current time if creating new order
        if not self.instance.pk:
            from django.utils import timezone
            now = timezone.now()
            # Set both initial and instance date
            self.fields['date'].initial = now
            self.instance.date = now
        
        # Import models at the top
        from users.models import User
        from roles.models import UserRole, Role
        
        # Handle seller field based on user role
        if user:
            user_role = user.primary_role.name if user.primary_role else None
            # Also check if user has specific roles using the has_role method
            is_seller = user.has_role('Seller')
            is_admin = user.has_role('Admin') or user.has_role('Super Admin')
            
            # Set a default queryset for all cases to avoid NoneType errors
            default_queryset = User.objects.filter(is_active=True)
            
            if is_seller:
                # For sellers, hide the seller field and set it to the current user
                self.fields['seller'].widget = forms.HiddenInput()
                self.fields['seller'].initial = user
                self.fields['seller'].required = False
                self.fields['seller'].queryset = default_queryset
            elif is_admin:
                # For admins, always show seller selection
                seller_role = Role.objects.filter(name='Seller').first()
                if seller_role:
                    seller_users = User.objects.filter(
                        user_roles__role=seller_role,
                        user_roles__is_active=True
                    ).distinct()
                    self.fields['seller'].queryset = seller_users
                    self.fields['seller'].empty_label = "Select a seller"
                else:
                    # If no seller role exists, show all users
                    self.fields['seller'].queryset = default_queryset
                    self.fields['seller'].empty_label = "Select a seller"
            else:
                # For other roles, hide the seller field
                self.fields['seller'].widget = forms.HiddenInput()
                self.fields['seller'].required = False
                self.fields['seller'].disabled = True
                self.fields['seller'].queryset = default_queryset
            # Set default status to pending for new orders
            self.fields['status'].initial = 'pending'
            
            # For sellers, hide status field completely and set it to pending
            if is_seller:
                # Hide status field for sellers - they cannot change it
                self.fields['status'].widget = forms.HiddenInput()
                self.fields['status'].initial = 'pending'
                self.fields['status'].required = False
                
                # Set date to today and make it read-only for sellers
                from django.utils import timezone
                now = timezone.now()
                self.fields['date'].initial = now
                self.fields['date'].widget.attrs['readonly'] = True
                self.fields['date'].widget.attrs['class'] = 'w-full px-4 py-3 pl-10 bg-gray-100 border border-gray-200 rounded-xl text-gray-600 cursor-not-allowed'
                # Ensure the instance date is set for sellers
                if not self.instance.pk:
                    self.instance.date = now
                
                # Hide and disable agent field for sellers
                self.fields['agent'].widget = forms.HiddenInput()
                self.fields['agent'].required = False
                self.fields['agent'].disabled = True
        

        
        # Product choices are now handled in the template via JavaScript
        
        # Populate agent choices with call center agents
        if 'agent' in self.fields:
            call_center_role = Role.objects.filter(name='Call Center Agent').first()
            if call_center_role:
                call_center_agents = User.objects.filter(
                    user_roles__role=call_center_role,
                    user_roles__is_active=True
                ).distinct().order_by('first_name', 'last_name')
                self.fields['agent'].queryset = call_center_agents
                self.fields['agent'].empty_label = "Select a call center agent"
                print(f"Found {call_center_agents.count()} call center agents")
            else:
                # If no call center agent role exists, show all users
                call_center_agents = User.objects.filter(is_active=True).order_by('first_name', 'last_name')
                self.fields['agent'].queryset = call_center_agents
                self.fields['agent'].empty_label = "Select a call center agent"
                print(f"No call center role found, using {call_center_agents.count()} active users")
            
            # Set initial value for agent field if editing existing order
            if self.instance and self.instance.pk and self.instance.agent:
                self.fields['agent'].initial = self.instance.agent.id
                print(f"Setting agent initial value to: {self.instance.agent.id}")
            else:
                print("No agent to set initial value for")
            
            # Debug: Print field information
            print(f"Agent field exists, queryset count: {self.fields['agent'].queryset.count()}")
            print(f"Agent field initial value: {self.fields['agent'].initial}")
            print(f"Agent field choices count: {len(self.fields['agent'].choices)}")
            
            # Ensure agent field is not required and can be empty
            self.fields['agent'].required = False
            self.fields['agent'].allow_empty = True
            
            cities = get_cities_list()
            self.fields['city'].widget.choices = [('', 'Select City')] + cities
            self.fields['city'].choices = [('', 'Select City')] + cities
            
            if self.instance and self.instance.pk and self.instance.city:
                city_name = self.instance.city
                states = get_states_for_city(city_name)
                self.fields['state'].widget.choices = [('', 'Select Area')] + states
                self.fields['state'].choices = [('', 'Select Area')] + states
            else:
                self.fields['state'].widget.choices = [('', 'Select Area - Please select city first')]
                self.fields['state'].choices = [('', 'Select Area - Please select city first')]

    def clean(self):
        cleaned_data = super().clean()
        
        # Get the user from the form instance
        user = getattr(self, 'user', None)
        
        # Debug: Print cleaned data
        print(f"Form clean - Agent field value: {cleaned_data.get('agent')}")
        print(f"Form clean - Seller field value: {cleaned_data.get('seller')}")
        print(f"Form clean - User role: {user.primary_role.name if user and user.primary_role else 'No role'}")
        print(f"Form clean - Form data keys: {list(cleaned_data.keys())}")
        print(f"Form clean - Agent field type: {type(cleaned_data.get('agent'))}")
        if cleaned_data.get('agent'):
            print(f"Form clean - Agent field value details: {cleaned_data['agent']}")
        
        # Handle status field for sellers
        if user and user.has_role('Seller'):
            # For sellers, always set status to pending
            cleaned_data['status'] = 'pending'
            
            # Ensure date is set for sellers if not provided
            if not cleaned_data.get('date'):
                from django.utils import timezone
                cleaned_data['date'] = timezone.now()
        
        # Preserve seller information when editing existing orders (only for sellers)
        if self.instance and self.instance.pk and user and user.has_role('Seller'):
            # If this is an existing order being edited by a seller, preserve seller info
            if hasattr(self.instance, 'seller') and self.instance.seller:
                cleaned_data['seller'] = self.instance.seller
            if hasattr(self.instance, 'seller_email') and self.instance.seller_email:
                cleaned_data['seller_email'] = self.instance.seller_email
        
        # Validate price is in AED (positive number)
        price = cleaned_data.get('price_per_unit')
        if price and price <= 0:
            self.add_error('price_per_unit', 'Price must be greater than 0 AED')
        

        
        return cleaned_data


class OrderItemForm(forms.ModelForm):
    """Form for order items."""
    
    class Meta:
        model = OrderItem
        fields = ['product', 'quantity', 'price']
        widgets = {
            'product': forms.Select(attrs={
                'class': 'bg-white border border-gray-300 rounded-md py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:ring-2 focus:ring-yellow-500 focus:border-transparent'
            }),
            'quantity': forms.NumberInput(attrs={
                'class': 'bg-white border border-gray-300 rounded-md py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:ring-2 focus:ring-yellow-500 focus:border-transparent', 
                'min': 1
            }),
            'price': forms.NumberInput(attrs={
                'class': 'bg-white border border-gray-300 rounded-md py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:ring-2 focus:ring-yellow-500 focus:border-transparent', 
                'step': '0.01', 
                'min': '0',
                'placeholder': '0.00 AED'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Product choices are now handled in the template via JavaScript


# Create a formset for order items
OrderItemFormSet = inlineformset_factory(
    Order, 
    OrderItem,
    form=OrderItemForm,
    extra=1,
    can_delete=True
)


class OrderStatusUpdateForm(forms.ModelForm):
    """Form for updating order status."""
    
    class Meta:
        model = Order
        fields = ['status', 'workflow_status', 'tracking_number', 'cancelled_reason']
        widgets = {
            'status': forms.Select(attrs={
                'class': 'bg-white border border-gray-300 rounded-md py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:ring-2 focus:ring-yellow-500 focus:border-transparent'
            }),
            'workflow_status': forms.Select(attrs={
                'class': 'bg-white border border-gray-300 rounded-md py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:ring-2 focus:ring-yellow-500 focus:border-transparent'
            }),
            'tracking_number': forms.TextInput(attrs={
                'class': 'bg-white border border-gray-300 rounded-md py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:ring-2 focus:ring-yellow-500 focus:border-transparent'
            }),
            'cancelled_reason': forms.Textarea(attrs={
                'class': 'bg-white border border-gray-300 rounded-md py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:ring-2 focus:ring-yellow-500 focus:border-transparent',
                'rows': 2
            }),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        status = cleaned_data.get('status')
        cancelled_reason = cleaned_data.get('cancelled_reason', '')
        tracking_number = cleaned_data.get('tracking_number', '')
        
        # If status is cancelled, cancelled_reason is required
        if status == 'cancelled' and not cancelled_reason:
            self.add_error('cancelled_reason', 'Cancellation reason is required when status is set to Cancelled')
        
        # If status is in delivery or delivered, tracking_number is required
        if status in ['shipped', 'delivered'] and not tracking_number:
            self.add_error('tracking_number', 'Tracking number is required for Delivery statuses')
        
        return cleaned_data 


class OrderImportForm(forms.Form):
    file = forms.FileField(
        label=_('Import File'),
        help_text=_('Upload a CSV file containing order data.'),
        widget=forms.FileInput(attrs={
            'class': 'block w-full text-sm text-gray-900 border border-gray-300 rounded-lg cursor-pointer bg-gray-50 focus:outline-none',
            'accept': '.csv',
            'id': 'csv_file'
        })
    )
    
    seller = forms.ModelChoiceField(
        queryset=None,
        required=False,
        label=_('Select Seller'),
        help_text=_('Select the seller for the imported orders (Admin only)'),
        widget=forms.Select(attrs={
            'class': 'form-select w-full'
        })
    )
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Import models at the top
        from users.models import User
        from roles.models import UserRole, Role
        
        if user:
            user_role = user.primary_role.name if user.primary_role else None
            # Also check if user has specific roles using the has_role method
            is_seller = user.has_role('Seller')
            is_admin = user.has_role('Admin') or user.has_role('Super Admin')
            
            # Set a default queryset for all cases to avoid NoneType errors
            default_queryset = User.objects.filter(is_active=True)
            
            if is_seller:
                # For sellers, hide the seller field and set it to the current user
                self.fields['seller'].widget = forms.HiddenInput()
                self.fields['seller'].initial = user
                self.fields['seller'].required = False
                self.fields['seller'].queryset = default_queryset
            elif is_admin:
                # For admins, show seller selection with only seller users
                # Get all users with Seller role
                seller_role = Role.objects.filter(name='Seller').first()
                if seller_role:
                    seller_users = User.objects.filter(
                        user_roles__role=seller_role,
                        user_roles__is_active=True
                    ).distinct()
                    self.fields['seller'].queryset = seller_users
                    self.fields['seller'].empty_label = "Select a seller"
                else:
                    # If no seller role exists, show all users
                    self.fields['seller'].queryset = default_queryset
                    self.fields['seller'].empty_label = "Select a seller"
            else:
                # For other roles, hide the seller field
                self.fields['seller'].widget = forms.HiddenInput()
                self.fields['seller'].required = False
                self.fields['seller'].disabled = True
                self.fields['seller'].queryset = default_queryset

    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            # Check file extension
            if not file.name.lower().endswith('.csv'):
                raise forms.ValidationError(_('Please upload a CSV file (.csv extension).'))
            
            # Check file size (max 5MB)
            if file.size > 5 * 1024 * 1024:
                raise forms.ValidationError(_('File size must be less than 5MB.'))
            
            # Check if file is empty
            if file.size == 0:
                raise forms.ValidationError(_('File is empty.'))
        
        return file 