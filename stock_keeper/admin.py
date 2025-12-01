# stock_keeper/admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    Warehouse, WarehouseInventory, InventoryMovement, 
    TrackingNumber, StockKeeperSession, StockAlert,
    StockKeeperTask, BarcodeScanHistory, PhysicalCountRecord
)

@admin.register(Warehouse)
class WarehouseAdmin(admin.ModelAdmin):
    list_display = ['name', 'country', 'zone', 'currency', 'total_items', 'low_stock_items', 'is_active', 'created_at']
    list_filter = ['country', 'zone', 'currency', 'is_active', 'created_at']
    search_fields = ['name', 'country', 'zone', 'contact_person', 'contact_email']
    readonly_fields = ['total_items', 'low_stock_items', 'created_at', 'updated_at']
    ordering = ['name']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'country', 'zone', 'currency')
        }),
        ('Contact Information', {
            'fields': ('contact_person', 'contact_phone', 'contact_email', 'address')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(WarehouseInventory)
class WarehouseInventoryAdmin(admin.ModelAdmin):
    list_display = ['product', 'warehouse', 'quantity', 'location_code', 'stock_status_display', 'is_low_stock', 'last_movement']
    list_filter = ['warehouse', 'is_low_stock', 'last_movement', 'created_at']
    search_fields = ['product__name_en', 'product__name_ar', 'warehouse__name', 'location_code']
    readonly_fields = ['is_low_stock', 'stock_status', 'last_movement', 'created_at', 'updated_at']
    ordering = ['warehouse', 'product']
    
    def stock_status_display(self, obj):
        status_colors = {
            'out_of_stock': 'red',
            'low_stock': 'orange',
            'normal': 'green',
            'overstocked': 'blue'
        }
        color = status_colors.get(obj.stock_status, 'gray')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.stock_status.replace('_', ' ').title()
        )
    stock_status_display.short_description = 'Stock Status'
    
    fieldsets = (
        ('Product & Warehouse', {
            'fields': ('product', 'warehouse')
        }),
        ('Stock Information', {
            'fields': ('quantity', 'location_code', 'min_stock_level', 'max_stock_level')
        }),
        ('Status Information', {
            'fields': ('is_low_stock', 'stock_status', 'last_movement')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(InventoryMovement)
class InventoryMovementAdmin(admin.ModelAdmin):
    list_display = ['tracking_number', 'movement_type', 'product', 'quantity', 'warehouses_display', 'status', 'created_by', 'created_at']
    list_filter = ['movement_type', 'status', 'warehouse', 'created_at', 'processed_at']
    search_fields = ['tracking_number', 'product__name_en', 'reference_number', 'reason']
    readonly_fields = ['tracking_number', 'created_at', 'processed_at', 'movement_description']
    ordering = ['-created_at']
    
    def warehouses_display(self, obj):
        if obj.movement_type == 'transfer':
            return f"{obj.from_warehouse.name} → {obj.to_warehouse.name}"
        elif obj.movement_type == 'stock_in':
            return f"→ {obj.to_warehouse.name}"
        elif obj.movement_type == 'stock_out':
            return f"{obj.from_warehouse.name} →"
        return "-"
    warehouses_display.short_description = 'Warehouses'
    
    fieldsets = (
        ('Movement Information', {
            'fields': ('tracking_number', 'movement_type', 'status', 'product', 'quantity')
        }),
        ('Warehouse Details', {
            'fields': ('from_warehouse', 'to_warehouse', 'from_location', 'to_location')
        }),
        ('Reference Information', {
            'fields': ('reference_number', 'reference_type', 'reason', 'notes')
        }),
        ('User & Timing', {
            'fields': ('created_by', 'processed_by', 'created_at', 'processed_at')
        }),
        ('Additional Details', {
            'fields': ('condition', 'movement_description')
        }),
    )

@admin.register(TrackingNumber)
class TrackingNumberAdmin(admin.ModelAdmin):
    list_display = ['tracking_number', 'product', 'warehouse', 'barcode', 'qr_code_display', 'is_active', 'created_at']
    list_filter = ['warehouse', 'is_active', 'created_at']
    search_fields = ['tracking_number', 'barcode', 'product__name_en']
    readonly_fields = ['tracking_number', 'barcode', 'qr_code_display', 'created_at']
    ordering = ['-created_at']
    
    def qr_code_display(self, obj):
        if obj.qr_code:
            return format_html(
                '<img src="{}" alt="QR Code" style="max-width: 50px; max-height: 50px;" />',
                obj.qr_code.url
            )
        return "No QR Code"
    qr_code_display.short_description = 'QR Code'
    
    fieldsets = (
        ('Tracking Information', {
            'fields': ('tracking_number', 'barcode', 'qr_code_display')
        }),
        ('Product & Warehouse', {
            'fields': ('product', 'warehouse')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

@admin.register(StockKeeperSession)
class StockKeeperSessionAdmin(admin.ModelAdmin):
    list_display = ['user', 'warehouse', 'shift_start', 'shift_end', 'duration_display', 'tasks_completed', 'items_processed', 'is_active']
    list_filter = ['warehouse', 'is_active', 'shift_start', 'shift_end']
    search_fields = ['user__first_name', 'user__last_name', 'user__email', 'warehouse__name']
    readonly_fields = ['duration_display', 'movements_count', 'shift_start', 'created_at']
    ordering = ['-shift_start']
    
    def duration_display(self, obj):
        duration = obj.duration
        if duration:
            hours = duration // 60
            minutes = duration % 60
            return f"{hours}h {minutes}m"
        return "Active"
    duration_display.short_description = 'Duration'
    
    fieldsets = (
        ('Session Information', {
            'fields': ('user', 'warehouse', 'shift_start', 'shift_end', 'is_active')
        }),
        ('Performance Metrics', {
            'fields': ('tasks_completed', 'items_processed', 'scan_count', 'movements_count')
        }),
        ('Notes', {
            'fields': ('session_notes',)
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

@admin.register(StockAlert)
class StockAlertAdmin(admin.ModelAdmin):
    list_display = ['alert_type', 'priority', 'product', 'warehouse', 'is_resolved', 'created_at']
    list_filter = ['alert_type', 'priority', 'warehouse', 'is_resolved', 'created_at']
    search_fields = ['product__name_en', 'warehouse__name', 'message']
    readonly_fields = ['created_at', 'resolved_at']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Alert Information', {
            'fields': ('alert_type', 'priority', 'product', 'warehouse')
        }),
        ('Message', {
            'fields': ('message',)
        }),
        ('Resolution', {
            'fields': ('is_resolved', 'resolved_by', 'resolved_at')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('product', 'warehouse', 'resolved_by')

@admin.register(StockKeeperTask)
class StockKeeperTaskAdmin(admin.ModelAdmin):
    list_display = ['title', 'task_type', 'assigned_to', 'warehouse', 'priority', 'status', 'due_date', 'created_at']
    list_filter = ['task_type', 'priority', 'status', 'warehouse', 'created_at', 'due_date']
    search_fields = ['title', 'description', 'assigned_to__first_name', 'assigned_to__last_name', 'assigned_to__email', 'warehouse__name']
    readonly_fields = ['created_at', 'updated_at', 'started_at', 'completed_at']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Task Information', {
            'fields': ('title', 'description', 'task_type', 'priority', 'status')
        }),
        ('Assignment', {
            'fields': ('assigned_to', 'warehouse', 'created_by')
        }),
        ('Timing', {
            'fields': ('due_date', 'estimated_duration', 'started_at', 'completed_at', 'actual_duration')
        }),
        ('Reference', {
            'fields': ('reference_id',)
        }),
        ('Completion', {
            'fields': ('completion_notes',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(BarcodeScanHistory)
class BarcodeScanHistoryAdmin(admin.ModelAdmin):
    list_display = ['barcode_data', 'scan_type', 'user', 'warehouse', 'scan_result', 'scan_timestamp']
    list_filter = ['scan_type', 'scan_result', 'warehouse', 'scan_timestamp']
    search_fields = ['barcode_data', 'user__first_name', 'user__last_name', 'user__email', 'product__name_en', 'notes']
    readonly_fields = ['scan_timestamp']
    ordering = ['-scan_timestamp']
    
    fieldsets = (
        ('Scan Information', {
            'fields': ('barcode_data', 'scan_type', 'scan_result')
        }),
        ('User & Location', {
            'fields': ('user', 'warehouse')
        }),
        ('Product & Task', {
            'fields': ('product', 'task')
        }),
        ('Details', {
            'fields': ('quantity_change', 'location_code', 'notes')
        }),
        ('Timestamps', {
            'fields': ('scan_timestamp',),
            'classes': ('collapse',)
        }),
    )

@admin.register(PhysicalCountRecord)
class PhysicalCountRecordAdmin(admin.ModelAdmin):
    list_display = ['count_session_id', 'product', 'warehouse', 'system_quantity', 'counted_quantity', 'variance', 'condition_status', 'count_timestamp']
    list_filter = ['condition_status', 'warehouse', 'count_timestamp', 'adjustment_applied']
    search_fields = ['count_session_id', 'product__name_en', 'warehouse__name', 'location_code']
    readonly_fields = ['variance', 'variance_percentage', 'count_timestamp', 'verification_timestamp']
    ordering = ['-count_timestamp']
    
    fieldsets = (
        ('Count Information', {
            'fields': ('count_session_id', 'product', 'warehouse', 'location_code')
        }),
        ('Quantities', {
            'fields': ('system_quantity', 'counted_quantity', 'variance', 'variance_percentage')
        }),
        ('Condition', {
            'fields': ('condition_status', 'count_notes')
        }),
        ('Verification', {
            'fields': ('verified_by', 'verification_timestamp', 'adjustment_applied')
        }),
        ('Timestamps', {
            'fields': ('count_timestamp',),
            'classes': ('collapse',)
        }),
    )

@admin.register(StockKeeperTask)
class StockKeeperTaskAdmin(admin.ModelAdmin):
    list_display = ['title', 'task_type', 'assigned_to', 'warehouse', 'priority', 'status', 'due_date', 'created_at']
    list_filter = ['task_type', 'priority', 'status', 'warehouse', 'created_at', 'due_date']
    search_fields = ['title', 'description', 'assigned_to__first_name', 'assigned_to__last_name', 'assigned_to__email', 'warehouse__name']
    readonly_fields = ['created_at', 'updated_at', 'started_at', 'completed_at']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Task Information', {
            'fields': ('title', 'description', 'task_type', 'priority', 'status')
        }),
        ('Assignment', {
            'fields': ('assigned_to', 'warehouse', 'created_by')
        }),
        ('Timing', {
            'fields': ('due_date', 'estimated_duration', 'started_at', 'completed_at', 'actual_duration')
        }),
        ('Reference', {
            'fields': ('reference_id',)
        }),
        ('Completion', {
            'fields': ('completion_notes',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(BarcodeScanHistory)
class BarcodeScanHistoryAdmin(admin.ModelAdmin):
    list_display = ['barcode_data', 'scan_type', 'user', 'warehouse', 'scan_result', 'scan_timestamp']
    list_filter = ['scan_type', 'scan_result', 'warehouse', 'scan_timestamp']
    search_fields = ['barcode_data', 'user__first_name', 'user__last_name', 'user__email', 'product__name_en', 'notes']
    readonly_fields = ['scan_timestamp']
    ordering = ['-scan_timestamp']
    
    fieldsets = (
        ('Scan Information', {
            'fields': ('barcode_data', 'scan_type', 'scan_result')
        }),
        ('User & Location', {
            'fields': ('user', 'warehouse')
        }),
        ('Product & Task', {
            'fields': ('product', 'task')
        }),
        ('Details', {
            'fields': ('quantity_change', 'location_code', 'notes')
        }),
        ('Timestamps', {
            'fields': ('scan_timestamp',),
            'classes': ('collapse',)
        }),
    )

@admin.register(PhysicalCountRecord)
class PhysicalCountRecordAdmin(admin.ModelAdmin):
    list_display = ['count_session_id', 'product', 'warehouse', 'system_quantity', 'counted_quantity', 'variance', 'condition_status', 'count_timestamp']
    list_filter = ['condition_status', 'warehouse', 'count_timestamp', 'adjustment_applied']
    search_fields = ['count_session_id', 'product__name_en', 'warehouse__name', 'location_code']
    readonly_fields = ['variance', 'variance_percentage', 'count_timestamp', 'verification_timestamp']
    ordering = ['-count_timestamp']
    
    fieldsets = (
        ('Count Information', {
            'fields': ('count_session_id', 'product', 'warehouse', 'location_code')
        }),
        ('Quantities', {
            'fields': ('system_quantity', 'counted_quantity', 'variance', 'variance_percentage')
        }),
        ('Condition', {
            'fields': ('condition_status', 'count_notes')
        }),
        ('Verification', {
            'fields': ('verified_by', 'verification_timestamp', 'adjustment_applied')
        }),
        ('Timestamps', {
            'fields': ('count_timestamp',),
            'classes': ('collapse',)
        }),
    )
