# stock_keeper/models.py
from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.utils import timezone
import qrcode
from io import BytesIO
from django.core.files import File
from PIL import Image
import random
import string

User = get_user_model()

def generate_tracking_number():
    """Generate a unique tracking number."""
    return f"TRK-{''.join(random.choices(string.ascii_uppercase + string.digits, k=8))}"

def generate_barcode():
    """Generate a unique barcode."""
    return f"BAR-{''.join(random.choices(string.digits, k=12))}"



class WarehouseInventory(models.Model):
    """Track product quantities in specific warehouses."""
    product = models.ForeignKey('sellers.Product', on_delete=models.CASCADE, related_name='warehouse_inventory')
    warehouse = models.ForeignKey('inventory.Warehouse', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=0, validators=[MinValueValidator(0)])
    location_code = models.CharField(max_length=50, blank=True, verbose_name="Storage Location")
    min_stock_level = models.PositiveIntegerField(default=5, verbose_name="Minimum Stock Level")
    max_stock_level = models.PositiveIntegerField(default=100, verbose_name="Maximum Stock Level")
    last_movement = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('product', 'warehouse')
        verbose_name = "Warehouse Inventory"
        verbose_name_plural = "Warehouse Inventory"

    def __str__(self):
        return f"{self.product.name_en} - {self.warehouse.name} ({self.quantity})"

    @property
    def is_low_stock(self):
        """Check if stock is below minimum level."""
        return self.quantity <= self.min_stock_level

    @property
    def stock_status(self):
        """Get stock status description."""
        if self.quantity == 0:
            return "Out of Stock"
        elif self.is_low_stock:
            return "Low Stock"
        elif self.quantity >= self.max_stock_level:
            return "Overstocked"
        else:
            return "Normal"

class InventoryMovement(models.Model):
    """Track all inventory movements with detailed information."""
    MOVEMENT_TYPES = (
        ('stock_in', 'Stock In'),
        ('stock_out', 'Stock Out'),
        ('transfer', 'Transfer'),
        ('adjustment', 'Adjustment'),
        ('return', 'Return'),
        ('damage', 'Damage'),
        ('expiry', 'Expiry'),
    )
    
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )
    
    tracking_number = models.CharField(max_length=50, unique=True, default=generate_tracking_number)
    movement_type = models.CharField(max_length=20, choices=MOVEMENT_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Product and quantity details
    product = models.ForeignKey('sellers.Product', on_delete=models.CASCADE, related_name='stock_keeper_movements')
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    
    # Warehouse details
    from_warehouse = models.ForeignKey('inventory.Warehouse', on_delete=models.CASCADE, related_name='stock_keeper_outgoing_movements', null=True, blank=True)
    to_warehouse = models.ForeignKey('inventory.Warehouse', on_delete=models.CASCADE, related_name='stock_keeper_incoming_movements', null=True, blank=True)
    from_location = models.CharField(max_length=50, blank=True)
    to_location = models.CharField(max_length=50, blank=True)
    
    # Reference information
    reference_number = models.CharField(max_length=100, blank=True)  # Order number, PO, etc.
    reference_type = models.CharField(max_length=50, blank=True)  # Order, Purchase, Transfer, etc.
    
    # User and timing
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='movements_created')
    processed_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='movements_processed', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    # Additional details
    reason = models.CharField(max_length=200, blank=True)
    notes = models.TextField(blank=True)
    condition = models.CharField(max_length=50, default='good')  # good, damaged, defective

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Inventory Movement"
        verbose_name_plural = "Inventory Movements"

    def __str__(self):
        return f"{self.get_movement_type_display()} - {self.product.name_en} ({self.quantity})"

    def save(self, *args, **kwargs):
        if self.status == 'completed' and not self.processed_at:
            self.processed_at = timezone.now()
        super().save(*args, **kwargs)

    @property
    def movement_description(self):
        """Get a human-readable description of the movement."""
        if self.movement_type == 'transfer':
            return f"Transfer {self.quantity} units of {self.product.name_en} from {self.from_warehouse.name} to {self.to_warehouse.name}"
        elif self.movement_type == 'stock_in':
            return f"Received {self.quantity} units of {self.product.name_en} at {self.to_warehouse.name}"
        elif self.movement_type == 'stock_out':
            return f"Shipped {self.quantity} units of {self.product.name_en} from {self.from_warehouse.name}"
        else:
            return f"{self.get_movement_type_display()} - {self.quantity} units of {self.product.name_en}"

