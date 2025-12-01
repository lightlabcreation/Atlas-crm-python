from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Payment, TruvoPayment, PaymentPlatform, Invoice
import re

class PaymentForm(forms.ModelForm):
    """Form for creating and editing payments"""
    
    class Meta:
        model = Payment
        fields = ['order', 'amount', 'payment_method', 'payment_status', 'notes']
        widgets = {
            'amount': forms.NumberInput(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-4 py-3 focus:ring-2 focus:ring-orange-500 focus:border-orange-500 transition-colors duration-200',
                'step': '0.01',
                'min': '0'
            }),
            'payment_method': forms.Select(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-4 py-3 focus:ring-2 focus:ring-orange-500 focus:border-orange-500 transition-colors duration-200 bg-white'
            }),
            'payment_status': forms.Select(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-4 py-3 focus:ring-2 focus:ring-orange-500 focus:border-orange-500 transition-colors duration-200 bg-white'
            }),
            'order': forms.Select(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-4 py-3 focus:ring-2 focus:ring-orange-500 focus:border-orange-500 transition-colors duration-200 bg-white'
            }),
            'notes': forms.Textarea(attrs={
                'rows': 3,
                'class': 'w-full border border-gray-300 rounded-lg px-4 py-3 focus:ring-2 focus:ring-orange-500 focus:border-orange-500 transition-colors duration-200 resize-none'
            }),
        }

class TruvoPaymentForm(forms.ModelForm):
    """Form for creating and editing Truvo payments"""
    
    class Meta:
        model = TruvoPayment
        fields = ['order', 'amount', 'payment_status', 'customer_name', 'customer_email', 'customer_phone']
        widgets = {
            'amount': forms.NumberInput(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-4 py-3 focus:ring-2 focus:ring-orange-500 focus:border-orange-500 transition-colors duration-200',
                'step': '0.01',
                'min': '0'
            }),
            'payment_status': forms.Select(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-4 py-3 focus:ring-2 focus:ring-orange-500 focus:border-orange-500 transition-colors duration-200 bg-white'
            }),
            'order': forms.Select(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-4 py-3 focus:ring-2 focus:ring-orange-500 focus:border-orange-500 transition-colors duration-200 bg-white'
            }),
            'customer_name': forms.TextInput(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-4 py-3 focus:ring-2 focus:ring-orange-500 focus:border-orange-500 transition-colors duration-200'
            }),
            'customer_email': forms.EmailInput(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-4 py-3 focus:ring-2 focus:ring-orange-500 focus:border-orange-500 transition-colors duration-200'
            }),
            'customer_phone': forms.TextInput(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-4 py-3 focus:ring-2 focus:ring-orange-500 focus:border-orange-500 transition-colors duration-200'
            }),
        }

