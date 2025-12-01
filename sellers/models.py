from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.db.models import Sum
from inventory.models import InventoryRecord
import uuid
from django.conf import settings

# Import Cloudinary Storage if available
try:
    from cloudinary_storage.storage import MediaCloudinaryStorage
    CLOUDINARY_AVAILABLE = True
except ImportError:
    CLOUDINARY_AVAILABLE = False
    MediaCloudinaryStorage = None

class Seller(models.Model):
    user = models.OneToOneField('users.User', on_delete=models.CASCADE, related_name='seller_profile')
    name = models.CharField(max_length=200, verbose_name=_('Seller Name'))
    phone = models.CharField(max_length=20, verbose_name=_('Phone Number'))
    email = models.EmailField(verbose_name=_('Email'))
    store_link = models.URLField(blank=True, verbose_name=_('Store Link'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Created At'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Updated At'))

    class Meta:
        verbose_name = _('Seller')
        verbose_name_plural = _('Sellers')
        ordering = ['-created_at']

    def __str__(self):
        return self.name

def product_image_path(instance, filename):
    """Generate file path for product images"""
    import os
    from django.utils.text import slugify
    
    # Get file extension
    ext = filename.split('.')[-1]
    
    # Create filename with product name
    if instance.name_en:
        # Use English name if available, otherwise use code
        base_name = slugify(instance.name_en)
    else:
        base_name = instance.code
    
    # If instance has an ID, use it, otherwise use a timestamp
    if instance.id:
        filename = f"{base_name}_{instance.id}.{ext}"
    else:
        import time
        timestamp = int(time.time())
        filename = f"{base_name}_{timestamp}.{ext}"
    
    return os.path.join('products', filename)

def generate_product_code():
    """Generate a unique product code"""
    # Generate a unique code using UUID and timestamp
    import time
    timestamp = int(time.time())
    unique_id = str(uuid.uuid4())[:8].upper()
    return f"SKU-{timestamp}-{unique_id}"

class Product(models.Model):
    name_en = models.CharField(max_length=100, verbose_name=_('Product Name (English)'))
    name_ar = models.CharField(max_length=100, verbose_name=_('Product Name (Arabic)'))
    code = models.CharField(max_length=50, unique=True, editable=False, help_text=_('Auto-generated SKU/Product Code'))
    category = models.CharField(max_length=50, blank=True, null=True, verbose_name=_('Category'))
    description = models.TextField(verbose_name=_('Description'), blank=True, null=True)
    product_variant = models.CharField(max_length=200, blank=True, null=True, verbose_name=_('Product Variant'), help_text=_('e.g., Red Large, Blue Small, etc.'))
    selling_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_('Selling Price'))
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name=_('Purchase Price'))
    stock_quantity = models.PositiveIntegerField(default=0, help_text=_('Current stock quantity'))
    image = models.ImageField(
        upload_to=product_image_path, 
        blank=True, 
        null=True, 
        verbose_name=_('Product Image'),
        storage=MediaCloudinaryStorage() if CLOUDINARY_AVAILABLE else None
    )
    product_link = models.URLField(blank=True, null=True, verbose_name=_('Product Link'))
    seller = models.ForeignKey('users.User', on_delete=models.CASCADE, verbose_name=_('Seller'))
    created_by = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='created_products', verbose_name=_('Created By'), null=True, blank=True)
    is_approved = models.BooleanField(default=False, verbose_name=_('Admin Approval'))
    approved_by = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_products', verbose_name=_('Approved By'))
    approved_at = models.DateTimeField(null=True, blank=True, verbose_name=_('Approved At'))
    warehouse = models.ForeignKey('inventory.Warehouse', on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_('Warehouse'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Created At'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Updated At'))
    
    def get_image_url(self):
        """Get the image URL, ensuring it's a full Cloudinary URL."""
        if self.image:
            try:
                import logging
                logger = logging.getLogger(__name__)
                
                # Get the image name/path
                image_name = self.image.name
                logger.info(f"Getting image URL for product {self.id}, image name: {image_name}")
                
                # Try to get URL from the image field
                url = self.image.url
                logger.info(f"Initial image.url: {url}")
                
                # Cloudinary URLs should start with http:// or https://
                # If URL doesn't start with http, it's likely a relative path
                if url and not (url.startswith('http://') or url.startswith('https://')):
                    logger.warning(f"Image URL is not a full URL, attempting to get Cloudinary URL")
                    
                    # Try to get the full URL from Cloudinary storage
                    if hasattr(self.image, 'storage'):
                        try:
                            # Cloudinary storage should return full URL
                            storage_url = self.image.storage.url(self.image.name)
                            logger.info(f"Storage.url() returned: {storage_url}")
                            if storage_url and (storage_url.startswith('http://') or storage_url.startswith('https://')):
                                url = storage_url
                        except Exception as storage_error:
                            logger.warning(f"Storage.url() failed: {str(storage_error)}")
                    
                    # If still not a full URL, construct Cloudinary URL manually
                    if url and not (url.startswith('http://') or url.startswith('https://')):
                        from django.conf import settings
                        if hasattr(settings, 'CLOUDINARY_STORAGE'):
                            cloud_name = settings.CLOUDINARY_STORAGE.get('CLOUD_NAME', '')
                            if cloud_name:
                                # Remove leading slash if present
                                image_path = image_name.lstrip('/')
                                # Construct Cloudinary URL
                                url = f"https://res.cloudinary.com/{cloud_name}/image/upload/{image_path}"
                                logger.info(f"Constructed Cloudinary URL: {url}")
                            else:
                                logger.error("CLOUDINARY_STORAGE['CLOUD_NAME'] not found in settings")
                
                # Final check: ensure URL is valid
                if url and (url.startswith('http://') or url.startswith('https://')):
                    logger.info(f"Final image URL: {url}")
                    return url
                else:
                    logger.warning(f"Invalid image URL for product {self.id}: {url}")
                    return None
                    
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error getting image URL for product {self.id}: {str(e)}", exc_info=True)
                return None
        return None

    class Meta:
        verbose_name = _('Product')
        verbose_name_plural = _('Products')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name_en} ({self.code})"

    def save(self, *args, **kwargs):
        import logging
        from django.conf import settings
        logger = logging.getLogger(__name__)
        
        # Check if we have a new image file to upload
        image_file = None
        if self.image and hasattr(self.image, 'file') and self.image.file:
            # This is a new file upload
            image_file = self.image.file
            logger.info(f"Saving product {self.id or 'new'} with NEW image file: {self.image.name}")
        elif self.image:
            logger.info(f"Saving product {self.id or 'new'} with existing image: {self.image.name}")
        
        # Log storage info
        if self.image:
            if hasattr(self.image, 'storage'):
                storage_class = type(self.image.storage).__name__
                logger.info(f"Image storage class: {storage_class}")
                # Check if it's Cloudinary storage
                if 'cloudinary' not in storage_class.lower():
                    logger.warning(f"WARNING: Image storage is NOT Cloudinary! It's: {storage_class}")
                    logger.warning(f"DEFAULT_FILE_STORAGE setting: {getattr(settings, 'DEFAULT_FILE_STORAGE', 'Not set')}")
            else:
                logger.warning("Image has no storage attribute")
        
        # Auto-generate code if not provided
        if not self.code:
            self.code = generate_product_code()
        
        # Auto-approve if created by admin
        if not self.pk and hasattr(self, '_current_user') and self._current_user:
            if self._current_user.has_role('Admin') or self._current_user.is_superuser:
                self.is_approved = True
                self.approved_by = self._current_user
                self.approved_at = timezone.now()
        
        # Save the product (this should trigger Cloudinary upload if image is set)
        super().save(*args, **kwargs)
        
        # Log image info after save
        if self.image:
            logger.info(f"Product saved. Image name: {self.image.name}")
            try:
                image_url = self.image.url
                logger.info(f"Image URL after save: {image_url}")
                
                # Check if URL is a Cloudinary URL
                if image_url and (image_url.startswith('http://') or image_url.startswith('https://')):
                    if 'cloudinary.com' in image_url:
                        logger.info("✓ Image successfully uploaded to Cloudinary!")
                    else:
                        logger.warning(f"Image URL is not a Cloudinary URL: {image_url}")
                else:
                    logger.error(f"Image URL is not a full URL (likely local path): {image_url}")
                    logger.error("This means the image was NOT uploaded to Cloudinary!")
            except Exception as e:
                logger.error(f"Error getting image URL after save: {str(e)}", exc_info=True)

    @property
    def total_quantity(self):
        total = InventoryRecord.objects.filter(product=self).aggregate(total=Sum('quantity'))['total']
        return total or self.stock_quantity

    @property
    def available_quantity(self):
        return self.total_quantity