class TrackingNumber(models.Model):
    """Manage tracking numbers and QR codes for inventory items."""
    tracking_number = models.CharField(max_length=50, unique=True, default=generate_tracking_number)
    product = models.ForeignKey('sellers.Product', on_delete=models.CASCADE, related_name='stock_keeper_tracking_numbers')
    warehouse = models.ForeignKey('inventory.Warehouse', on_delete=models.CASCADE)
    qr_code = models.ImageField(upload_to='qr_codes/', blank=True, null=True)
    barcode = models.CharField(max_length=100, unique=True, default=generate_barcode)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Tracking Number"
        verbose_name_plural = "Tracking Numbers"

    def __str__(self):
        return f"{self.tracking_number} - {self.product.name_en}"

    def save(self, *args, **kwargs):
        if not self.qr_code:
            self.generate_qr_code()
        super().save(*args, **kwargs)

    def generate_qr_code(self):
        """Generate QR code for the tracking number."""
        if self.tracking_number:
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(self.tracking_number)
            qr.make(fit=True)

            img = qr.make_image(fill_color="black", back_color="white")
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            
            filename = f"qr_{self.tracking_number}.png"
            self.qr_code.save(filename, File(buffer), save=False)

class StockKeeperSession(models.Model):
    """Track stock keeper work sessions."""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    warehouse = models.ForeignKey('inventory.Warehouse', on_delete=models.CASCADE)
    shift_start = models.DateTimeField(auto_now_add=True)
    shift_end = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    tasks_completed = models.PositiveIntegerField(default=0)
    items_processed = models.PositiveIntegerField(default=0)
    scan_count = models.PositiveIntegerField(default=0)
    session_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = "Stock Keeper Session"
        verbose_name_plural = "Stock Keeper Sessions"
        ordering = ['-shift_start']

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.warehouse.name} ({self.shift_start.date()})"

    @property
    def duration(self):
        """Get session duration in minutes."""
        if self.shift_end:
            return int((self.shift_end - self.shift_start).total_seconds() / 60)
        elif self.is_active:
            return int((timezone.now() - self.shift_start).total_seconds() / 60)
        return 0

    @property
    def movements_count(self):
        """Get number of movements processed in this session."""
        return self.user.movements_processed.filter(
            processed_at__gte=self.shift_start,
            processed_at__lte=self.shift_end if self.shift_end else timezone.now()
        ).count()

class StockAlert(models.Model):
    """Manage stock alerts and notifications."""
    ALERT_TYPES = (
        ('low_stock', 'Low Stock'),
        ('out_of_stock', 'Out of Stock'),
        ('overstocked', 'Overstocked'),
        ('expiry', 'Expiry Warning'),
        ('damage', 'Damage Report'),
        ('transfer_request', 'Transfer Request'),
    )
    
    PRIORITY_CHOICES = (
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    )
    
    alert_type = models.CharField(max_length=20, choices=ALERT_TYPES)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    product = models.ForeignKey('sellers.Product', on_delete=models.CASCADE, related_name='stock_keeper_alerts')
    warehouse = models.ForeignKey('inventory.Warehouse', on_delete=models.CASCADE)
    message = models.TextField()
    is_resolved = models.BooleanField(default=False)
    resolved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Stock Alert"
        verbose_name_plural = "Stock Alerts"

    def __str__(self):
        return f"{self.get_alert_type_display()} - {self.product.name_en} ({self.warehouse.name})"

    def resolve(self, user):
        """Resolve the alert."""
        self.is_resolved = True
        self.resolved_by = user
        self.resolved_at = timezone.now()
        self.save()

class StockKeeperTask(models.Model):
    """Task assignments for stock keepers."""
    TASK_TYPES = (
        ('receive', 'Receive Stock'),
        ('ship', 'Ship Orders'),
        ('transfer', 'Transfer Stock'),
        ('count', 'Cycle Count'),
        ('adjustment', 'Stock Adjustment'),
        ('maintenance', 'Maintenance'),
    )
    
    PRIORITY_CHOICES = (
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    )
    
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )
    
    task_type = models.CharField(max_length=20, choices=TASK_TYPES)
    assigned_to = models.ForeignKey(User, on_delete=models.CASCADE, related_name='assigned_tasks')
    warehouse = models.ForeignKey('inventory.Warehouse', on_delete=models.CASCADE)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='normal')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    reference_id = models.IntegerField(null=True, blank=True)  # Links to orders, transfers, etc.
    due_date = models.DateTimeField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    estimated_duration = models.PositiveIntegerField(null=True, blank=True)  # in minutes
    actual_duration = models.PositiveIntegerField(null=True, blank=True)  # in minutes
    completion_notes = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_tasks')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Stock Keeper Task"
        verbose_name_plural = "Stock Keeper Tasks"
    
    def __str__(self):
        return f"{self.title} - {self.assigned_to.get_full_name()}"
    
    def start_task(self):
        """Start the task."""
        self.status = 'in_progress'
        self.started_at = timezone.now()
        self.save()
    
    def complete_task(self, notes=''):
        """Complete the task."""
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.completion_notes = notes
        if self.started_at:
            self.actual_duration = int((self.completed_at - self.started_at).total_seconds() / 60)
        self.save()

