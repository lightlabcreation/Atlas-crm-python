from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('email', 'full_name', 'primary_role', 'store_name', 'account_number', 'approval_status', 'is_active', 'date_joined')
    list_filter = ('is_active', 'is_staff', 'date_joined', 'store_type', 'country', 'approval_status')
    search_fields = ('email', 'full_name', 'phone_number', 'store_name', 'bank_name', 'account_number')
    ordering = ('-date_joined',)
    readonly_fields = ('date_joined', 'last_login', 'approved_by', 'approved_at')
    
    actions = ['approve_users', 'reject_users']
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal Information'), {
            'fields': (
                'full_name', 'phone_number', 'country', 
                'id_front_image', 'id_back_image', 'profile_image'
            )
        }),
        (_('E-commerce Store Details'), {
            'fields': (
                'store_name', 'store_link', 'store_type', 'store_specialization',
                'marketing_platforms', 'expected_daily_orders'
            )
        }),
        (_('Bank Details'), {
            'fields': (
                'bank_name', 'account_holder_name', 'account_number', 'iban_confirmation'
            )
        }),
        (_('Approval Status'), {
            'fields': (
                'approval_status', 'rejection_reason', 'approved_by', 'approved_at'
            )
        }),
        (_('Legacy Fields'), {
            'fields': ('company_name',),
            'classes': ('collapse',)
        }),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'full_name', 'password1', 'password2'),
        }),
    )

    def primary_role(self, obj):
        role = obj.get_primary_role()
        return role.name if role else '-'
    primary_role.short_description = 'Primary Role'
    
    def account_number(self, obj):
        return obj.account_number if obj.account_number else '-'
    account_number.short_description = 'IBAN'
    
    def approve_users(self, request, queryset):
        """Admin action to approve selected users."""
        from django.utils import timezone
        count = 0
        for user in queryset.filter(approval_status='pending'):
            user.approve_user(request.user)
            count += 1
        
        self.message_user(request, f"تمت الموافقة على {count} مستخدم.")
    approve_users.short_description = "Approve selected users"
    
    def reject_users(self, request, queryset):
        """Admin action to reject selected users."""
        count = 0
        for user in queryset.filter(approval_status='pending'):
            user.reject_user(request.user, "Rejected via admin action")
            count += 1
        
        self.message_user(request, f"تم رفض {count} مستخدم.")
    reject_users.short_description = "Reject selected users"
