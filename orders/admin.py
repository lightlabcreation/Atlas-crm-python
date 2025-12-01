from django.contrib import admin
from .models import Order, OrderItem, OrderWorkflowLog

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_code', 'customer', 'status', 'workflow_status', 'seller_email', 'agent', 'total_price_aed', 'date')
    list_filter = ('status', 'workflow_status', 'seller_email', 'agent', 'date')
    search_fields = ('order_code', 'customer', 'customer_phone', 'seller_email')
    readonly_fields = ('order_code', 'created_at', 'updated_at', 'assigned_at')
    inlines = [OrderItemInline]
    actions = ['assign_to_agent', 'unassign_agent', 'change_seller']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('order_code', 'customer', 'customer_phone', 'date', 'status')
        }),
        ('Workflow Status', {
            'fields': ('workflow_status',)
        }),
        ('Product Details', {
            'fields': ('product', 'quantity', 'price_per_unit')
        }),
        ('Seller Information', {
            'fields': ('seller_email', 'store_link', 'seller')
        }),
        ('Call Center Assignment', {
            'fields': ('agent', 'assigned_at')
        }),
        ('Escalation Information', {
            'fields': ('escalated_to_manager', 'escalated_at', 'escalated_by', 'escalation_reason'),
            'classes': ('collapse',)
        }),
        ('Shipping Information', {
            'fields': ('shipping_address', 'city', 'state', 'zip_code', 'country')
        }),
        ('Notes', {
            'fields': ('notes', 'internal_notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def assign_to_agent(self, request, queryset):
        from django.utils import timezone
        # Get available agents (users with Call Center role)
        from users.models import User
        agents = User.objects.filter(user_roles__role__name='Call Center Agent', user_roles__is_active=True).distinct()
        
        if not agents.exists():
            self.message_user(request, 'No call center agents found. Please create users with Call Center role.')
            return
        
        # Assign orders to agents in round-robin fashion
        agent_list = list(agents)
        for i, order in enumerate(queryset):
            agent = agent_list[i % len(agent_list)]
            order.agent = agent
            order.assigned_at = timezone.now()
            order.save()
        
        self.message_user(request, f'{queryset.count()} orders have been assigned to call center agents.')
    assign_to_agent.short_description = "Assign orders to call center agents"
    
    def unassign_agent(self, request, queryset):
        updated = queryset.update(agent=None, assigned_at=None)
        self.message_user(request, f'{queryset.count()} orders have been unassigned from agents.')
    unassign_agent.short_description = "Unassign orders from agents"
    
    def change_seller(self, request, queryset):
        from django.contrib import messages
        from django.shortcuts import render
        from users.models import User
        
        if 'apply' in request.POST:
            new_seller_id = request.POST.get('new_seller')
            if new_seller_id:
                try:
                    new_seller = User.objects.get(id=new_seller_id)
                    updated_count = 0
                    
                    for order in queryset:
                        old_seller = order.seller
                        order.seller = new_seller
                        order.seller_email = new_seller.email
                        order.save()
                        
                        # Create workflow log
                        OrderWorkflowLog.objects.create(
                            order=order,
                            from_status=order.workflow_status,
                            to_status=order.workflow_status,
                            user=request.user,
                            notes=f'Seller changed from {old_seller.get_full_name() if old_seller else "None"} to {new_seller.get_full_name()}'
                        )
                        updated_count += 1
                    
                    self.message_user(request, f'Successfully changed seller for {updated_count} orders to {new_seller.get_full_name()}.')
                    return
                except User.DoesNotExist:
                    messages.error(request, 'Selected seller not found.')
            else:
                messages.error(request, 'Please select a seller.')
        
        # Get all sellers (users with Seller role)
        sellers = User.objects.filter(user_roles__role__name='Seller', user_roles__is_active=True).distinct().order_by('first_name', 'last_name')
        
        context = {
            'orders': queryset,
            'sellers': sellers,
            'action_name': 'change_seller',
            'title': 'Change Seller for Selected Orders'
        }
        
        return render(request, 'admin/change_seller.html', context)
    change_seller.short_description = "Change seller for selected orders"

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'product', 'quantity', 'price', 'total_price_aed')
    list_filter = ('order__status',)
    search_fields = ('order__order_code', 'product__name')

@admin.register(OrderWorkflowLog)
class OrderWorkflowLogAdmin(admin.ModelAdmin):
    list_display = ('order', 'from_status', 'to_status', 'user', 'timestamp')
    list_filter = ('from_status', 'to_status', 'timestamp')
    search_fields = ('order__order_code', 'user__first_name', 'user__last_name', 'user__email', 'notes')
    readonly_fields = ('timestamp',)
    ordering = ('-timestamp',)
