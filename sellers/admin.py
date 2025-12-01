from django.contrib import admin
from .models import Product, SalesChannel

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name_en', 'code', 'seller', 'selling_price', 'stock_quantity', 'is_approved', 'created_at')
    list_filter = ('seller', 'is_approved', 'created_at')
    search_fields = ('name_en', 'name_ar', 'code', 'description')
    readonly_fields = ('code', 'created_at', 'updated_at', 'approved_at')
    fieldsets = (
        ('Basic Information', {
            'fields': ('name_en', 'name_ar', 'code', 'description', 'image')
        }),
        ('Pricing & Stock', {
            'fields': ('selling_price', 'purchase_price', 'stock_quantity')
        }),
        ('Sales & Links', {
            'fields': ('product_link', 'seller')
        }),
        ('Approval Status', {
            'fields': ('is_approved', 'approved_by', 'approved_at')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    actions = ['approve_products', 'reject_products']
    
    def approve_products(self, request, queryset):
        from django.utils import timezone
        updated = 0
        
        for product in queryset:
            if not product.is_approved:
                product.is_approved = True
                product.approved_by = request.user
                product.approved_at = timezone.now()
                product.save()
                
                # Create notification for seller (handled by signals)
                pass
                
                updated += 1
        
        self.message_user(request, f'{updated} products have been approved.')
    approve_products.short_description = "Approve selected products"
    
    def reject_products(self, request, queryset):
        updated = 0
        
        for product in queryset:
            if product.is_approved:
                product.is_approved = False
                product.approved_by = None
                product.approved_at = None
                product.save()
                
                # Create notification for seller (handled by signals)
                pass
                
                updated += 1
        
        self.message_user(request, f'{updated} products have been rejected.')
    reject_products.short_description = "Reject selected products"

@admin.register(SalesChannel)
class SalesChannelAdmin(admin.ModelAdmin):
    list_display = ('name_en', 'url', 'seller', 'country')
    list_filter = ('country', 'seller')
    search_fields = ('name_en', 'name_ar', 'url')
    fieldsets = (
        ('Channel Information', {
            'fields': ('name_en', 'name_ar', 'url', 'country')
        }),
        ('Seller & API', {
            'fields': ('seller', 'api_key', 'api_secret')
        })
    )
