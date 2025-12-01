from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.conf import settings
import uuid

# Import Cloudinary Storage if available
try:
    from cloudinary_storage.storage import MediaCloudinaryStorage
    CLOUDINARY_AVAILABLE = True
except ImportError:
    CLOUDINARY_AVAILABLE = False
    MediaCloudinaryStorage = None

class Supplier(models.Model):
    """Model for storing supplier information."""
    
    name = models.CharField(_('name'), max_length=150)
    contact_person = models.CharField(_('contact person'), max_length=150, blank=True, null=True)
    email = models.EmailField(_('email'), blank=True, null=True)
    phone = models.CharField(_('phone'), max_length=20, blank=True, null=True)
    address = models.TextField(_('address'), blank=True, null=True)
    country = models.CharField(_('country'), max_length=100)
    category = models.CharField(_('category'), max_length=50, default='General')
    
    # Rating and quality metrics
    quality_score = models.DecimalField(_('quality score'), max_digits=3, decimal_places=1, default=0.0)
    delivery_score = models.DecimalField(_('delivery score'), max_digits=3, decimal_places=1, default=0.0)
    price_score = models.DecimalField(_('price score'), max_digits=3, decimal_places=1, default=0.0)
    total_orders = models.PositiveIntegerField(_('total orders'), default=0)
    
    # System fields
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='created_suppliers'
    )
    is_active = models.BooleanField(_('active'), default=True)
    
    class Meta:
        verbose_name = _('supplier')
        verbose_name_plural = _('suppliers')
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name
    
    def update_scores(self):
        """Calculate the average scores from all sourcing requests."""
        completed_requests = self.sourcing_requests.filter(status='completed')
        if completed_requests.count() > 0:
            self.quality_score = completed_requests.aggregate(models.Avg('quality_rating'))['quality_rating__avg'] or 0
            self.delivery_score = completed_requests.aggregate(models.Avg('delivery_rating'))['delivery_rating__avg'] or 0
            self.price_score = completed_requests.aggregate(models.Avg('price_rating'))['price_rating__avg'] or 0
            self.total_orders = completed_requests.count()
            self.save()

