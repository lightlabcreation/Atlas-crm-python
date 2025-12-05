# finance/cod_forms.py
"""
Forms for COD (Cash on Delivery) Payment Management
"""
from django import forms
from django.utils.translation import gettext_lazy as _
from .cod_models import CODPayment, CODReconciliation
from orders.models import Order


class CODPaymentForm(forms.ModelForm):
    """Form for creating and editing COD payments"""

    class Meta:
        model = CODPayment
        fields = [
            'order', 'cod_amount', 'customer_name', 'customer_phone',
            'delivery_address', 'notes'
        ]
        widgets = {
            'order': forms.Select(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-4 py-3 focus:ring-2 focus:ring-orange-500 focus:border-orange-500'
            }),
            'cod_amount': forms.NumberInput(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-4 py-3 focus:ring-2 focus:ring-orange-500 focus:border-orange-500',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00'
            }),
            'customer_name': forms.TextInput(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-4 py-3 focus:ring-2 focus:ring-orange-500 focus:border-orange-500',
                'placeholder': 'Customer Full Name'
            }),
            'customer_phone': forms.TextInput(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-4 py-3 focus:ring-2 focus:ring-orange-500 focus:border-orange-500',
                'placeholder': '+971 XX XXX XXXX'
            }),
            'delivery_address': forms.Textarea(attrs={
                'rows': 3,
                'class': 'w-full border border-gray-300 rounded-lg px-4 py-3 focus:ring-2 focus:ring-orange-500 focus:border-orange-500 resize-none',
                'placeholder': 'Full delivery address'
            }),
            'notes': forms.Textarea(attrs={
                'rows': 2,
                'class': 'w-full border border-gray-300 rounded-lg px-4 py-3 focus:ring-2 focus:ring-orange-500 focus:border-orange-500 resize-none',
                'placeholder': 'Additional notes (optional)'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show orders without existing COD payments
        self.fields['order'].queryset = Order.objects.filter(cod_payment__isnull=True)


class CODCollectionForm(forms.ModelForm):
    """Form for delivery agents to mark COD as collected"""

    class Meta:
        model = CODPayment
        fields = [
            'collected_amount', 'collection_proof_image', 'customer_signature',
            'receipt_number', 'notes'
        ]
        widgets = {
            'collected_amount': forms.NumberInput(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-4 py-3 focus:ring-2 focus:ring-green-500 focus:border-green-500',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00',
                'required': True
            }),
            'receipt_number': forms.TextInput(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-4 py-3 focus:ring-2 focus:ring-green-500 focus:border-green-500',
                'placeholder': 'Receipt Number'
            }),
            'collection_proof_image': forms.FileInput(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-4 py-3 focus:ring-2 focus:ring-green-500 focus:border-green-500',
                'accept': 'image/*',
                'required': True
            }),
            'customer_signature': forms.FileInput(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-4 py-3 focus:ring-2 focus:ring-green-500 focus:border-green-500',
                'accept': 'image/*',
                'required': True
            }),
            'notes': forms.Textarea(attrs={
                'rows': 2,
                'class': 'w-full border border-gray-300 rounded-lg px-4 py-3 focus:ring-2 focus:ring-green-500 focus:border-green-500 resize-none',
                'placeholder': 'Collection notes'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make proof of payment MANDATORY as per specification requirement
        self.fields['collection_proof_image'].required = True
        self.fields['customer_signature'].required = True
        self.fields['collected_amount'].required = True

        # Add help text for required fields
        self.fields['collection_proof_image'].help_text = _('MANDATORY: Photo proof of payment collection')
        self.fields['customer_signature'].help_text = _('MANDATORY: Customer signature confirmation')

    def clean_collected_amount(self):
        """Validate collected amount"""
        collected = self.cleaned_data.get('collected_amount')
        if collected is None:
            raise forms.ValidationError(_('Collected amount is required'))
        if collected < 0:
            raise forms.ValidationError(_('Collected amount cannot be negative'))
        return collected

    def clean_collection_proof_image(self):
        """Validate collection proof image - MANDATORY"""
        image = self.cleaned_data.get('collection_proof_image')
        if not image:
            raise forms.ValidationError(_('Collection proof image is MANDATORY. Please upload photo evidence of payment collection.'))

        # Validate file size (max 5MB)
        if image.size > 5 * 1024 * 1024:
            raise forms.ValidationError(_('Image file size cannot exceed 5MB'))

        return image

    def clean_customer_signature(self):
        """Validate customer signature - MANDATORY"""
        signature = self.cleaned_data.get('customer_signature')
        if not signature:
            raise forms.ValidationError(_('Customer signature is MANDATORY. Please upload customer signature confirmation.'))

        # Validate file size (max 5MB)
        if signature.size > 5 * 1024 * 1024:
            raise forms.ValidationError(_('Signature file size cannot exceed 5MB'))

        return signature


class CODDepositForm(forms.Form):
    """Form for marking COD as deposited to company account"""

    cod_payment_ids = forms.CharField(widget=forms.HiddenInput())
    deposit_reference = forms.CharField(
        max_length=100,
        required=True,
        label=_('Deposit Reference'),
        widget=forms.TextInput(attrs={
            'class': 'w-full border border-gray-300 rounded-lg px-4 py-3 focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
            'placeholder': 'Bank reference or transaction ID'
        })
    )
    deposit_date = forms.DateTimeField(
        required=False,
        label=_('Deposit Date'),
        widget=forms.DateTimeInput(attrs={
            'type': 'datetime-local',
            'class': 'w-full border border-gray-300 rounded-lg px-4 py-3 focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
        })
    )
    notes = forms.CharField(
        required=False,
        label=_('Notes'),
        widget=forms.Textarea(attrs={
            'rows': 2,
            'class': 'w-full border border-gray-300 rounded-lg px-4 py-3 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none',
            'placeholder': 'Additional notes about the deposit'
        })
    )


class CODVerificationForm(forms.Form):
    """Form for finance team to verify COD payments"""

    cod_payment_ids = forms.CharField(widget=forms.HiddenInput())
    verification_notes = forms.CharField(
        required=False,
        label=_('Verification Notes'),
        widget=forms.Textarea(attrs={
            'rows': 3,
            'class': 'w-full border border-gray-300 rounded-lg px-4 py-3 focus:ring-2 focus:ring-purple-500 focus:border-purple-500 resize-none',
            'placeholder': 'Verification comments'
        })
    )


class CODDisputeForm(forms.Form):
    """Form for creating a dispute for COD payment"""

    dispute_reason = forms.CharField(
        required=True,
        label=_('Dispute Reason'),
        widget=forms.Textarea(attrs={
            'rows': 4,
            'class': 'w-full border border-red-300 rounded-lg px-4 py-3 focus:ring-2 focus:ring-red-500 focus:border-red-500 resize-none',
            'placeholder': 'Explain the reason for dispute...'
        })
    )


class CODReconciliationForm(forms.ModelForm):
    """Form for COD reconciliation"""

    class Meta:
        model = CODReconciliation
        fields = [
            'reconciliation_date', 'agent', 'notes', 'discrepancy_notes'
        ]
        widgets = {
            'reconciliation_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full border border-gray-300 rounded-lg px-4 py-3 focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
            }),
            'agent': forms.Select(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-4 py-3 focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
            }),
            'notes': forms.Textarea(attrs={
                'rows': 3,
                'class': 'w-full border border-gray-300 rounded-lg px-4 py-3 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none'
            }),
            'discrepancy_notes': forms.Textarea(attrs={
                'rows': 2,
                'class': 'w-full border border-red-300 rounded-lg px-4 py-3 focus:ring-2 focus:ring-red-500 focus:border-red-500 resize-none',
                'placeholder': 'Notes about any discrepancies'
            }),
        }


class CODFilterForm(forms.Form):
    """Form for filtering COD payments"""

    status = forms.ChoiceField(
        choices=[('', 'All Statuses')] + list(CODPayment.COD_STATUS_CHOICES),
        required=False,
        widget=forms.Select(attrs={
            'class': 'border border-gray-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-orange-500 focus:border-orange-500'
        })
    )

    collected_by = forms.ModelChoiceField(
        queryset=None,  # Will be set in __init__
        required=False,
        empty_label='All Agents',
        widget=forms.Select(attrs={
            'class': 'border border-gray-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-orange-500 focus:border-orange-500'
        })
    )

    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'border border-gray-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-orange-500 focus:border-orange-500'
        })
    )

    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'border border-gray-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-orange-500 focus:border-orange-500'
        })
    )

    def __init__(self, *args, **kwargs):
        from django.contrib.auth import get_user_model
        super().__init__(*args, **kwargs)

        User = get_user_model()
        # Get users who have collected COD payments
        self.fields['collected_by'].queryset = User.objects.filter(
            cod_collections__isnull=False
        ).distinct().order_by('first_name', 'last_name')