class SalesChannel(models.Model):
    name_en = models.CharField(max_length=100, verbose_name=_('Channel Name (English)'))
    name_ar = models.CharField(max_length=100, verbose_name=_('Channel Name (Arabic)'))
    url = models.URLField(verbose_name=_('Channel URL'))
    country = models.ForeignKey('settings.Country', on_delete=models.CASCADE, verbose_name=_('Country'))
    seller = models.ForeignKey('users.User', on_delete=models.CASCADE, verbose_name=_('Seller'))
    api_key = models.CharField(max_length=100, blank=True, verbose_name=_('API Key'))
    api_secret = models.CharField(max_length=100, blank=True, verbose_name=_('API Secret'))

    class Meta:
        verbose_name = _('Sales Channel')
        verbose_name_plural = _('Sales Channels')
        ordering = ['-id']

    def __str__(self):
        return f"{self.name_en} - {self.seller.get_full_name() or self.seller.email}"

class ProductDeletionRequest(models.Model):
    """Model for product deletion requests from sellers"""
    STATUS_CHOICES = [
        ('pending', _('Pending')),
        ('approved', _('Approved')),
        ('rejected', _('Rejected')),
    ]
    
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='deletion_requests')
    seller = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='deletion_requests')
    reason = models.TextField(help_text=_('Reason for deletion request'))
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    admin_notes = models.TextField(blank=True, null=True, help_text=_('Admin notes for the request'))
    requested_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(blank=True, null=True)
    reviewed_by = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_deletion_requests')
    
    class Meta:
        ordering = ['-requested_at']
        verbose_name = _('Product Deletion Request')
        verbose_name_plural = _('Product Deletion Requests')
    
    def __str__(self):
        return f"Deletion Request for {self.product.name_en} by {self.seller.get_full_name()}"
    
    def save(self, *args, **kwargs):
        if self.status in ['approved', 'rejected'] and not self.reviewed_at:
            self.reviewed_at = timezone.now()
        super().save(*args, **kwargs)