class SourcingRequest(models.Model):
    """Model for sourcing requests from sellers."""
    
    STATUS_CHOICES = (
        ('draft', _('Draft')),
        ('submitted', _('Submitted')),
        ('under_review', _('Under Review')),
        ('approved', _('Approved')),
        ('rejected', _('Rejected')),
        ('in_progress', _('In Progress')),
        ('shipped', _('Shipped')),
        ('delivered', _('Delivered')),
        ('completed', _('Completed')),
        ('cancelled', _('Cancelled')),
    )
    
    PRIORITY_CHOICES = (
        ('low', _('Low')),
        ('medium', _('Medium')),
        ('high', _('High')),
        ('urgent', _('Urgent')),
    )
    
    FINANCE_SOURCE_CHOICES = (
        ('self_financed', _('Self Financed')),
        ('bank_loan', _('Bank Loan')),
        ('investor', _('Investor')),
        ('seller', _('Seller Account')),
        ('company', _('Company Account')),
    )
    
    # Identification
    request_number = models.CharField(_('request number'), max_length=20, unique=True, editable=False)
    
    # Foreign Keys
    seller = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='sourcing_requests',
        limit_choices_to={'role': 'seller'}
    )
    supplier = models.ForeignKey(
        Supplier, 
        on_delete=models.PROTECT, 
        related_name='sourcing_requests',
        null=True,
        blank=True
    )
    product = models.ForeignKey(
        'sellers.Product',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sourcing_requests'
    )
    
    # Request details
    product_name = models.CharField(_('product name'), max_length=200)
    product_image = models.ImageField(
        _('product image'), 
        upload_to='sourcing_products/', 
        blank=True, 
        null=True,
        storage=MediaCloudinaryStorage() if CLOUDINARY_AVAILABLE else None
    )
    product_url = models.URLField(_('product url'), max_length=500, blank=True, null=True, help_text=_('Link to product page'))
    carton_quantity = models.PositiveIntegerField(_('carton quantity'), default=0, help_text=_('Number of cartons'))
    unit_quantity = models.PositiveIntegerField(_('unit quantity'), default=0, help_text=_('Total number of units/pieces'))
    total_units = models.PositiveIntegerField(_('total units'), default=0)
    source_country = models.CharField(_('source country'), max_length=100)
    destination_country = models.CharField(_('destination country'), max_length=100)
    finance_source = models.CharField(_('finance source'), max_length=20, choices=FINANCE_SOURCE_CHOICES)
    supplier_contact = models.CharField(_('supplier contact'), max_length=100, blank=True, null=True)
    supplier_phone = models.CharField(_('supplier phone'), max_length=20, blank=True, null=True)
    
    # Financial details
    cost_per_unit = models.DecimalField(_('cost per unit'), max_digits=10, decimal_places=2, default=0)
    total_cost = models.DecimalField(_('total cost'), max_digits=10, decimal_places=2, default=0)
    shipping_cost = models.DecimalField(_('shipping cost'), max_digits=10, decimal_places=2, default=0)
    customs_fees = models.DecimalField(_('customs fees'), max_digits=10, decimal_places=2, default=0)
    grand_total = models.DecimalField(_('grand total'), max_digits=10, decimal_places=2, default=0)
    currency = models.CharField(_('currency'), max_length=3, default='AED')
    
    # Logistics information
    weight = models.DecimalField(_('weight (kg)'), max_digits=8, decimal_places=2, default=0)
    dimensions = models.CharField(_('dimensions'), max_length=50, blank=True, null=True)
    tracking_number = models.CharField(_('tracking number'), max_length=100, blank=True, null=True)
    estimated_arrival = models.DateField(_('estimated arrival'), blank=True, null=True)
    actual_arrival = models.DateField(_('actual arrival'), blank=True, null=True)
    
    # Status and workflow
    status = models.CharField(_('status'), max_length=20, choices=STATUS_CHOICES, default='draft')
    priority = models.CharField(_('priority'), max_length=10, choices=PRIORITY_CHOICES, default='normal')
    notes = models.TextField(_('notes'), blank=True, null=True)
    
    # Timestamps and tracking
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    submitted_at = models.DateTimeField(_('submitted at'), blank=True, null=True)
    approved_at = models.DateTimeField(_('approved at'), blank=True, null=True)
    completed_at = models.DateTimeField(_('completed at'), blank=True, null=True)
    
    # Approval workflow
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='approved_sourcing_requests'
    )
    
    # Ratings (filled after completion)
    quality_rating = models.DecimalField(_('quality rating'), max_digits=3, decimal_places=1, default=0)
    delivery_rating = models.DecimalField(_('delivery rating'), max_digits=3, decimal_places=1, default=0)
    price_rating = models.DecimalField(_('price rating'), max_digits=3, decimal_places=1, default=0)
    
    class Meta:
        verbose_name = _('sourcing request')
        verbose_name_plural = _('sourcing requests')
        ordering = ['-created_at']
    
    def __str__(self):
        return self.request_number
    
    @property
    def product_image_url(self):
        """Get the product image URL as a property for template access."""
        return self.get_product_image_url()
    
    def get_product_image_url(self):
        """Get the product image URL, checking both product_image and linked product."""
        # First, check if there's a direct product_image uploaded
        if self.product_image:
            try:
                # Check if the image field has a name (file exists)
                if self.product_image.name:
                    url = self.product_image.url
                    
                    # If URL is a Cloudinary URL (starts with http/https), return it directly
                    if url and (url.startswith('http://') or url.startswith('https://')):
                        return url
                    
                    # If URL is relative, try to get full Cloudinary URL
                    if url and not (url.startswith('http://') or url.startswith('https://')):
                        # Try to get URL from storage if it's Cloudinary
                        if hasattr(self.product_image, 'storage') and hasattr(self.product_image.storage, 'url'):
                            try:
                                full_url = self.product_image.storage.url(self.product_image.name)
                                if full_url and (full_url.startswith('http://') or full_url.startswith('https://')):
                                    return full_url
                            except:
                                pass
                    
                    # Return URL even if it's relative (Django will handle it)
                    if url:
                        return url
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.debug(f"Error getting product_image URL: {e}")
                # Try alternative method
                try:
                    if hasattr(self.product_image, 'url'):
                        return self.product_image.url
                except:
                    pass
        
        # If no direct image, check if there's a linked product with an image
        if self.product:
            try:
                # Use the product's get_image_url method if available (for Cloudinary support)
                if hasattr(self.product, 'get_image_url'):
                    image_url = self.product.get_image_url()
                    if image_url:
                        return image_url
                
                # Fallback to direct image URL
                if hasattr(self.product, 'image') and self.product.image:
                    try:
                        url = self.product.image.url
                        if url and (url.startswith('http://') or url.startswith('https://') or url.startswith('/')):
                            return url
                    except Exception as e:
                        import logging
                        logger = logging.getLogger(__name__)
                        logger.debug(f"Error getting product.image URL: {e}")
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.debug(f"Error accessing product: {e}")
        
        # If no linked product, try to find product by name
        if self.product_name and not self.product:
            try:
                from sellers.models import Product
                # Try to find a product with matching name
                product = Product.objects.filter(
                    name_en__iexact=self.product_name
                ).first()
                
                if product:
                    # Use the product's get_image_url method if available
                    if hasattr(product, 'get_image_url'):
                        image_url = product.get_image_url()
                        if image_url:
                            return image_url
                    
                    # Fallback to direct image URL
                    if hasattr(product, 'image') and product.image:
                        try:
                            url = product.image.url
                            if url and (url.startswith('http://') or url.startswith('https://') or url.startswith('/')):
                                return url
                        except:
                            pass
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.debug(f"Error finding product by name: {e}")
        
        return None
    
    def save(self, *args, **kwargs):
        # Generate the request number if it doesn't exist
        if not self.request_number:
            year = timezone.now().year
            month = timezone.now().month
            prefix = f"SOR-{year}-{month:02d}-"
            
            # Get the latest request number with this prefix
            latest = SourcingRequest.objects.filter(
                request_number__startswith=prefix
            ).order_by('-request_number').first()
            
            if latest:
                # Extract the number and increment
                last_num = int(latest.request_number.split('-')[-1])
                new_num = last_num + 1
            else:
                new_num = 1
                
            self.request_number = f"{prefix}{new_num:04d}"
        
        # Calculate totals
        # unit_quantity is now the total quantity in pieces
        # So total_units = unit_quantity (total pieces)
        self.total_units = self.unit_quantity
        self.grand_total = self.total_cost + self.shipping_cost + self.customs_fees
        
        # Update status timestamps
        if self.status == 'submitted' and not self.submitted_at:
            self.submitted_at = timezone.now()
        if self.status == 'approved' and not self.approved_at:
            self.approved_at = timezone.now()
        if self.status == 'completed' and not self.completed_at:
            self.completed_at = timezone.now()
            
            # Update supplier ratings if this is a new completion
            if self.supplier:
                self.supplier.update_scores()
                
        super().save(*args, **kwargs)

