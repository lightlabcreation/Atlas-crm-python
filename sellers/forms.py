from django import forms
from sellers.models import Product, ProductDeletionRequest
from django.core.validators import MinValueValidator

class SellerProductForm(forms.ModelForm):
    """Form for sellers to create and edit products."""
    
    class Meta:
        model = Product
        fields = [
            'name_en', 'name_ar', 'category', 'description', 'selling_price', 
            'purchase_price', 'product_link', 'stock_quantity', 'image'
        ]
        widgets = {
            'name_en': forms.TextInput(attrs={
                'class': 'form-input w-full',
                'placeholder': 'Enter product name in English',
                'required': True
            }),
            'name_ar': forms.TextInput(attrs={
                'class': 'form-input w-full',
                'placeholder': 'أدخل اسم المنتج بالعربية'
            }),
            'category': forms.Select(attrs={
                'class': 'form-input w-full'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-input w-full',
                'rows': '4',
                'placeholder': 'Enter product description'
            }),
            'selling_price': forms.NumberInput(attrs={
                'class': 'form-input w-full',
                'placeholder': '0.00',
                'step': '0.01',
                'min': '0',
                'required': True
            }),
            'purchase_price': forms.NumberInput(attrs={
                'class': 'form-input w-full',
                'placeholder': '0.00',
                'step': '0.01',
                'min': '0'
            }),
            'product_link': forms.URLInput(attrs={
                'class': 'form-input w-full',
                'placeholder': 'https://example.com/product',
                'required': True
            }),
            'stock_quantity': forms.NumberInput(attrs={
                'class': 'form-input w-full',
                'placeholder': '0',
                'min': '0',
                'step': '1'
            }),
            'image': forms.FileInput(attrs={
                'class': 'form-input w-full',
                'accept': 'image/*'
            })
        }
        labels = {
            'name_en': 'Product Name (English) *',
            'name_ar': 'Product Name (Arabic)',
            'category': 'Category',
            'description': 'Description',
            'selling_price': 'Selling Price (AED) *',
            'purchase_price': 'Cost Price (AED)',
            'product_link': 'Product Link *',
            'stock_quantity': 'Stock Quantity',
            'image': 'Product Image'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Add category choices
        self.fields['category'].widget.choices = [
            ('', 'Select category'),
            ('electronics', 'Electronics'),
            ('clothing', 'Clothing'),
            ('home', 'Home & Garden'),
            ('sports', 'Sports'),
            ('books', 'Books'),
            ('beauty', 'Beauty'),
            ('toys', 'Toys'),
            ('other', 'Other')
        ]
        
        # Make required fields more obvious
        for field_name, field in self.fields.items():
            if field_name in ['name_en', 'selling_price', 'product_link']:
                field.widget.attrs['required'] = True

    def clean_product_link(self):
        """Validate product link is a valid URL."""
        product_link = self.cleaned_data.get('product_link')
        if not product_link:
            raise forms.ValidationError('Product link is required.')
        return product_link

    def clean_selling_price(self):
        """Validate selling price is positive."""
        selling_price = self.cleaned_data.get('selling_price')
        if selling_price and selling_price <= 0:
            raise forms.ValidationError('Selling price must be greater than 0.')
        return selling_price

    def clean_purchase_price(self):
        """Validate purchase price is non-negative."""
        purchase_price = self.cleaned_data.get('purchase_price')
        if purchase_price and purchase_price < 0:
            raise forms.ValidationError('Purchase price cannot be negative.')
        return purchase_price

    def clean_stock_quantity(self):
        """Validate stock quantity is non-negative."""
        stock_quantity = self.cleaned_data.get('stock_quantity')
        if stock_quantity and stock_quantity < 0:
            raise forms.ValidationError('Stock quantity cannot be negative.')
        return stock_quantity

    def save(self, commit=True, seller=None):
        """Save the product with the seller automatically set."""
        product = super().save(commit=False)
        if seller:
            product.seller = seller
        if commit:
            product.save()
        return product

class ProductDeletionRequestForm(forms.ModelForm):
    """Form for requesting product deletion."""
    
    class Meta:
        model = ProductDeletionRequest
        fields = ['reason']
        widgets = {
            'reason': forms.Textarea(attrs={
                'class': 'form-input w-full',
                'rows': '4',
                'placeholder': 'Please provide a reason for deleting this product...',
                'required': True
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['reason'].label = 'Reason for Deletion'
        self.fields['reason'].help_text = 'Please provide a detailed reason for why you want to delete this product.'
    
    def clean_reason(self):
        """Validate reason is not empty and has minimum length."""
        reason = self.cleaned_data.get('reason')
        if not reason or len(reason.strip()) < 10:
            raise forms.ValidationError('Please provide a detailed reason (at least 10 characters).')
        return reason.strip()
