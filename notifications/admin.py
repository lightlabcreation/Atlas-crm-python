from django.contrib import admin
from .models import Notification

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'notification_type', 'priority', 'is_read', 'created_at')
    list_filter = ('notification_type', 'priority', 'is_read', 'is_archived', 'created_at', 'target_role')
    search_fields = ('title', 'message', 'user__first_name', 'user__last_name', 'user__email')
    list_editable = ('is_read', 'is_archived')
    readonly_fields = ('created_at', 'updated_at', 'read_at')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'message', 'notification_type', 'priority')
        }),
        ('User & Targeting', {
            'fields': ('user', 'target_role')
        }),
        ('Content & Metadata', {
            'fields': ('related_object_type', 'related_object_id', 'related_url')
        }),
        ('Status & Tracking', {
            'fields': ('is_read', 'is_archived', 'read_at')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'expires_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')
    
    def mark_as_read(self, request, queryset):
        from django.utils import timezone
        updated = queryset.update(is_read=True, read_at=timezone.now())
        self.message_user(request, f'{updated} notifications marked as read.')
    mark_as_read.short_description = "Mark selected notifications as read"
    
    def mark_as_unread(self, request, queryset):
        updated = queryset.update(is_read=False, read_at=None)
        self.message_user(request, f'{updated} notifications marked as unread.')
    mark_as_unread.short_description = "Mark selected notifications as unread"
    
    def archive_notifications(self, request, queryset):
        updated = queryset.update(is_archived=True)
        self.message_user(request, f'{updated} notifications archived.')
    archive_notifications.short_description = "Archive selected notifications"
    
    def unarchive_notifications(self, request, queryset):
        updated = queryset.update(is_archived=False)
        self.message_user(request, f'{updated} notifications unarchived.')
    unarchive_notifications.short_description = "Unarchive selected notifications"
    
    actions = [mark_as_read, mark_as_unread, archive_notifications, unarchive_notifications]
