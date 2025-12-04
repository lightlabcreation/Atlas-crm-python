from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm as BaseUserCreationForm, PasswordChangeForm as DjangoPasswordChangeForm
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
import re

User = get_user_model()

class EmailVerificationForm(forms.Form):
    """Form for email verification code."""
    verification_code = forms.CharField(
        max_length=6,
        min_length=6,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-center text-2xl font-mono tracking-widest',
            'placeholder': '000000',
            'maxlength': '6',
            'pattern': '[0-9]{6}',
            'inputmode': 'numeric'
        }),
        help_text="Enter the 6-digit code sent to your email"
    )
    
    def clean_verification_code(self):
        code = self.cleaned_data.get('verification_code')
        if code and not code.isdigit():
            raise ValidationError("Verification code must contain only numbers.")
        return code

class LoginForm(forms.Form):
    """Form for user login."""
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-t-md focus:outline-none focus:ring-yellow-500 focus:border-yellow-500 focus:z-10 sm:text-sm', 'placeholder': 'Email address'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-b-md focus:outline-none focus:ring-yellow-500 focus:border-yellow-500 focus:z-10 sm:text-sm', 'placeholder': 'Password'})
    )

class RegisterForm(forms.ModelForm):
    """Form for user registration."""
    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={'class': 'appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-yellow-500 focus:border-yellow-500 sm:text-sm'})
    )
    password2 = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput(attrs={'class': 'appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-yellow-500 focus:border-yellow-500 sm:text-sm'})
    )

    # Add reCAPTCHA field
    from django_recaptcha.fields import ReCaptchaField
    captcha = ReCaptchaField()
    
    # Marketing platforms choices
    MARKETING_PLATFORMS_CHOICES = [
        ('instagram', 'Instagram'),
        ('facebook', 'Facebook'),
        ('tiktok', 'TikTok'),
        ('snapchat', 'Snapchat'),
        ('twitter', 'Twitter'),
        ('linkedin', 'LinkedIn'),
        ('youtube', 'YouTube'),
        ('google_ads', 'Google Ads'),
        ('other', 'Other'),
    ]
    
    marketing_platforms = forms.MultipleChoiceField(
        choices=MARKETING_PLATFORMS_CHOICES,
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-checkbox h-4 w-4 text-yellow-600 border-gray-300 rounded focus:ring-yellow-500'})
    )
    
    class Meta:
        model = User
        fields = [
            'email', 'full_name', 'phone_number', 'country',
            'id_front_image', 'id_back_image',
            'store_name', 'store_link', 'store_type', 'store_specialization', 
            'marketing_platforms', 'expected_daily_orders',
            'bank_name', 'account_holder_name', 'account_number', 'iban_confirmation'
        ]
        widgets = {
            'email': forms.EmailInput(attrs={
                'class': 'appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-yellow-500 focus:border-yellow-500 sm:text-sm',
                'placeholder': 'Email address'
            }),
            'full_name': forms.TextInput(attrs={
                'class': 'appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-yellow-500 focus:border-yellow-500 sm:text-sm',
                'placeholder': 'Full Name'
            }),
            'phone_number': forms.TextInput(attrs={
                'class': 'appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-yellow-500 focus:border-yellow-500 sm:text-sm',
                'placeholder': 'Phone Number (e.g., +971501234567)',
                'pattern': r'^(\+971|971|0)?[5-9][0-9]{8}$'
            }),
            'country': forms.Select(attrs={
                'class': 'appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-yellow-500 focus:border-yellow-500 sm:text-sm'
            }, choices=[
                ('', 'Select Country'),
                ('UAE', 'United Arab Emirates'),
                ('KSA', 'Saudi Arabia'),
                ('Kuwait', 'Kuwait'),
                ('Qatar', 'Qatar'),
                ('Bahrain', 'Bahrain'),
                ('Oman', 'Oman'),
                ('Jordan', 'Jordan'),
                ('Lebanon', 'Lebanon'),
                ('Egypt', 'Egypt'),
                ('Other', 'Other'),
            ]),
            'id_front_image': forms.FileInput(attrs={
                'class': 'form-input w-full',
                'accept': 'image/*',
                'required': True
            }),
            'id_back_image': forms.FileInput(attrs={
                'class': 'form-input w-full',
                'accept': 'image/*',
                'required': True
            }),
            'store_name': forms.TextInput(attrs={
                'class': 'appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-yellow-500 focus:border-yellow-500 sm:text-sm',
                'placeholder': 'Store Name'
            }),
            'store_link': forms.URLInput(attrs={
                'class': 'appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-yellow-500 focus:border-yellow-500 sm:text-sm',
                'placeholder': 'https://yourstore.com'
            }),
            'store_type': forms.Select(attrs={
                'class': 'appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-yellow-500 focus:border-yellow-500 sm:text-sm'
            }, choices=[
                ('', 'Select Store Type'),
                ('general', 'General'),
                ('specialized', 'Specialized')
            ]),
            'store_specialization': forms.TextInput(attrs={
                'class': 'appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-yellow-500 focus:border-yellow-500 sm:text-sm',
                'placeholder': 'e.g., Electronics, Fashion, Food'
            }),
            'expected_daily_orders': forms.NumberInput(attrs={
                'class': 'appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-yellow-500 focus:border-yellow-500 sm:text-sm',
                'min': '0',
                'value': '0'
            }),
            'bank_name': forms.TextInput(attrs={
                'class': 'appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-yellow-500 focus:border-yellow-500 sm:text-sm',
                'placeholder': 'Bank Name'
            }),
            'account_holder_name': forms.TextInput(attrs={
                'class': 'appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-yellow-500 focus:border-yellow-500 sm:text-sm',
                'placeholder': 'Account Holder Name (as per bank)'
            }),
            'account_number': forms.TextInput(attrs={
                'class': 'appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-yellow-500 focus:border-yellow-500 sm:text-sm',
                'placeholder': 'IBAN Number'
            }),
            'iban_confirmation': forms.TextInput(attrs={
                'class': 'appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-yellow-500 focus:border-yellow-500 sm:text-sm',
                'placeholder': 'Confirm IBAN'
            }),
        }
    
    def clean_phone_number(self):
        """Validate phone number format for UAE numbers."""
        phone_number = self.cleaned_data.get('phone_number')
        if phone_number:
            # Remove any spaces or special characters
            phone_number = re.sub(r'[\s\-\(\)]', '', phone_number)
            
            # Check if it's a valid UAE phone number
            # Pattern: +971501234567 or 971501234567 or 0501234567
            pattern = r'^(\+971|971|0)?[5-9][0-9]{8}$'
            
            if not re.match(pattern, phone_number):
                raise ValidationError(
                    "يرجى إدخال رقم هاتف صحيح للإمارات. "
                    "مثال: +971501234567 أو 0501234567"
                )
            
            # Normalize to +971 format
            if phone_number.startswith('0'):
                phone_number = '+971' + phone_number[1:]
            elif phone_number.startswith('971'):
                phone_number = '+' + phone_number
            elif not phone_number.startswith('+971'):
                phone_number = '+971' + phone_number
            
            return phone_number
        return phone_number
    
    def clean_password1(self):
        password1 = self.cleaned_data.get("password1")
        if password1:
            # Check minimum length
            if len(password1) < 8:
                raise ValidationError("Password must be at least 8 characters long.")
            
            # Check for uppercase letter
            if not any(c.isupper() for c in password1):
                raise ValidationError("Password must contain at least one uppercase letter.")
            
            # Check for lowercase letter
            if not any(c.islower() for c in password1):
                raise ValidationError("Password must contain at least one lowercase letter.")
            
            # Check for number
            if not any(c.isdigit() for c in password1):
                raise ValidationError("Password must contain at least one number.")
        
        return password1
    
    def clean_password2(self):
        # Check that the two password entries match
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise ValidationError("Passwords don't match")
        return password2
    
    def clean_iban_confirmation(self):
        account_number = self.cleaned_data.get("account_number")
        iban_confirmation = self.cleaned_data.get("iban_confirmation")
        if account_number and iban_confirmation and account_number != iban_confirmation:
            raise ValidationError("IBAN confirmation doesn't match")
        return iban_confirmation
    
    def clean_store_specialization(self):
        store_type = self.cleaned_data.get("store_type")
        store_specialization = self.cleaned_data.get("store_specialization")
        if store_type == 'specialized' and not store_specialization:
            raise ValidationError("Please specify the store specialization")
        return store_specialization
    
    def save(self, commit=True):
        # Save the provided password in hashed format
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        
        # Convert marketing_platforms to JSON
        if 'marketing_platforms' in self.cleaned_data:
            user.marketing_platforms = self.cleaned_data['marketing_platforms']
        
        if commit:
            user.save()
        return user

