# orders/models.py
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
import uuid

def generate_order_code():
    """Generate a shorter order code with # prefix"""
    from django.db.utils import OperationalError, ProgrammingError
    from django.utils import timezone
    import random

    today = timezone.now().date()
    date_part = f"{today.year % 100:02d}{today.month:02d}{today.day:02d}"

    try:
        from .models import Order 

       
        existing_orders_today = Order.objects.filter(
            order_code__startswith=f"#{date_part}"
        ).count()
    except (OperationalError, ProgrammingError):
      
        existing_orders_today = 0

    order_number = existing_orders_today + 1
    code = f"#{date_part}{order_number:03d}"

    try:
        while Order.objects.filter(order_code=code).exists():
            order_number += 1
            code = f"#{date_part}{order_number:03d}"
    except (OperationalError, ProgrammingError):
        pass

    return code

class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', _('Pending')),
        ('processing', _('Processing')),
        ('confirmed', _('Confirmed')),
        ('packaged', _('Packaged')),
        ('shipped', _('Shipped')),
        ('delivered', _('Delivered')),
        ('cancelled', _('Cancelled')),
        ('returned', _('Returned')),
        # Call center specific statuses
        ('no_answer_1st', _('No Answer - 1st Attempt')),
        ('no_answer_2nd', _('No Answer - 2nd Attempt')),
        ('no_answer_final', _('No Answer - Final Attempt')),
        ('postponed', _('Postponed')),
        ('invalid_number', _('Invalid Number')),
        ('call_back_later', _('Call Back Later')),
        ('escalate_manager', _('Escalate to Manager')),
    ]

    # Workflow status choices
    WORKFLOW_STATUS_CHOICES = [
        ('seller_submitted', _('Seller Submitted')),
        ('callcenter_review', _('Call Center Review')),
        ('callcenter_approved', _('Call Center Approved')),
        ('pick_and_pack', _('Pick and Pack')),
        ('stockkeeper_approved', _('Stock Keeper Approved')),
        ('packaging_in_progress', _('Packaging In Progress')),
        ('packaging_completed', _('Packaging Completed')),
        ('ready_for_delivery', _('Ready for Delivery')),
        ('delivery_in_progress', _('Delivery In Progress')),
        ('delivery_completed', _('Delivery Completed')),
        ('cancelled', _('Cancelled')),
    ]

    order_code = models.CharField(max_length=50, unique=True, verbose_name=_('Order Code'), default=generate_order_code)
    customer = models.CharField(max_length=255, verbose_name=_('Customer'), help_text=_('Customer full name'), default='Unknown Customer')
    date = models.DateTimeField(default=timezone.now, verbose_name=_('Order Date'))
    # Deprecated direct product relationship - use OrderItem instead
    product = models.ForeignKey('sellers.Product', on_delete=models.PROTECT, related_name='direct_orders', verbose_name=_('Legacy Product'), null=True, blank=True)
    quantity = models.PositiveIntegerField(verbose_name=_('Quantity'), default=1)
    price_per_unit = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_('Price Per Unit (AED)'), default=0, help_text=_('Price in UAE Dirhams'))
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name=_('Status'))
    
    # Workflow tracking
    workflow_status = models.CharField(max_length=30, choices=WORKFLOW_STATUS_CHOICES, default='seller_submitted', verbose_name=_('Workflow Status'))
    
    # Additional fields for detailed view
    customer_phone = models.CharField(max_length=20, blank=True, verbose_name=_('Customer Phone'))
    seller_email = models.EmailField(blank=True, verbose_name=_('Seller Email'))
    seller = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='orders', verbose_name=_('Seller'), null=True, blank=True)
    store_link = models.URLField(verbose_name=_('Store Link'), help_text=_('Product link is required'))
    
    # Shipping information
    street_address = models.CharField(max_length=255, blank=True, verbose_name=_('Street Address'), help_text=_('Street address and building number'))
    shipping_address = models.TextField(blank=True, verbose_name=_('Shipping Address'))
    city = models.CharField(max_length=100, blank=True, verbose_name=_('City'))
    state = models.CharField(max_length=100, blank=True, verbose_name=_('Area'), help_text=_('Area/Region within city'))
    zip_code = models.CharField(max_length=20, blank=True, verbose_name=_('ZIP Code'))
    country = models.CharField(max_length=100, blank=True, verbose_name=_('Country'))
    delivery_area = models.CharField(max_length=100, blank=True, verbose_name=_('Delivery Area'), help_text=_('Confirmed delivery area by call center'))
    
    # UAE specific fields
    emirate = models.CharField(max_length=50, blank=True, verbose_name=_('Emirate'), help_text=_('UAE Emirate'))
    region = models.CharField(max_length=50, blank=True, verbose_name=_('Region'), help_text=_('UAE Region within Emirate'))
    
    # Order details
    notes = models.TextField(blank=True, verbose_name=_('Order Notes'))
    internal_notes = models.TextField(blank=True, verbose_name=_('Internal Notes'))
    
    # Call center agent assignment
    agent = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_orders', verbose_name=_('Call Center Agent'))
    assigned_at = models.DateTimeField(null=True, blank=True, verbose_name=_('Assigned At'))
    
    # Manager escalation tracking
    escalated_to_manager = models.BooleanField(default=False, verbose_name=_('Escalated to Manager'))
    escalated_at = models.DateTimeField(null=True, blank=True, verbose_name=_('Escalated At'))
    escalated_by = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='escalated_orders', verbose_name=_('Escalated By'))
    escalation_reason = models.TextField(blank=True, verbose_name=_('Escalation Reason'), help_text=_('Reason for escalating to manager'))
    postponed_until = models.DateTimeField(null=True, blank=True, verbose_name=_('Postponed Until'), help_text=_('Date and time when order should be processed'))
    call_back_time = models.DateTimeField(null=True, blank=True, verbose_name=_('Call Back Time'), help_text=_('Date and time for call back set by call center'))
    no_answer_time = models.DateTimeField(null=True, blank=True, verbose_name=_('No Answer Time'), help_text=_('Date and time for next call attempt when customer did not answer'))
    
    # Tracking and delivery information
    tracking_number = models.CharField(max_length=100, blank=True, verbose_name=_('Tracking Number'))
    cancelled_reason = models.TextField(blank=True, verbose_name=_('Cancellation Reason'))
    
    # Timestamps
    created_at = models.DateTimeField(default=timezone.now, verbose_name=_('Created At'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Updated At'))

    class Meta:
        verbose_name = _('Order')
        verbose_name_plural = _('Orders')
        ordering = ['-date']

    def __str__(self):
        return f"{self.order_code} - {self.customer}"

    @property
    def total_price(self):
        """Calculate total price in AED"""
        # If we have order items, calculate based on them
        if hasattr(self, 'items') and self.items.exists():
            return sum(item.total_price for item in self.items.all())
        # Fall back to legacy calculation
        return self.quantity * self.price_per_unit

    @property
    def total_price_aed(self):
        """Get total price formatted in AED"""
        return f"AED {self.total_price:,.2f}"

    @property
    def price_per_unit_aed(self):
        """Get price per unit formatted in AED"""
        return f"AED {self.price_per_unit:,.2f}"

    def advance_workflow(self, new_status, user, notes=""):
        """Advance the order workflow to the next stage"""
        workflow_progression = {
            'seller_submitted': 'callcenter_review',
            'callcenter_review': 'callcenter_approved',
            'callcenter_approved': 'packaging_in_progress',
            'packaging_in_progress': 'packaging_completed',
            'packaging_completed': 'ready_for_delivery',
            'ready_for_delivery': 'delivery_in_progress',
            'delivery_in_progress': 'delivery_completed',
        }
        
        if self.workflow_status in workflow_progression:
            self.workflow_status = workflow_progression[self.workflow_status]
            self.save()
            
            # Create workflow log entry
            OrderWorkflowLog.objects.create(
                order=self,
                from_status=workflow_progression[self.workflow_status],
                to_status=new_status,
                user=user,
                notes=notes
            )
            
            return True
        return False

class OrderWorkflowLog(models.Model):
    """Log of order workflow transitions"""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='workflow_logs')
    from_status = models.CharField(max_length=30, choices=Order.WORKFLOW_STATUS_CHOICES)
    to_status = models.CharField(max_length=30, choices=Order.WORKFLOW_STATUS_CHOICES)
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, verbose_name=_('User who made the change'))
    notes = models.TextField(blank=True, verbose_name=_('Notes about the transition'))
    timestamp = models.DateTimeField(default=timezone.now, verbose_name=_('Timestamp'))
    
    class Meta:
        verbose_name = _('Order Workflow Log')
        verbose_name_plural = _('Order Workflow Logs')
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.order.order_code} - {self.from_status} → {self.to_status} by {self.user.get_full_name() or self.user.email}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey('sellers.Product', on_delete=models.CASCADE)
    quantity = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_('Price (AED)'))
    
    class Meta:
        verbose_name = _('Order Item')
        verbose_name_plural = _('Order Items')
    
    def __str__(self):
        return f"{self.order.order_code} - {self.product.name_en} x {self.quantity}"
    
    @property
    def total_price(self):
        return self.quantity * self.price
    
    @property
    def total_price_aed(self):
        return f"AED {self.total_price:,.2f}"


class StatusLog(models.Model):
    """Track status changes for orders"""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='status_logs', verbose_name=_('Order'))
    old_status = models.CharField(max_length=50, verbose_name=_('Old Status'), blank=True, null=True)
    new_status = models.CharField(max_length=50, verbose_name=_('New Status'))
    changed_by = models.ForeignKey('users.User', on_delete=models.CASCADE, verbose_name=_('Changed By'))
    change_reason = models.TextField(blank=True, null=True, verbose_name=_('Change Reason'))
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name=_('Timestamp'))
    is_manager_change = models.BooleanField(default=False, verbose_name=_('Is Manager Change'))
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = _('Status Log')
        verbose_name_plural = _('Status Logs')
    
    def __str__(self):
        return f"{self.order.order_code} - {self.old_status} → {self.new_status} by {self.changed_by.username}"