class SourcingRequestDocument(models.Model):
    """Model for storing documents related to sourcing requests."""
    
    DOCUMENT_TYPES = (
        ('invoice', _('Invoice')),
        ('packing_list', _('Packing List')),
        ('shipping_label', _('Shipping Label')),
        ('product_image', _('Product Image')),
        ('customs_document', _('Customs Document')),
        ('payment_receipt', _('Payment Receipt')),
        ('other', _('Other')),
    )
    
    sourcing_request = models.ForeignKey(
        SourcingRequest, 
        on_delete=models.CASCADE, 
        related_name='documents'
    )
    document_type = models.CharField(_('document type'), max_length=20, choices=DOCUMENT_TYPES)
    file = models.FileField(_('file'), upload_to='sourcing_documents/')
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='uploaded_sourcing_documents'
    )
    uploaded_at = models.DateTimeField(_('uploaded at'), auto_now_add=True)
    notes = models.TextField(_('notes'), blank=True, null=True)
    
    class Meta:
        verbose_name = _('sourcing request document')
        verbose_name_plural = _('sourcing request documents')
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return f"{self.get_document_type_display()} for {self.sourcing_request.request_number}"

class SourcingComment(models.Model):
    """Model for comments on sourcing requests."""
    
    sourcing_request = models.ForeignKey(
        SourcingRequest, 
        on_delete=models.CASCADE, 
        related_name='comments'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE
    )
    comment = models.TextField(_('comment'))
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('sourcing comment')
        verbose_name_plural = _('sourcing comments')
        ordering = ['created_at']
    
    def __str__(self):
        return f"Comment by {self.user.get_full_name()} on {self.sourcing_request.request_number}"
