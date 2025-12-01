from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

User = get_user_model()

class Notification(models.Model):
    """Universal notification model for all users and roles"""
    
    NOTIFICATION_TYPES = (
        ('product_approved', 'Product Approved'),
        ('product_rejected', 'Product Rejected'),
        ('product_pending', 'Product Pending Approval'),
        ('product_deleted', 'Product Deleted'),
        ('new_order', 'New Order'),
        ('order_status_changed', 'Order Status Changed'),
        ('order_approved', 'Order Approved'),
        ('order_rejected', 'Order Rejected'),
        ('inventory_low', 'Low Inventory'),
        ('inventory_out', 'Out of Stock'),
        ('user_approved', 'User Account Approved'),
        ('user_rejected', 'User Account Rejected'),
        ('system', 'System Notification'),
        ('workflow_update', 'Workflow Update'),
        ('delivery_update', 'Delivery Update'),
        ('payment_received', 'Payment Received'),
        ('payment_failed', 'Payment Failed'),
        ('data_export', 'Data Export'),
        ('data_import', 'Data Import'),
    )
    
    PRIORITY_LEVELS = (
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    )
    
    # Basic notification info
    title = models.CharField(max_length=255, verbose_name=_('Title'))
    message = models.TextField(verbose_name=_('Message'))
    notification_type = models.CharField(max_length=30, choices=NOTIFICATION_TYPES, default='system', verbose_name=_('Type'))
    priority = models.CharField(max_length=10, choices=PRIORITY_LEVELS, default='medium', verbose_name=_('Priority'))
    
    # User and role targeting
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_notifications', verbose_name=_('User'))
    target_role = models.CharField(max_length=50, blank=True, null=True, verbose_name=_('Target Role'))
    
    # Content and metadata
    related_object_type = models.CharField(max_length=50, blank=True, null=True, verbose_name=_('Related Object Type'))
    related_object_id = models.PositiveIntegerField(blank=True, null=True, verbose_name=_('Related Object ID'))
    related_url = models.URLField(blank=True, null=True, verbose_name=_('Related URL'))
    
    # Status and tracking
    is_read = models.BooleanField(default=False, verbose_name=_('Is Read'))
    is_archived = models.BooleanField(default=False, verbose_name=_('Is Archived'))
    read_at = models.DateTimeField(blank=True, null=True, verbose_name=_('Read At'))
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Created At'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Updated At'))
    expires_at = models.DateTimeField(blank=True, null=True, verbose_name=_('Expires At'))
    
    class Meta:
        verbose_name = _('Notification')
        verbose_name_plural = _('Notifications')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read', 'created_at']),
            models.Index(fields=['notification_type', 'created_at']),
            models.Index(fields=['target_role', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.user.get_full_name() or self.user.email}"
    
    @property
    def is_expired(self):
        """Check if notification has expired"""
        if self.expires_at:
            from django.utils import timezone
            return timezone.now() > self.expires_at
        return False
    
    @property
    def age(self):
        """Get notification age in human readable format"""
        from django.utils import timezone
        from datetime import timedelta
        
        now = timezone.now()
        age = now - self.created_at
        
        if age.days > 0:
            return f"{age.days} day{'s' if age.days != 1 else ''} ago"
        elif age.seconds > 3600:
            hours = age.seconds // 3600
            return f"{hours} hour{'s' if hours != 1 else ''} ago"
        elif age.seconds > 60:
            minutes = age.seconds // 60
            return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
        else:
            return "Just now"
    
    def mark_as_read(self):
        """Mark notification as read"""
        from django.utils import timezone
        
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])
    
    def mark_as_unread(self):
        """Mark notification as unread"""
        self.is_read = False
        self.read_at = None
        self.save(update_fields=['is_read', 'read_at'])
    
    def archive(self):
        """Archive notification"""
        self.is_archived = True
        self.save(update_fields=['is_archived'])
    
    def unarchive(self):
        """Unarchive notification"""
        self.is_archived = False
        self.save(update_fields=['is_archived'])
    
    @classmethod
    def create_notification(cls, user, title, message, notification_type='system', priority='medium', 
                          target_role=None, related_object_type=None, related_object_id=None, 
                          related_url=None, expires_at=None):
        """Create a new notification"""
        return cls.objects.create(
            user=user,
            title=title,
            message=message,
            notification_type=notification_type,
            priority=priority,
            target_role=target_role,
            related_object_type=related_object_type,
            related_object_id=related_object_id,
            related_url=related_url,
            expires_at=expires_at
        )
    
    @classmethod
    def create_bulk_notifications(cls, users, title, message, notification_type='system', priority='medium',
                                target_role=None, related_object_type=None, related_object_id=None,
                                related_url=None, expires_at=None):
        """Create notifications for multiple users"""
        notifications = []
        for user in users:
            notification = cls(
                user=user,
                title=title,
                message=message,
                notification_type=notification_type,
                priority=priority,
                target_role=target_role,
                related_object_type=related_object_type,
                related_object_id=related_object_id,
                related_url=related_url,
                expires_at=expires_at
            )
            notifications.append(notification)
        
        return cls.objects.bulk_create(notifications)
    
    @classmethod
    def get_user_notifications(cls, user, unread_only=False, limit=None, include_expired=False):
        """Get notifications for a specific user"""
        queryset = cls.objects.filter(user=user, is_archived=False)
        
        if unread_only:
            queryset = queryset.filter(is_read=False)
        
        if not include_expired:
            from django.utils import timezone
            queryset = queryset.filter(
                models.Q(expires_at__isnull=True) | models.Q(expires_at__gt=timezone.now())
            )
        
        if limit:
            queryset = queryset[:limit]
        
        return queryset
    
    @classmethod
    def get_role_notifications(cls, role, unread_only=False, limit=None, include_expired=False):
        """Get notifications for a specific role"""
        queryset = cls.objects.filter(target_role=role, is_archived=False)
        
        if unread_only:
            queryset = queryset.filter(is_read=False)
        
        if not include_expired:
            from django.utils import timezone
            queryset = queryset.filter(
                models.Q(expires_at__isnull=True) | models.Q(expires_at__gt=timezone.now())
            )
        
        if limit:
            queryset = queryset[:limit]
        
        return queryset