class UserCreationForm(BaseUserCreationForm):
    """Form for admin to create a new user."""
    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-input w-full',
            'placeholder': 'Enter first name'
        })
    )
    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-input w-full',
            'placeholder': 'Enter last name'
        })
    )
    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={
            'class': 'form-input w-full pr-10',
            'placeholder': 'Enter password'
        })
    )
    password2 = forms.CharField(
        label="Password confirmation",
        widget=forms.PasswordInput(attrs={
            'class': 'form-input w-full pr-10',
            'placeholder': 'Confirm password'
        })
    )
    primary_role = forms.ModelChoiceField(
        queryset=None,
        required=False,
        empty_label="Select a role",
        widget=forms.Select(attrs={
            'class': 'form-select w-full'
        })
    )
    secondary_roles = forms.ModelMultipleChoiceField(
        queryset=None,
        required=False,
        widget=forms.SelectMultiple(attrs={
            'class': 'form-select w-full',
            'size': '5'
        }),
        help_text="Hold Ctrl/Cmd to select multiple roles"
    )
    
    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'phone_number', 'is_active', 'profile_image', 
                  'store_link', 'bank_name', 'account_holder_name', 'account_number', 'iban_confirmation',
                  'id_front_image', 'id_back_image')
        widgets = {
            'email': forms.EmailInput(attrs={
                'class': 'form-input w-full',
                'placeholder': 'user@atlasfulfillment.ae'
            }),
            'first_name': forms.TextInput(attrs={
                'class': 'form-input w-full',
                'placeholder': 'Enter first name'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-input w-full',
                'placeholder': 'Enter last name'
            }),
            'phone_number': forms.TextInput(attrs={
                'class': 'form-input w-full',
                'placeholder': '+971501234567'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-checkbox h-5 w-5 text-yellow-600 border-gray-300 rounded focus:ring-yellow-500'
            }),
            'profile_image': forms.FileInput(attrs={
                'class': 'form-input w-full',
                'accept': 'image/*'
            }),
            'store_link': forms.URLInput(attrs={
                'class': 'form-input w-full',
                'placeholder': 'https://yourstore.com'
            }),
            'bank_name': forms.TextInput(attrs={
                'class': 'form-input w-full',
                'placeholder': 'Enter bank name'
            }),
            'account_holder_name': forms.TextInput(attrs={
                'class': 'form-input w-full',
                'placeholder': 'Enter account holder name'
            }),
            'account_number': forms.TextInput(attrs={
                'class': 'form-input w-full',
                'placeholder': 'Enter account number or IBAN'
            }),
            'iban_confirmation': forms.TextInput(attrs={
                'class': 'form-input w-full',
                'placeholder': 'Confirm IBAN'
            }),
            'id_front_image': forms.FileInput(attrs={
                'class': 'form-input w-full',
                'accept': 'image/*'
            }),
            'id_back_image': forms.FileInput(attrs={
                'class': 'form-input w-full',
                'accept': 'image/*'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            from roles.models import Role
            roles_queryset = Role.objects.filter(is_active=True).order_by('name')
            self.fields['primary_role'].queryset = roles_queryset
            self.fields['secondary_roles'].queryset = roles_queryset
        except ImportError:
            # If roles app is not available, hide the fields
            if 'primary_role' in self.fields:
                del self.fields['primary_role']
            if 'secondary_roles' in self.fields:
                del self.fields['secondary_roles']
    
    def clean_password1(self):
        password1 = self.cleaned_data.get("password1")
        if password1:
            # Check minimum length
            if len(password1) < 8:
                raise ValidationError("Password must be at least 8 characters long.")
            
            # Check for uppercase letter
            if not any(c.isupper() for c in password1):
                raise ValidationError("Password must contain at least one uppercase letter.")
            
            # Check for lowercase letter
            if not any(c.islower() for c in password1):
                raise ValidationError("Password must contain at least one lowercase letter.")
            
            # Check for number
            if not any(c.isdigit() for c in password1):
                raise ValidationError("Password must contain at least one number.")
        
        return password1
    
    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match")
        return password2
    
    def save(self, commit=True):
        user = super().save(commit=False)
        
        # Combine first_name and last_name into full_name
        first_name = self.cleaned_data.get('first_name', '')
        last_name = self.cleaned_data.get('last_name', '')
        user.full_name = f"{first_name} {last_name}".strip()
        
        # Set admin-created users as automatically approved and active
        user.is_active = True
        user.approval_status = 'approved'
        user.email_verified = True  # Admin-created users don't need email verification
        
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
            
            # Handle role assignment
            try:
                from roles.models import UserRole
                
                # Handle primary role
                if 'primary_role' in self.cleaned_data and self.cleaned_data['primary_role']:
                    new_role = self.cleaned_data['primary_role']
                    
                    # Create user role using get_or_create to prevent duplicates
                    UserRole.objects.get_or_create(
                        user=user,
                        role=new_role,
                        defaults={
                            'is_primary': True,
                            'is_active': True
                        }
                    )
                
                # Handle secondary roles
                if 'secondary_roles' in self.cleaned_data:
                    selected_secondary_roles = self.cleaned_data['secondary_roles']
                    
                    for role in selected_secondary_roles:
                        # Skip if this is the primary role
                        if 'primary_role' in self.cleaned_data and self.cleaned_data['primary_role'] == role:
                            continue
                        
                        UserRole.objects.get_or_create(
                            user=user,
                            role=role,
                            defaults={'is_primary': False, 'is_active': True}
                        )
                        
            except ImportError:
                pass
        
        return user

class UserChangeForm(forms.ModelForm):
    """Form for user updates."""
    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-input w-full',
            'placeholder': 'Enter first name'
        })
    )
    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-input w-full',
            'placeholder': 'Enter last name'
        })
    )
    primary_role = forms.ModelChoiceField(
        queryset=None,
        required=False,
        empty_label="Select a role",
        widget=forms.Select(attrs={
            'class': 'form-select w-full'
        })
    )
    secondary_roles = forms.ModelMultipleChoiceField(
        queryset=None,
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'form-checkbox'
        })
    )
    password1 = forms.CharField(
        label="New Password",
        required=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-input w-full',
            'placeholder': 'Enter new password (leave blank to keep current)'
        })
    )
    password2 = forms.CharField(
        label="Confirm New Password",
        required=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-input w-full',
            'placeholder': 'Confirm new password'
        })
    )
    
    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'phone_number', 'profile_image')
        widgets = {
            'email': forms.EmailInput(attrs={
                'class': 'form-input w-full',
                'placeholder': 'user@atlasfulfillment.ae'
            }),
            'first_name': forms.TextInput(attrs={
                'class': 'form-input w-full',
                'placeholder': 'Enter first name'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-input w-full',
                'placeholder': 'Enter last name'
            }),
            'phone_number': forms.TextInput(attrs={
                'class': 'form-input w-full',
                'placeholder': '+971501234567'
            }),
            'profile_image': forms.FileInput(attrs={
                'class': 'form-input w-full',
                'accept': 'image/*'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Set initial values for first_name and last_name from full_name
        if self.instance.pk and self.instance.full_name:
            name_parts = self.instance.full_name.split(' ', 1)
            if len(name_parts) > 1:
                self.fields['first_name'].initial = name_parts[0]
                self.fields['last_name'].initial = name_parts[1]
                print(f"Setting first_name: {name_parts[0]}, last_name: {name_parts[1]}")  # Debug
            else:
                self.fields['first_name'].initial = name_parts[0]
                print(f"Setting first_name only: {name_parts[0]}")  # Debug
        else:
            print(f"No instance or full_name. Instance: {self.instance}, full_name: {getattr(self.instance, 'full_name', 'N/A')}")  # Debug
        
        try:
            from roles.models import Role
            self.fields['primary_role'].queryset = Role.objects.filter(is_active=True).order_by('name')
            self.fields['secondary_roles'].queryset = Role.objects.filter(is_active=True).order_by('name')
            
            # Set initial value for primary_role
            if self.instance.pk:
                # Get primary role from user_roles
                primary_user_role = self.instance.user_roles.filter(is_primary=True, is_active=True).first()
                if primary_user_role:
                    self.fields['primary_role'].initial = primary_user_role.role
                    print(f"Setting primary role initial: {primary_user_role.role.name}")
                
                # Set initial values for secondary roles (excluding primary)
                secondary_roles = self.instance.user_roles.filter(is_primary=False, is_active=True)
                if secondary_roles.exists():
                    secondary_role_list = [role.role for role in secondary_roles]
                    self.fields['secondary_roles'].initial = secondary_role_list
                    print(f"Setting secondary roles initial: {[r.name for r in secondary_role_list]}")
                else:
                    print("No secondary roles found")
        except ImportError:
            # If roles app is not available, hide the fields
            if 'primary_role' in self.fields:
                del self.fields['primary_role']
    
    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        
        if password1 or password2:
            if not password1:
                raise ValidationError("Please enter a new password.")
            if not password2:
                raise ValidationError("Please confirm your new password.")
            if password1 != password2:
                raise ValidationError("Passwords do not match.")
            if len(password1) < 8:
                raise ValidationError("Password must be at least 8 characters long.")
        
        return cleaned_data
    
    def save(self, commit=True):
        original_is_active = self.instance.is_active if self.instance.pk else True
        
        user = super().save(commit=False)
        
        first_name = self.cleaned_data.get('first_name', '')
        last_name = self.cleaned_data.get('last_name', '')
        user.full_name = f"{first_name} {last_name}".strip()
        
        if 'is_active' not in self.cleaned_data or self.cleaned_data.get('is_active') is None:
            user.is_active = original_is_active
        
        if commit:
            user.save()
            
            # Handle password change if provided
            password1 = self.cleaned_data.get('password1')
            if password1:
                user.set_password(password1)
                user.save()
            
            # Handle role assignment
            try:
                from roles.models import UserRole
                
                # Handle primary role
                if 'primary_role' in self.cleaned_data and self.cleaned_data['primary_role']:
                    new_primary_role = self.cleaned_data['primary_role']
                    
                    # Remove existing primary role
                    UserRole.objects.filter(user=user, is_primary=True).update(is_primary=False)
                    
                    # Create or update primary user role
                    user_role, created = UserRole.objects.get_or_create(
                        user=user,
                        role=new_primary_role,
                        defaults={'is_primary': True, 'is_active': True}
                    )
                    if not created:
                        user_role.is_primary = True
                        user_role.is_active = True
                        user_role.save()
                
                # Handle secondary roles
                if 'secondary_roles' in self.cleaned_data:
                    selected_secondary_roles = self.cleaned_data['secondary_roles']
                    
                    # Get current secondary roles
                    current_secondary_roles = user.user_roles.filter(is_primary=False)
                    
                    # Remove roles that are no longer selected
                    for current_role in current_secondary_roles:
                        if current_role.role not in selected_secondary_roles:
                            current_role.delete()
                    
                    # Add new secondary roles
                    for role in selected_secondary_roles:
                        # Skip if this is the primary role
                        if 'primary_role' in self.cleaned_data and self.cleaned_data['primary_role'] == role:
                            continue
                        
                        UserRole.objects.get_or_create(
                            user=user,
                            role=role,
                            defaults={'is_primary': False, 'is_active': True}
                        )
                        
            except ImportError:
                pass
        
        return user

class PasswordChangeForm(DjangoPasswordChangeForm):
    """Form for changing user password."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['old_password'].widget.attrs.update({
            'class': 'appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-yellow-500 focus:border-yellow-500 sm:text-sm'
        })
        self.fields['new_password1'].widget.attrs.update({
            'class': 'appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-yellow-500 focus:border-yellow-500 sm:text-sm'
        })
        self.fields['new_password2'].widget.attrs.update({
            'class': 'appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-yellow-500 focus:border-yellow-500 sm:text-sm'
        }) 