class PaymentPlatformForm(forms.ModelForm):
    """Form for creating and editing payment platform integrations"""
    
    class Meta:
        model = PaymentPlatform
        fields = [
            'platform_name', 'store_name', 'store_url', 'api_key', 'api_secret', 
            'access_token', 'refresh_token', 'merchant_id', 'webhook_url',
            'sync_frequency', 'auto_sync', 'sync_orders', 'sync_payments', 
            'sync_inventory', 'notes'
        ]
        widgets = {
            'platform_name': forms.Select(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-4 py-3 focus:ring-2 focus:ring-orange-500 focus:border-orange-500 transition-colors duration-200 bg-white'
            }),
            'store_name': forms.TextInput(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-4 py-3 focus:ring-2 focus:ring-orange-500 focus:border-orange-500 transition-colors duration-200'
            }),
            'store_url': forms.URLInput(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-4 py-3 focus:ring-2 focus:ring-orange-500 focus:border-orange-500 transition-colors duration-200'
            }),
            'api_key': forms.TextInput(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-4 py-3 focus:ring-2 focus:ring-orange-500 focus:border-orange-500 transition-colors duration-200'
            }),
            'api_secret': forms.PasswordInput(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-4 py-3 focus:ring-2 focus:ring-orange-500 focus:border-orange-500 transition-colors duration-200'
            }),
            'access_token': forms.PasswordInput(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-4 py-3 focus:ring-2 focus:ring-orange-500 focus:border-orange-500 transition-colors duration-200'
            }),
            'refresh_token': forms.PasswordInput(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-4 py-3 focus:ring-2 focus:ring-orange-500 focus:border-orange-500 transition-colors duration-200'
            }),
            'merchant_id': forms.TextInput(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-4 py-3 focus:ring-2 focus:ring-orange-500 focus:border-orange-500 transition-colors duration-200'
            }),
            'webhook_url': forms.URLInput(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-4 py-3 focus:ring-2 focus:ring-orange-500 focus:border-orange-500 transition-colors duration-200'
            }),
            'sync_frequency': forms.Select(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-4 py-3 focus:ring-2 focus:ring-orange-500 focus:border-orange-500 transition-colors duration-200 bg-white'
            }),
            'notes': forms.Textarea(attrs={
                'rows': 4,
                'class': 'w-full border border-gray-300 rounded-lg px-4 py-3 focus:ring-2 focus:ring-orange-500 focus:border-orange-500 transition-colors duration-200 resize-none'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make sensitive fields optional
        self.fields['api_secret'].required = False
        self.fields['access_token'].required = False
        self.fields['refresh_token'].required = False
        self.fields['merchant_id'].required = False
        self.fields['webhook_url'].required = False
    
    def clean(self):
        cleaned_data = super().clean()
        platform_name = cleaned_data.get('platform_name')
        
        # Platform-specific validation
        if platform_name == 'amazon_seller':
            if not cleaned_data.get('merchant_id'):
                self.add_error('merchant_id', _('Merchant ID is required for Amazon Seller Central'))
        
        elif platform_name == 'shopify':
            if not cleaned_data.get('api_key') or not cleaned_data.get('api_secret'):
                self.add_error('api_key', _('API Key and Secret are required for Shopify'))
        
        elif platform_name == 'magento':
            if not cleaned_data.get('access_token'):
                self.add_error('access_token', _('Access Token is required for Magento'))
        
        return cleaned_data

class PlatformConnectionTestForm(forms.Form):
    """Form for testing platform connections"""
    
    platform_id = forms.IntegerField(widget=forms.HiddenInput())
    test_type = forms.ChoiceField(
        choices=[
            ('connection', 'Test Connection'),
            ('orders', 'Test Orders Sync'),
            ('payments', 'Test Payments Sync'),
            ('inventory', 'Test Inventory Sync'),
        ],
        widget=forms.RadioSelect,
        initial='connection'
    )

class PlatformSyncForm(forms.Form):
    """Form for manual platform synchronization"""
    
    platform_id = forms.IntegerField(widget=forms.HiddenInput())
    sync_orders = forms.BooleanField(required=False, initial=True)
    sync_payments = forms.BooleanField(required=False, initial=True)
    sync_inventory = forms.BooleanField(required=False, initial=False)
    sync_products = forms.BooleanField(required=False, initial=False)
    sync_customers = forms.BooleanField(required=False, initial=False)
    
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'}),
        help_text=_('Sync data from this date (optional)')
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'}),
        help_text=_('Sync data until this date (optional)')
    )

class InvoiceForm(forms.ModelForm):
    """Form for creating and editing invoices"""
    
    class Meta:
        model = Invoice
        fields = ['order', 'total_amount', 'status', 'due_date', 'notes']
        widgets = {
            'total_amount': forms.NumberInput(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-4 py-3 focus:ring-2 focus:ring-orange-500 focus:border-orange-500 transition-colors duration-200',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00'
            }),
            'status': forms.Select(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-4 py-3 focus:ring-2 focus:ring-orange-500 focus:border-orange-500 transition-colors duration-200 bg-white'
            }),
            'order': forms.Select(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-4 py-3 focus:ring-2 focus:ring-orange-500 focus:border-orange-500 transition-colors duration-200 bg-white'
            }),
            'due_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full border border-gray-300 rounded-lg px-4 py-3 focus:ring-2 focus:ring-orange-500 focus:border-orange-500 transition-colors duration-200'
            }),
            'notes': forms.Textarea(attrs={
                'rows': 3,
                'class': 'w-full border border-gray-300 rounded-lg px-4 py-3 focus:ring-2 focus:ring-orange-500 focus:border-orange-500 transition-colors duration-200 resize-none'
            }),
        }
    
    def clean_total_amount(self):
        """Clean and validate total_amount field"""
        amount = self.cleaned_data.get('total_amount')
        
        if amount is None:
            return amount
            
        # If amount is a string, clean it
        if isinstance(amount, str):
            # Remove currency symbols and extra spaces
            amount = re.sub(r'[^\d.,]', '', amount)
            # Replace comma with dot for decimal separator
            amount = amount.replace(',', '.')
            
            try:
                amount = float(amount)
            except ValueError:
                raise forms.ValidationError(_('Please enter a valid amount.'))
        
        if amount < 0:
            raise forms.ValidationError(_('Amount cannot be negative.'))
            
        return amount 