class BarcodeScanHistory(models.Model):
    """Track barcode scan history for audit and analytics."""
    SCAN_TYPES = (
        ('product_lookup', 'Product Lookup'),
        ('stock_update', 'Stock Update'),
        ('receive', 'Receive Stock'),
        ('ship', 'Ship Orders'),
        ('transfer', 'Transfer Stock'),
        ('count', 'Cycle Count'),
    )
    
    SCAN_RESULTS = (
        ('success', 'Success'),
        ('not_found', 'Not Found'),
        ('error', 'Error'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    warehouse = models.ForeignKey('inventory.Warehouse', on_delete=models.CASCADE)
    scan_type = models.CharField(max_length=20, choices=SCAN_TYPES)
    barcode_data = models.CharField(max_length=255)
    product = models.ForeignKey('sellers.Product', on_delete=models.CASCADE, null=True, blank=True)
    task = models.ForeignKey(StockKeeperTask, on_delete=models.CASCADE, null=True, blank=True)
    scan_result = models.CharField(max_length=20, choices=SCAN_RESULTS)
    quantity_change = models.IntegerField(default=0)
    location_code = models.CharField(max_length=50, blank=True)
    notes = models.TextField(blank=True)
    scan_timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-scan_timestamp']
        verbose_name = "Barcode Scan History"
        verbose_name_plural = "Barcode Scan History"
    
    def __str__(self):
        return f"{self.barcode_data} - {self.get_scan_type_display()} ({self.scan_timestamp})"

class PhysicalCountRecord(models.Model):
    """Record physical inventory counts for cycle counting."""
    CONDITION_STATUS = (
        ('good', 'Good'),
        ('damaged', 'Damaged'),
        ('defective', 'Defective'),
        ('missing', 'Missing'),
    )
    
    count_session_id = models.CharField(max_length=50)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    warehouse = models.ForeignKey('inventory.Warehouse', on_delete=models.CASCADE)
    product = models.ForeignKey('sellers.Product', on_delete=models.CASCADE)
    location_code = models.CharField(max_length=50, blank=True)
    system_quantity = models.PositiveIntegerField(null=True, blank=True)
    counted_quantity = models.PositiveIntegerField(null=True, blank=True)
    variance = models.IntegerField(null=True, blank=True)  # Generated field: counted_quantity - system_quantity
    condition_status = models.CharField(max_length=20, choices=CONDITION_STATUS, default='good')
    count_notes = models.TextField(blank=True)
    count_timestamp = models.DateTimeField(auto_now_add=True)
    verified_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='verified_counts')
    verification_timestamp = models.DateTimeField(null=True, blank=True)
    adjustment_applied = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-count_timestamp']
        verbose_name = "Physical Count Record"
        verbose_name_plural = "Physical Count Records"
    
    def __str__(self):
        counted = self.counted_quantity if self.counted_quantity is not None else 'N/A'
        system = self.system_quantity if self.system_quantity is not None else 'N/A'
        return f"{self.product.name_en} - {counted} (System: {system})"
    
    def save(self, *args, **kwargs):
        # Calculate variance if both quantities are available
        if self.counted_quantity is not None and self.system_quantity is not None:
            self.variance = self.counted_quantity - self.system_quantity
        elif self.counted_quantity is not None and self.system_quantity is None:
            # If only counted quantity is available, variance is the counted quantity
            self.variance = self.counted_quantity
        else:
            self.variance = None
        super().save(*args, **kwargs)
    
    @property
    def variance_percentage(self):
        """Get variance as percentage."""
        if self.system_quantity and self.system_quantity > 0 and self.variance is not None:
            return (self.variance / self.system_quantity) * 100
        return 0
