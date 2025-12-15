from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.db.models import Q, Sum, Count
from django.core.paginator import Paginator
from .models import Product, ProductDeletionRequest
from .forms import SellerProductForm, ProductDeletionRequestForm
from inventory.models import InventoryRecord
from orders.models import Order
from orders.forms import OrderImportForm
from inventory.models import Warehouse
from users.models import AuditLog
from datetime import datetime
import csv
import io
import json

def has_seller_role(user):
    return (
        user.is_superuser or
        user.has_role('Super Admin') or
        user.has_role('Admin') or
        user.has_role('Seller')
    )

def _generate_order_code():
    """Generate a unique order code."""
    import random
    import string
    while True:
        code = 'ORD-' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        if not Order.objects.filter(order_code=code).exists():
            return code

def create_seller_notification(seller, title, message, notification_type='system', priority='medium', 
                              related_object_type=None, related_object_id=None, related_url=None):
    """Create a notification for a seller using the universal notifications system"""
    try:
        from notifications.models import Notification
        
        # Create notification directly without using create_notification method
        return Notification.objects.create(
            user=seller,
            title=title,
            message=message,
            notification_type=notification_type,
            priority=priority,
            target_role='Seller',
            related_object_type=related_object_type,
            related_object_id=related_object_id,
            related_url=related_url
        )
    except ImportError:
        # Notifications app not available yet
        return None
    except Exception as e:
        # Log the error but don't break the main functionality
        print(f"Error creating notification: {e}")
        return None

def get_seller_notifications_count(user):
    """Get unread notifications count for a seller"""
    try:
        from notifications.models import Notification
        
        return Notification.objects.filter(
            user=user,
            is_read=False,
            is_archived=False
        ).count()
    except ImportError:
        # Notifications app not available yet
        return 0


@login_required
def dashboard(request):
    """Seller dashboard with real data from database."""
    if not has_seller_role(request.user):
        messages.error(request, "ليس لديك صلاحية للدخول لهذه الصفحة.")
        return redirect('dashboard:index')
    
    try:
        from django.db.models import Count
        from django.utils import timezone
        from datetime import timedelta
        from sourcing.models import SourcingRequest
        
        # Get real data for the current user (seller)
        all_products = Product.objects.filter(seller=request.user)  # All products (approved and pending)
        # Get orders where the seller is the current user ONLY
        all_orders = Order.objects.filter(seller=request.user)
        
        # Calculate detailed order statistics
        orders_count = all_orders.count()
        received_orders = all_orders.filter(status__in=['pending', 'pending_confirmation', 'confirmed', 'processing', 'shipped', 'delivered']).count()
        completed_orders = all_orders.filter(status='confirmed').count()
        processing_orders = all_orders.filter(status__in=['pending', 'pending_confirmation', 'processing']).count()
        cancelled_orders = all_orders.filter(status='cancelled').count()
        postponed_orders = all_orders.filter(status='pending').count()  # Orders that are pending/on hold
        in_progress_orders = all_orders.filter(status__in=['processing', 'shipped']).count()
        delivered_orders = all_orders.filter(status='delivered').count()
        
        # Calculate inventory statistics
        total_inventory = all_products.count()
        available_inventory = all_products.filter(stock_quantity__gt=0).count()
        in_delivery_inventory = all_products.filter(stock_quantity=0).count()
        
        # Calculate sales data - sum of all order totals
        total_sales_amount = sum(order.total_price for order in all_orders)
        
        # Calculate this month's sales
        this_month = timezone.now().month
        this_year = timezone.now().year
        this_month_orders = all_orders.filter(
            date__year=this_year,
            date__month=this_month
        )
        this_month_sales = sum(order.total_price for order in this_month_orders)
        
        # Calculate sales by status
        confirmed_sales = sum(order.total_price for order in all_orders.filter(status='confirmed'))
        delivered_sales = sum(order.total_price for order in all_orders.filter(status='delivered'))
        
        # Get sourcing requests
        sourcing_requests = SourcingRequest.objects.filter(seller=request.user)
        sourcing_requests_count = sourcing_requests.count()
        pending_requests = sourcing_requests.filter(status='pending').count()
        approved_requests = sourcing_requests.filter(status='approved').count()
        
        # Get notifications count using the notifications app
        notifications_count = get_seller_notifications_count(request.user)
        
        # Calculate approval statistics
        pending_approval_count = Product.objects.filter(seller=request.user, is_approved=False).count()
        
        # Calculate additional product statistics
        low_stock_products = all_products.filter(stock_quantity__lt=10, stock_quantity__gt=0)
        out_of_stock_products = all_products.filter(stock_quantity=0).count()
        products_with_orders = all_orders.filter(product__in=all_products).values('product').distinct().count()
        products_without_orders = all_products.count() - products_with_orders
        
        # Get top performing products (by order count)
        top_performing_products = []
        for product in all_products:
            order_count = all_orders.filter(product=product).count()
            if order_count > 0:
                top_performing_products.append({
                    'product': product,
                    'order_count': order_count,
                    'total_revenue': sum(order.total_price for order in all_orders.filter(product=product))
                })
        
        # Sort by order count and take top 5
        top_performing_products.sort(key=lambda x: x['order_count'], reverse=True)
        top_performing_products = top_performing_products[:5]
        
        # Get recent orders and products
        recent_orders = all_orders.order_by('-date')[:5]
        
        # Enhance products with order information
        enhanced_products = []
        for product in all_products:
            product_orders = all_orders.filter(product=product)
            order_count = product_orders.count()
            total_ordered_quantity = sum(order.quantity for order in product_orders)
            total_revenue = sum(order.total_price for order in product_orders)
            last_order = product_orders.order_by('-date').first()
            last_order_date = last_order.date if last_order else None
            
            enhanced_products.append({
                'product': product,
                'has_orders': order_count > 0,
                'order_count': order_count,
                'total_ordered_quantity': total_ordered_quantity,
                'total_revenue': total_revenue,
                'last_order_date': last_order_date,
            })
        
        products = enhanced_products
        all_products_for_dropdown = all_products.order_by('-created_at')  # For dropdowns
        
        # Prepare sales performance data for chart (last 6 months)
        sales_data = []
        months = []
        for i in range(6):
            month_date = timezone.now() - timedelta(days=30*i)
            month_orders = all_orders.filter(
                date__year=month_date.year,
                date__month=month_date.month
            )
            month_sales = sum(order.total_price for order in month_orders)
            sales_data.append(float(month_sales))
            months.append(month_date.strftime('%b'))
        
        # Prepare top products data for chart - count orders for each product
        top_products = []
        for product in all_products:
            product_orders = all_orders.filter(product=product).count()
            top_products.append((product, product_orders))
        
        # Sort by order count and take top 5
        top_products.sort(key=lambda x: x[1], reverse=True)
        top_products = top_products[:5]
        
        product_names = [product.name_en for product, _ in top_products]
        product_sales = [count for _, count in top_products]
        
        # Calculate total revenue
        total_revenue = sum(order.total_price for order in all_orders)
        
        # Fix: Provide unread_notifications as an empty list (or fetch if you have a notifications app)
        unread_notifications = []
        
        return render(request, 'sellers/dashboard.html', {
            'products': products,
            'all_products': all_products_for_dropdown,  # For dropdowns
            'all_products_json': json.dumps([{
                'id': p.id,
                'name': p.name_en,
                'code': p.code
            } for p in all_products_for_dropdown]),  # For JavaScript
            'recent_orders': recent_orders,
            'total_revenue': total_revenue,
            'total_inventory': total_inventory,
            'available_inventory': available_inventory,
            'in_delivery_inventory': in_delivery_inventory,
            'orders_count': orders_count,
            'received_orders': received_orders,
            'completed_orders': completed_orders,
            'processing_orders': processing_orders,
            'cancelled_orders': cancelled_orders,
            'postponed_orders': postponed_orders,
            'in_progress_orders': in_progress_orders,
            'delivered_orders': delivered_orders,
            'total_sales': f"AED {total_sales_amount:,.0f}",
            'this_month_sales': f"AED {this_month_sales:,.0f}",
            'confirmed_sales': f"AED {confirmed_sales:,.0f}",
            'delivered_sales': f"AED {delivered_sales:,.0f}",
            'sourcing_requests_count': sourcing_requests_count,
            'pending_requests': pending_requests,
            'approved_requests': approved_requests,
            'pending_approval_count': pending_approval_count,
            'low_stock_products': low_stock_products,
            'out_of_stock_products': out_of_stock_products,
            'products_with_orders': products_with_orders,
            'products_without_orders': products_without_orders,
            'top_performing_products': top_performing_products,
            'sales_data': json.dumps(sales_data),
            'months': json.dumps(months),
            'product_names': json.dumps(product_names),
            'product_sales': json.dumps(product_sales),
            'unread_notifications': unread_notifications,
            'notifications_count': notifications_count,
        })
        
    except Exception as e:
        # Log the error and show a user-friendly message
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error in seller dashboard: {str(e)}")
        
        messages.error(request, "حدث خطأ أثناء تحميل البيانات. يرجى المحاولة مرة أخرى.")
        
        # Return empty dashboard with default values
        return render(request, 'sellers/dashboard.html', {
            'products': [],
            'all_products': [],
            'all_products_json': '[]',
            'recent_orders': [],
            'total_revenue': 0,
            'total_inventory': 0,
            'available_inventory': 0,
            'in_delivery_inventory': 0,
            'orders_count': 0,
            'received_orders': 0,
            'completed_orders': 0,
            'processing_orders': 0,
            'cancelled_orders': 0,
            'postponed_orders': 0,
            'in_progress_orders': 0,
            'delivered_orders': 0,
            'total_sales': "AED 0",
            'this_month_sales': "AED 0",
            'confirmed_sales': "AED 0",
            'delivered_sales': "AED 0",
            'sourcing_requests_count': 0,
            'pending_requests': 0,
            'approved_requests': 0,
            'pending_approval_count': 0,
            'low_stock_products': [],
            'out_of_stock_products': 0,
            'products_with_orders': 0,
            'products_without_orders': 0,
            'top_performing_products': [],
            'sales_data': json.dumps([0, 0, 0, 0, 0, 0]),
            'months': json.dumps(['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun']),
            'product_names': json.dumps([]),
            'product_sales': json.dumps([]),
            'unread_notifications': [],
            'notifications_count': 0,
        })

@login_required
def product_list(request):
    """List all products for the seller."""
    if not has_seller_role(request.user):
        messages.error(request, "ليس لديك صلاحية للدخول لهذه الصفحة.")
        return redirect('dashboard:index')
    
    # Get search and filter parameters
    search_query = request.GET.get('search', '')
    selected_warehouse_id = request.GET.get('warehouse', '')
    status_filter = request.GET.get('status', '')
    
    # Get products for this seller
    if request.user.has_role('Seller'):
        products = Product.objects.filter(seller=request.user).order_by('-created_at')
    else:
        products = Product.objects.all().order_by('-created_at')
    
    # Apply search filter
    if search_query:
        products = products.filter(
            Q(name_en__icontains=search_query) |
            Q(name_ar__icontains=search_query) |
            Q(code__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    # Apply warehouse filter
    if selected_warehouse_id:
        # Filter products that have inventory records in the selected warehouse
        products = products.filter(inventoryrecord__warehouse_id=selected_warehouse_id).distinct()
    
    # Apply status filter
    if status_filter:
        if status_filter == 'in_stock':
            products = products.filter(stock_quantity__gt=10)
        elif status_filter == 'low_stock':
            products = products.filter(stock_quantity__gt=0, stock_quantity__lte=10)
        elif status_filter == 'out_of_stock':
            products = products.filter(stock_quantity=0)
    
    # Get warehouses for filter dropdown
    warehouses = Warehouse.objects.all()
    
    # Get pending approval products for admin
    pending_approval_products = []
    if request.user.has_role('Admin') or request.user.is_superuser:
        pending_approval_products = Product.objects.filter(is_approved=False).order_by('-created_at')[:6]
    
    # Prepare inventory data similar to inventory/products
    inventory_data = []
    for product in products:
        # Count pending orders for this product
        from orders.models import Order
        pending_orders = Order.objects.filter(
            product=product,
            status__in=['pending', 'processing']
        ).count()
        
        inventory_data.append({
            'product': product,
            'total_quantity': product.stock_quantity or 0,
            'available_quantity': product.stock_quantity or 0,
            'pending_orders': pending_orders,
        })
        
    return render(request, 'sellers/products.html', {
        'products': products,
        'inventory_data': inventory_data,
        'warehouses': warehouses,
        'search_query': search_query,
        'selected_warehouse_id': selected_warehouse_id,
        'status_filter': status_filter,
        'pending_approval_products': pending_approval_products,
    })

@login_required
def product_create(request):
    """Create a new product."""
    if not has_seller_role(request.user):
        messages.error(request, "ليس لديك صلاحية للدخول لهذه الصفحة.")
        return redirect('dashboard:index')
    
    # Get warehouses for admin selection (optional - seller can add product even without warehouse)
    from inventory.models import Warehouse
    warehouses = Warehouse.objects.filter(is_active=True)
    
    # Check if user is admin or superuser (can assign warehouse)
    is_admin = request.user.has_role('Admin') or request.user.is_superuser
    
    if request.method == 'POST':
        # Debug: Log request info
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"POST request received for product_create. FILES keys: {list(request.FILES.keys())}, Content-Type: {request.content_type}")
        
        # Get form data manually to handle the form properly
        name_en = request.POST.get('name_en')
        name_ar = request.POST.get('name_ar')
        category = request.POST.get('category')
        description = request.POST.get('description')
        selling_price = request.POST.get('selling_price')
        purchase_price = request.POST.get('cost_price') or request.POST.get('purchase_price')
        stock_quantity = request.POST.get('stock_quantity', 0)
        product_link = request.POST.get('product_link')
        image = request.FILES.get('image')
        warehouse_id = request.POST.get('warehouse_id') if is_admin else None
        
        # Debug: Log image info
        if image:
            logger.info(f"Image file received: name={image.name}, size={image.size}, content_type={image.content_type}")
        else:
            logger.warning("No image file in request.FILES for product_create")
            # Check if 'image' key exists but is empty
            if 'image' in request.FILES:
                logger.warning("'image' key exists in FILES but is empty")
        
        # Handle product variants
        product_variants = request.POST.getlist('product_variants[]')
        # Filter out empty variants and join with commas
        variants_list = [v.strip() for v in product_variants if v.strip()]
        product_variant = ', '.join(variants_list) if variants_list else ''
        
        # Validate required fields
        if not name_en or not selling_price:
            messages.error(request, 'Please fill in all required fields.')
            return render(request, 'sellers/product_create.html', {'warehouses': warehouses, 'is_admin': is_admin})
        
        # Validate warehouse if admin is creating product (optional - can be None)
        warehouse = None
        if is_admin and warehouse_id:
            try:
                warehouse = Warehouse.objects.get(id=warehouse_id, is_active=True)
            except Warehouse.DoesNotExist:
                messages.warning(request, 'The selected warehouse does not exist or is inactive. Product will be created without warehouse assignment.')
                warehouse = None
        
        # Validate price ranges
        try:
            selling_price_float = float(selling_price)
            if selling_price_float < 0 or selling_price_float > 999999.99:
                messages.error(request, 'Selling price must be between 0 and 999,999.99 AED.')
                return render(request, 'sellers/product_create.html', {'warehouses': warehouses, 'is_admin': is_admin})
        except (ValueError, TypeError):
            messages.error(request, 'Please enter a valid selling price.')
            return render(request, 'sellers/product_create.html', {'warehouses': warehouses, 'is_admin': is_admin})
        
        try:
            purchase_price_float = float(purchase_price) if purchase_price else None
            if purchase_price_float is not None and (purchase_price_float < 0 or purchase_price_float > 999999.99):
                messages.error(request, 'Purchase price must be between 0 and 999,999.99 AED.')
                return render(request, 'sellers/product_create.html', {'warehouses': warehouses, 'is_admin': is_admin})
        except (ValueError, TypeError):
            messages.error(request, 'Please enter a valid purchase price.')
            return render(request, 'sellers/product_create.html', {'warehouses': warehouses, 'is_admin': is_admin})
        
        try:
            # Create product manually
            product = Product.objects.create(
                name_en=name_en,
                name_ar=name_ar or '',
                category=category or '',
                description=description or '',
                product_variant=product_variant,
                selling_price=selling_price_float,
                purchase_price=purchase_price_float,
                stock_quantity=int(stock_quantity) if stock_quantity else 0,
                product_link=product_link or '',
                seller=request.user,
                created_by=request.user,
                image=image if image else None,
                warehouse=warehouse  # Assign warehouse if admin
            )
            
            # Verify image was saved if provided
            if image:
                # Refresh from database to get updated image URL
                product.refresh_from_db()
                
                # Get image URL using the model method
                image_url = product.get_image_url()
                
                if product.image and image_url:
                    logger.info(f"Product image uploaded successfully. URL: {image_url}")
                    messages.success(request, f'Product created successfully! Image uploaded.')
                elif product.image:
                    logger.warning(f"Product image was set but URL is not available. image.name: {product.image.name}, image.url: {getattr(product.image, 'url', 'N/A')}")
                    messages.warning(request, 'Product created but image may not be accessible. Please check the image or try uploading again.')
                else:
                    logger.error("Image was not saved to product")
                    messages.error(request, 'Error: Image was not saved. Please try again.')
            
            # Auto-approve products created by admin or superuser
            if is_admin:
                product.is_approved = True
                product.approved_by = request.user
                product.approved_at = timezone.now()
                product.save()
                
                # Create inventory record if warehouse is assigned
                if warehouse:
                    from inventory.models import InventoryRecord
                    InventoryRecord.objects.create(
                        product=product,
                        warehouse=warehouse,
                        quantity=product.stock_quantity
                    )
                
                messages.success(request, f"Product '{product.name_en}' created and approved successfully with SKU: {product.code}.")
            else:
                # Sellers need approval
                product.is_approved = False
                product.save()
                messages.success(request, f"Product '{product.name_en}' created successfully with SKU: {product.code}. Waiting for admin approval.")
            
            return redirect('sellers:products')
                
        except Exception as e:
                # Log the error
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error creating product: {str(e)}")
                
                # Handle Cloudinary errors specifically
                error_message = str(e)
                if "concurrent requests" in error_message.lower() or "too many" in error_message.lower():
                    messages.error(request, "خطأ في رفع الصورة: يرجى المحاولة مرة أخرى بعد قليل. تأكد من عدم الضغط على الزر أكثر من مرة.")
                elif "cloudinary" in error_message.lower():
                    messages.error(request, "خطأ في رفع الصورة إلى Cloudinary. يرجى التحقق من إعدادات Cloudinary أو المحاولة مرة أخرى.")
                else:
                    messages.error(request, f"Error creating product: {error_message}")
    
    return render(request, 'sellers/product_create.html', {'warehouses': warehouses, 'is_admin': is_admin})

@login_required
def product_detail(request, product_id):
    """View a specific product."""
    if not has_seller_role(request.user):
        messages.error(request, "ليس لديك صلاحية للدخول لهذه الصفحة.")
        return redirect('dashboard:index')
    product = get_object_or_404(Product, id=product_id)
    
    # Check permissions
    if request.user.has_role('Seller') and product.seller != request.user:
        messages.error(request, "You don't have permission to view this product.")
        return redirect('sellers:products')
        
    return render(request, 'sellers/product_detail.html', {
        'product': product,
    })

@login_required
def product_edit(request, product_id):
    """Edit a specific product."""
    if not has_seller_role(request.user):
        messages.error(request, "ليس لديك صلاحية للدخول لهذه الصفحة.")
        return redirect('dashboard:index')
    
    try:
        product = get_object_or_404(Product, id=product_id)
        
        # Check permissions - use has_role instead of primary_role
        if request.user.has_role('Seller') and product.seller != request.user:
            messages.error(request, "You don't have permission to edit this product.")
            return redirect('sellers:products')
        
        if request.method == 'POST':
            # Debug: Log request info
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"POST request received. FILES keys: {list(request.FILES.keys())}, Content-Type: {request.content_type}")
            
            # Get form data manually to handle the form properly
            name_en = request.POST.get('name_en')
            name_ar = request.POST.get('name_ar')
            category = request.POST.get('category')
            description = request.POST.get('description')
            selling_price = request.POST.get('selling_price')
            purchase_price = request.POST.get('purchase_price')
            stock_quantity = request.POST.get('stock_quantity', 0)
            product_link = request.POST.get('product_link')
            image = request.FILES.get('image')
            
            # Debug: Log image info
            if image:
                logger.info(f"Image file received: name={image.name}, size={image.size}, content_type={image.content_type}")
            else:
                logger.warning("No image file in request.FILES")
                # Check if 'image' key exists but is empty
                if 'image' in request.FILES:
                    logger.warning("'image' key exists in FILES but is empty")
            
            # Validate required fields
            if not name_en or not selling_price:
                messages.error(request, 'Please fill in all required fields.')
                return render(request, 'sellers/product_edit.html', {'product': product})
            
            try:
                # Update product fields
                product.name_en = name_en
                product.name_ar = name_ar or ''
                product.category = category or ''
                product.description = description or ''
                product.selling_price = float(selling_price)
                product.purchase_price = float(purchase_price) if purchase_price else None
                product.stock_quantity = int(stock_quantity) if stock_quantity else 0
                product.product_link = product_link or ''
                
                # Update image if provided
                if image:
                    try:
                        # Delete old image if exists
                        if product.image:
                            try:
                                product.image.delete(save=False)
                            except Exception as e:
                                logger.warning(f"Could not delete old image: {str(e)}")
                        
                        # Save new image
                        logger.info(f"Attempting to save image: {image.name}, size: {image.size} bytes")
                        logger.info(f"Image storage class: {type(product.image.storage) if hasattr(product.image, 'storage') else 'No storage'}")
                        
                        # Assign image to product
                        product.image = image
                        
                        # Save immediately to upload to Cloudinary
                        product.save()
                        
                        # Refresh from database to get updated image URL
                        product.refresh_from_db()
                        
                        # Get image URL using the model method
                        image_url = product.get_image_url()
                        
                        # Verify image was saved
                        if product.image and image_url:
                            logger.info(f"Image uploaded successfully. URL: {image_url}")
                            messages.success(request, f'Product and image updated successfully!')
                        elif product.image:
                            logger.warning(f"Image was set but URL is not available. image.name: {product.image.name}, image.url: {getattr(product.image, 'url', 'N/A')}")
                            messages.warning(request, 'Product updated but image may not be accessible. Please check the image or try uploading again.')
                        else:
                            logger.error("Image was not saved to product")
                            messages.error(request, 'Error: Image was not saved. Please try again.')
                    except Exception as img_error:
                        logger.error(f"Error uploading image: {str(img_error)}", exc_info=True)
                        error_msg = str(img_error)
                        if 'cloudinary' in error_msg.lower():
                            messages.error(request, 'خطأ في رفع الصورة إلى Cloudinary. يرجى التحقق من إعدادات Cloudinary أو المحاولة مرة أخرى.')
                        else:
                            messages.error(request, f'خطأ في رفع الصورة: {error_msg}. يرجى المحاولة مرة أخرى.')
                        # Continue with other updates even if image fails
                
                # If product was edited, it needs to be re-approved (unless edited by admin)
                if request.user.has_role('Admin') or request.user.is_superuser:
                    product.is_approved = True
                    product.approved_by = request.user
                    product.approved_at = timezone.now()
                elif product.is_approved:
                    product.is_approved = False
                    product.approved_by = None
                    product.approved_at = None
                
                # Save product (only if image wasn't already saved)
                if not image:
                    product.save()
                
                messages.success(request, f'Product "{product.name_en}" updated successfully.')
                return redirect('sellers:product_detail', product_id=product.id)
                
            except Exception as e:
                # Log the error
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error updating product: {str(e)}")
                
                messages.error(request, f"Error updating product: {str(e)}")
        
        return render(request, 'sellers/product_edit.html', {
            'product': product,
        })
    except Exception as e:
        messages.error(request, f'Error accessing product: {str(e)}')
        return redirect('sellers:products')

@login_required
def product_delete(request, product_id):
    """Delete a specific product."""
    if not has_seller_role(request.user):
        messages.error(request, "ليس لديك صلاحية للدخول لهذه الصفحة.")
        return redirect('dashboard:index')
    
    product = get_object_or_404(Product, id=product_id)
    
    # Check permissions
    if request.user.has_role('Seller') and product.seller != request.user:
        messages.error(request, "You don't have permission to delete this product.")
        return redirect('sellers:products')
    
    if request.method == 'POST':
        try:
            # Create audit log
            AuditLog.objects.create(
                user=request.user,
                action='delete',
                entity_type='product',
                entity_id=str(product.id),
                description=f"Product deleted: {product.name} by {request.user.email}",
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            product.delete()
            messages.success(request, f"Product '{product.name}' has been deleted successfully.")
            return redirect('sellers:products')
        except Exception as e:
            messages.error(request, f"Error deleting product: {str(e)}")
            return redirect('sellers:product_detail', product_id=product.id)
    
    return render(request, 'sellers/product_delete_confirm.html', {'product': product})

@login_required
def product_delete_request(request, product_id):
    """Request deletion of a specific product."""
    if not has_seller_role(request.user):
        messages.error(request, "ليس لديك صلاحية للدخول لهذه الصفحة.")
        return redirect('dashboard:index')
    
    product = get_object_or_404(Product, id=product_id)
    
    # Check permissions - use has_role instead of primary_role
    if request.user.has_role('Seller') and product.seller != request.user:
        messages.error(request, "You don't have permission to request deletion of this product.")
        return redirect('sellers:products')
    
    # Check if there's already a pending deletion request
    existing_request = ProductDeletionRequest.objects.filter(
        product=product, 
        seller=request.user, 
        status='pending'
    ).first()
    
    if existing_request:
        messages.warning(request, f'You already have a pending deletion request for "{product.name_en}".')
        return redirect('sellers:products')
    
    if request.method == 'POST':
        form = ProductDeletionRequestForm(request.POST)
        if form.is_valid():
            deletion_request = form.save(commit=False)
            deletion_request.product = product
            deletion_request.seller = request.user
            deletion_request.save()
            
            # Create notification for admin
            from notifications.models import Notification
            Notification.objects.create(
                user=request.user,
                title="Product Deletion Request",
                message=f"Seller {request.user.get_full_name()} has requested to delete product '{product.name_en}'",
                notification_type='product_deletion_request',
                priority='high',
                related_object_type='product',
                related_object_id=product.id,
                related_url=f"/admin/sellers/productdeletionrequest/{deletion_request.id}/"
            )
            
            messages.success(request, f'Deletion request for "{product.name_en}" has been submitted successfully. An admin will review it soon.')
            return redirect('sellers:products')
    else:
        form = ProductDeletionRequestForm()
    
    return render(request, 'sellers/product_delete_request.html', {
        'product': product,
        'form': form,
    })

@login_required
def order_list(request):
    """List orders for the seller."""
    if not has_seller_role(request.user):
        messages.error(request, "ليس لديك صلاحية للدخول لهذه الصفحة.")
        return redirect('dashboard:index')
    
    # Get orders based on user role
    if request.user.has_role('Seller'):
        # Sellers ONLY see orders they created (seller=request.user)
        # Remove the product-based filtering for security
        orders = Order.objects.select_related('agent', 'seller', 'product').filter(
            seller=request.user
        ).order_by('-date')
    else:
        # Admins and super admins see all orders
        orders = Order.objects.select_related('agent', 'seller', 'product').all().order_by('-date')
    
    # Apply filters - exactly like main orders view
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    if search_query:
        orders = orders.filter(
            Q(order_code__icontains=search_query) |
            Q(customer__icontains=search_query) |
            Q(customer_phone__icontains=search_query) |
            Q(product__name_en__icontains=search_query)
        )
    
    if status_filter:
        orders = orders.filter(status=status_filter)
    
    if date_from:
        orders = orders.filter(date__date__gte=date_from)
    
    if date_to:
        orders = orders.filter(date__date__lte=date_to)
    
    # Pagination - same as main orders view
    from django.core.paginator import Paginator
    paginator = Paginator(orders, 10)  # Show 10 orders per page (same as main view)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get order statistics
    total_orders = orders.count()
    pending_orders = orders.filter(status='pending').count()
    confirmed_orders = orders.filter(status='confirmed').count()
    cancelled_orders = orders.filter(status='cancelled').count()
    
    return render(request, 'sellers/orders.html', {
        'orders': page_obj,
        'page_obj': page_obj,
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'confirmed_orders': confirmed_orders,
        'cancelled_orders': cancelled_orders,
        'search_query': search_query,
        'status_filter': status_filter,
        'date_from': date_from,
        'date_to': date_to,
        'status_choices': Order.STATUS_CHOICES,  # Same as main orders view
    })

@login_required
def import_orders(request):
    """Import orders from CSV for sellers with improved error handling and validation."""
    if not has_seller_role(request.user):
        messages.error(request, "ليس لديك صلاحية للدخول لهذه الصفحة.")
        return redirect('dashboard:index')
    
    if request.method == 'POST':
        form = OrderImportForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            try:
                file = request.FILES.get('file')
                if not file:
                    messages.error(request, 'No file was uploaded.')
                    return render(request, 'sellers/import_orders.html', {'form': form})
                
                # Validate file type
                if not file.name.lower().endswith('.csv'):
                    messages.error(request, 'Please upload a CSV file (.csv extension).')
                    return render(request, 'sellers/import_orders.html', {'form': form})
                
                # Check file size (max 5MB) 
                if file.size > 5 * 1024 * 1024:
                    messages.error(request, 'File size must be less than 5MB.')
                    return render(request, 'sellers/import_orders.html', {'form': form})
                
                try:
                    # Try UTF-8 first
                    decoded_file = file.read().decode('utf-8')
                except UnicodeDecodeError:
                    # Try with different encoding
                    file.seek(0)  # Reset file pointer
                    try:
                        decoded_file = file.read().decode('latin-1')
                    except UnicodeDecodeError:
                        messages.error(request, 'Unable to read file. Please ensure it is a valid CSV file.')
                        return render(request, 'sellers/import_orders.html', {'form': form})
                
                csv_data = csv.reader(io.StringIO(decoded_file))
                
                # Validate header row
                try:
                    header = next(csv_data)
                    expected_columns = ['Order Code', 'Customer Name', 'Mobile Number', 'Shipping Address', 'Product ID/Code', 'Quantity', 'Price']
                    
                    # More flexible header validation - check if we have the essential columns
                    essential_columns = ['Customer Name', 'Mobile Number', 'Shipping Address', 'Product ID/Code']
                    found_essential = 0
                    
                    for col in essential_columns:
                        if any(col.lower() in h.lower() for h in header):
                            found_essential += 1
                    
                    if found_essential < 3:  # Need at least 3 out of 4 essential columns
                        messages.error(request, f'CSV file must have essential columns: Customer Name, Mobile Number, Shipping Address, Product ID/Code. Found {found_essential} essential columns.')
                        return render(request, 'sellers/import_orders.html', {'form': form})
                    
                except StopIteration:
                    messages.error(request, 'CSV file is empty or invalid.')
                    return render(request, 'sellers/import_orders.html', {'form': form})
                
                success_count = 0
                error_count = 0
                warnings = []
                errors = []
                
                for row_num, row in enumerate(csv_data, start=2):  # Start from 2 because we skipped header
                    try:
                        # Skip empty rows
                        if not row or all(cell.strip() == '' for cell in row):
                            continue
                        
                        # Extract data from row (flexible column mapping)
                        order_code = row[0].strip() if len(row) > 0 and row[0].strip() else None
                        customer_name = row[1].strip() if len(row) > 1 and row[1].strip() else None
                        mobile_number = row[2].strip() if len(row) > 2 and row[2].strip() else None
                        address = row[3].strip() if len(row) > 3 and row[3].strip() else None
                        product_id = row[4].strip() if len(row) > 4 and row[4].strip() else None
                        quantity = int(float(row[5])) if len(row) > 5 and row[5].strip() else 1
                        price = float(row[6]) if len(row) > 6 and row[6].strip() else 0.0
                        notes = row[7].strip() if len(row) > 7 and row[7].strip() else ''
                        order_date_str = row[8].strip() if len(row) > 8 and row[8].strip() else None
                        
                        # Validate required fields
                        if not customer_name:
                            errors.append(f"Row {row_num}: Customer Name is required")
                            error_count += 1
                            continue
                        
                        if not mobile_number:
                            errors.append(f"Row {row_num}: Mobile Number is required")
                            error_count += 1
                            continue
                        
                        if not address:
                            errors.append(f"Row {row_num}: Shipping Address is required")
                            error_count += 1
                            continue
                        
                        if not product_id:
                            warnings.append(f"Row {row_num}: Product ID/Code is missing. Order will be created without product link.")
                        
                        if quantity <= 0:
                            errors.append(f"Row {row_num}: Quantity must be greater than 0")
                            error_count += 1
                            continue
                        
                        if price < 0:
                            errors.append(f"Row {row_num}: Price cannot be negative")
                            error_count += 1
                            continue
                        
                        # Parse order date
                        try:
                            if order_date_str:
                                order_date = datetime.strptime(order_date_str, '%Y-%m-%d')
                            else:
                                order_date = timezone.now()
                        except ValueError:
                            order_date = timezone.now()
                        
                        # Find product by ID or code (if product_id exists)
                        product = None
                        if product_id:
                            product_id_clean = product_id.strip()
                            
                            # First try to find by exact code match
                            try:
                                product = Product.objects.get(code=product_id_clean)
                            except Product.DoesNotExist:
                                pass
                            
                            # If no exact code match, try by partial code match
                            if not product:
                                product = Product.objects.filter(code__icontains=product_id_clean).first()
                            
                            # If still no product found, try by exact name match
                            if not product:
                                product = Product.objects.filter(name_en__iexact=product_id_clean).first()
                            
                            # If still no product found, try by partial name match
                            if not product:
                                product = Product.objects.filter(name_en__icontains=product_id_clean).first()
                            
                            # If still no product found, try by Arabic name
                            if not product:
                                product = Product.objects.filter(name_ar__icontains=product_id_clean).first()
                            
                            # If still no product found, try by product ID (numeric)
                            if not product and product_id_clean.isdigit():
                                try:
                                    product = Product.objects.get(id=int(product_id_clean))
                                except (Product.DoesNotExist, ValueError):
                                    pass
                        
                        # If product not found, log warning but continue
                        if product_id and not product:
                            warnings.append(f"Row {row_num}: Product not found for ID/Code '{product_id}'. Order will be created without product link.")
                        
                        # Check if order already exists
                        if order_code and Order.objects.filter(order_code=order_code).exists():
                            errors.append(f"Row {row_num}: Order code '{order_code}' already exists")
                            error_count += 1
                            continue
                        
                        # Create order (seller is always the current user for sellers)
                        order = Order.objects.create(
                            order_code=order_code or _generate_order_code(),
                            customer=customer_name,
                            customer_phone=mobile_number,
                            shipping_address=address,
                            street_address='',  # Street address not available in CSV import
                            product=product,  # Can be None if product not found
                            quantity=quantity,
                            price_per_unit=price,
                            notes=notes,
                            date=order_date,
                            status='pending',
                            seller=request.user,
                            seller_email=request.user.email
                        )
                        
                        success_count += 1
                        
                        # Create audit log
                        AuditLog.objects.create(
                            user=request.user,
                            action='import',
                            entity_type='Order',
                            entity_id=str(order.id),
                            description=f"Imported order {order.order_code} from CSV" + (f" with product: {product.name_en} (Code: {product.code})" if product else " without product link")
                        )
                        
                    except Exception as e:
                        errors.append(f"Row {row_num}: {str(e)}")
                        error_count += 1
                
                # Show results
                if success_count > 0:
                    messages.success(request, f'Successfully imported {success_count} orders.')
                    
                    # Create notification for successful import
                    create_seller_notification(
                        seller=request.user,
                        title="Orders Imported Successfully",
                        message=f"Successfully imported {success_count} orders from CSV file.",
                        notification_type='data_import',
                        priority='medium',
                        related_object_type='order',
                        related_url="/sellers/orders/"
                    )
                
                if warnings:
                    messages.info(request, f'Found {len(warnings)} warnings during import.')
                    for warning in warnings[:5]:  # Show first 5 warnings
                        messages.warning(request, warning)
                    if len(warnings) > 5:
                        messages.warning(request, f'... and {len(warnings) - 5} more warnings.')
                
                if error_count > 0:
                    messages.error(request, f'Failed to import {error_count} orders. Check the errors below.')
                    for error in errors[:10]:  # Show first 10 errors
                        messages.error(request, error)
                    if len(errors) > 10:
                        messages.error(request, f'... and {len(errors) - 10} more errors.')
                
                return redirect('sellers:orders')
                
            except Exception as e:
                messages.error(request, f'Error processing file: {str(e)}')
                print(f"Import error: {e}")
        else:
            messages.error(request, 'Please correct the errors below.')
            print(f"Form errors: {form.errors}")
    else:
        form = OrderImportForm(user=request.user)
    
    return render(request, 'sellers/import_orders.html', {'form': form})

@login_required
def export_orders(request):
    """Export orders to CSV - RESTRICTED TO SUPER ADMIN ONLY."""
    from users.models import AuditLog

    # SECURITY: Restrict data export to Super Admin only (P0 CRITICAL requirement)
    if not request.user.is_superuser:
        from utils.views import permission_denied_authenticated
        AuditLog.objects.create(
            user=request.user,
            action='unauthorized_export_attempt',
            entity_type='order',
            description=f"Unauthorized attempt to export orders by {request.user.email}",
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        return permission_denied_authenticated(
            request,
            message="Data export is restricted to Super Admin only for security compliance."
        )
    
    # Get orders based on user role
    if request.user.has_role('Seller'):
        # Sellers export only their own orders
        orders = Order.objects.select_related('agent', 'seller', 'product').filter(seller=request.user).order_by('-date')
    else:
        # Admins and super admins export all orders
        orders = Order.objects.select_related('agent', 'seller', 'product').all().order_by('-date')
    
    # Apply search filter if provided
    search_query = request.GET.get('search', '')
    if search_query:
        orders = orders.filter(
            Q(order_code__icontains=search_query) |
            Q(customer__icontains=search_query) |
            Q(product__name_en__icontains=search_query) |
            Q(product__name_ar__icontains=search_query)
        )
    
    # Apply status filter if provided
    status_filter = request.GET.get('status', '')
    if status_filter:
        orders = orders.filter(status=status_filter)
    
    # Create CSV response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="orders_export_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'Order Code', 'Customer', 'Customer Phone', 'Product', 'Quantity', 
        'Total Price (AED)', 'Status', 'Date', 'Seller Email', 'Notes'
    ])
    
    for order in orders:
        writer.writerow([
            order.order_code,
            order.customer,
            order.customer_phone or '',
            order.product.name_en if order.product else '',
            order.quantity,
            order.total_price_aed,
            order.status,
            order.date.strftime('%Y-%m-%d %H:%M:%S') if order.date else '',
            order.seller_email or '',
            order.notes or ''
        ])
    
    # Audit log for successful export (P0 CRITICAL security requirement)
    AuditLog.objects.create(
        user=request.user,
        action='data_export',
        entity_type='order',
        description=f"Exported {orders.count()} orders to CSV",
        ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT', '')
    )

    # Create notification for successful export
    create_seller_notification(
        seller=request.user,
        title="Orders Exported Successfully",
        message=f"Successfully exported {orders.count()} orders to CSV file.",
        notification_type='data_export',
        priority='low',
        related_object_type='order',
        related_url="/sellers/orders/"
    )

    return response

@login_required
def order_detail(request, order_id):
    """View a specific order."""
    if not has_seller_role(request.user):
        messages.error(request, "ليس لديك صلاحية للدخول لهذه الصفحة.")
        return redirect('dashboard:index')
    order = get_object_or_404(Order, id=order_id)
    
    # Check permissions - sellers can ONLY view orders they created
    if request.user.has_role('Seller') and order.seller != request.user:
        messages.error(request, "You don't have permission to view this order.")
        return redirect('sellers:orders')
        
    return render(request, 'sellers/order_detail.html', {
        'order': order,
    })

@login_required
def order_update(request, order_id):
    """Update a specific order."""
    if not has_seller_role(request.user):
        messages.error(request, "ليس لديك صلاحية للدخول لهذه الصفحة.")
        return redirect('dashboard:index')
    
    order = get_object_or_404(Order, id=order_id)
    
    # Check permissions - sellers can ONLY edit orders they created
    if request.user.has_role('Seller') and order.seller != request.user:
        messages.error(request, "You don't have permission to edit this order.")
        return redirect('sellers:orders')
    
    # Redirect to the main orders update page
    return redirect('orders:update', order_id=order_id)

@login_required
def sourcing_request_list(request):
    """List sourcing requests."""
    if not has_seller_role(request.user):
        messages.error(request, "ليس لديك صلاحية للدخول لهذه الصفحة.")
        return redirect('dashboard:index')
    # Check if user has Seller role or is Super Admin
    if not (request.user.has_role('Seller') or request.user.is_superuser or request.user.has_role('Super Admin')):
        messages.error(request, "You don't have permission to access this page.")
        return redirect('dashboard:index')
    
    # Import sourcing models
    from sourcing.models import SourcingRequest
    
    # Get sourcing requests for the current user
    sourcing_requests = SourcingRequest.objects.filter(seller=request.user).order_by('-created_at')
    
    # Add pagination
    from django.core.paginator import Paginator
    paginator = Paginator(sourcing_requests, 10)  # Show 10 per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'sellers/sourcing_requests.html', {
        'sourcing_requests': sourcing_requests,
        'page_obj': page_obj,
    })

@login_required
def sourcing_request_create(request):
    """Create a new sourcing request."""
    if not has_seller_role(request.user):
        messages.error(request, "ليس لديك صلاحية للدخول لهذه الصفحة.")
        return redirect('dashboard:index')
    if request.method == 'POST':
        # Handle AJAX form submission
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            from django.http import JsonResponse
            from sourcing.models import SourcingRequest
            from django.utils import timezone
            
            try:
                # Handle file upload
                product_image = None
                if 'product_image' in request.FILES:
                    product_image = request.FILES['product_image']
                
                # Create sourcing request
                sourcing_request = SourcingRequest.objects.create(
                    seller=request.user,
                    product_name=request.POST.get('product_name') or 'Product Request',
                    product_image=product_image,
                    product_url=request.POST.get('product_url', ''),
                    carton_quantity=int(request.POST.get('carton_quantity', 0)),
                    unit_quantity=int(request.POST.get('unit_quantity', 0)),
                    source_country=request.POST.get('source_country', 'China'),
                    destination_country=request.POST.get('destination_country', 'UAE'),
                    finance_source='seller' if request.POST.get('finance_source') == 'self_financed' else 'company',
                    priority=request.POST.get('priority', 'medium'),
                    status='submitted',
                    notes=request.POST.get('notes', ''),
                    submitted_at=timezone.now()
                )
                
                # Skip notifications for now to avoid errors
                pass
                
                return JsonResponse({
                    'success': True,
                    'message': 'Sourcing request created successfully!',
                    'request_id': sourcing_request.id
                })
                
            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'error': str(e)
                })
        
        # Handle regular form submission (fallback)
        try:
            # Handle file upload
            product_image = None
            if 'product_image' in request.FILES:
                product_image = request.FILES['product_image']
            
            # Create sourcing request
            sourcing_request = SourcingRequest.objects.create(
                seller=request.user,
                product_name=request.POST.get('product_name') or 'Product Request',
                product_image=product_image,
                product_url=request.POST.get('product_url', ''),
                carton_quantity=int(request.POST.get('carton_quantity', 0)),
                unit_quantity=int(request.POST.get('unit_quantity', 0)),
                source_country=request.POST.get('source_country', 'China'),
                destination_country=request.POST.get('destination_country', 'UAE'),
                finance_source='seller' if request.POST.get('finance_source') == 'self_financed' else 'company',
                priority=request.POST.get('priority', 'medium'),
                status='submitted',
                notes=request.POST.get('notes', ''),
                submitted_at=timezone.now()
            )
            
            messages.success(request, 'Sourcing request created successfully!')
            return redirect('sellers:sourcing_requests')
            
        except Exception as e:
            messages.error(request, f'Error creating sourcing request: {str(e)}')
            return redirect('sellers:sourcing_request_create')
    
    # GET request - show form page (for non-JS users)
    products = Product.objects.filter(seller=request.user).order_by('-created_at')
    
    return render(request, 'sellers/sourcing_request_create.html', {
        'products': products,
    })

@login_required
def sourcing_request_detail(request, request_id):
    """View a specific sourcing request."""
    if not has_seller_role(request.user):
        messages.error(request, "ليس لديك صلاحية للدخول لهذه الصفحة.")
        return redirect('dashboard:index')
    # Check if user has Seller role or is Super Admin
    if not (request.user.has_role('Seller') or request.user.is_superuser or request.user.has_role('Super Admin')):
        messages.error(request, "You don't have permission to access this page.")
        return redirect('dashboard:index')
    
    from sourcing.models import SourcingRequest
    from django.shortcuts import get_object_or_404
    
    sourcing_request = get_object_or_404(SourcingRequest, id=request_id, seller=request.user)
    
    return render(request, 'sellers/sourcing_request_detail.html', {
        'sourcing_request': sourcing_request,
    })

@login_required
def finance(request):
    """Seller finance overview and analytics."""
    if not has_seller_role(request.user):
        messages.error(request, "ليس لديك صلاحية للدخول لهذه الصفحة.")
        return redirect('dashboard:index')
    # Check if user has Seller role or is Super Admin
    if not (request.user.has_role('Seller') or request.user.is_superuser or request.user.has_role('Super Admin')):
        messages.error(request, "You don't have permission to access this page.")
        return redirect('dashboard:index')
    
    from django.db.models import Count, Avg
    from django.utils import timezone
    from datetime import datetime, timedelta
    import calendar
    
    # Get all orders for this seller (both direct seller and product seller)
    all_orders = Order.objects.filter(
        Q(seller=request.user) | Q(product__seller=request.user)
    ).distinct()
    
    # Calculate total sales
    total_sales = sum(order.total_price for order in all_orders)
    
    # Calculate monthly sales (current month)
    current_month_start = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    monthly_orders = all_orders.filter(date__gte=current_month_start)
    monthly_sales = sum(order.total_price for order in monthly_orders)
    
    # Calculate weekly sales (current week)
    current_week_start = timezone.now() - timedelta(days=timezone.now().weekday())
    current_week_start = current_week_start.replace(hour=0, minute=0, second=0, microsecond=0)
    weekly_orders = all_orders.filter(date__gte=current_week_start)
    weekly_sales = sum(order.total_price for order in weekly_orders)
    
    # Calculate daily sales (today)
    today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    daily_orders = all_orders.filter(date__gte=today_start)
    daily_sales = sum(order.total_price for order in daily_orders)
    
    # Calculate sales by month for the last 6 months
    sales_by_period = {}
    for i in range(6):
        month_date = timezone.now() - timedelta(days=30*i)
        month_start = month_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if i > 0:
            month_end = month_start + timedelta(days=32)
            month_end = month_end.replace(day=1) - timedelta(days=1)
        else:
            month_end = timezone.now()
        
        month_orders = all_orders.filter(
            date__gte=month_start,
            date__lte=month_end
        )
        month_sales = sum(order.total_price for order in month_orders)
        
        month_name = month_start.strftime('%b')
        sales_by_period[month_name] = month_sales
    
    # Get top selling products
    top_products = []
    products = Product.objects.filter(seller=request.user, is_approved=True)
    
    for product in products:
        product_orders = all_orders.filter(product=product)
        sales_volume = product_orders.count()
        revenue = sum(order.total_price for order in product_orders)
        
        if sales_volume > 0:
            # Calculate growth (simple comparison with previous period)
            previous_period_start = timezone.now() - timedelta(days=60)
            previous_period_end = timezone.now() - timedelta(days=30)
            current_period_start = timezone.now() - timedelta(days=30)
            
            previous_sales = product_orders.filter(
                date__gte=previous_period_start,
                date__lte=previous_period_end
            ).count()
            
            current_sales = product_orders.filter(
                date__gte=current_period_start
            ).count()
            
            if previous_sales > 0:
                growth = ((current_sales - previous_sales) / previous_sales) * 100
            else:
                growth = 100 if current_sales > 0 else 0
            
            top_products.append({
                'name': product.name_en or product.name_ar or 'Unnamed Product',
                'sku': product.code,
                'image': product.image,
                'sales_volume': sales_volume,
                'revenue': f"AED {revenue:,.0f}",
                'growth': round(growth, 1)
            })
    
    # Sort by sales volume and take top 5
    top_products.sort(key=lambda x: x['sales_volume'], reverse=True)
    top_products = top_products[:5]
    
    # Format currency values
    context = {
        'total_sales': f"AED {total_sales:,.0f}",
        'monthly_sales': f"AED {monthly_sales:,.0f}",
        'weekly_sales': f"AED {weekly_sales:,.0f}",
        'daily_sales': f"AED {daily_sales:,.0f}",
        'sales_by_period': sales_by_period,
        'top_products': top_products,
    }
    
    return render(request, 'sellers/finance.html', context)



@login_required
def inventory(request):
    """Show inventory management page for seller products."""
    if not has_seller_role(request.user):
        messages.error(request, "ليس لديك صلاحية للدخول لهذه الصفحة.")
        return redirect('dashboard:index')
    
    # Handle export request
    if request.GET.get('export') == 'csv':
        import csv
        from django.http import HttpResponse
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="inventory_export.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Product Name', 'SKU', 'Description', 'Available Quantity', 'Total Quantity', 'Selling Price', 'Purchase Price', 'Product Link', 'Status', 'Created Date'])
        
        products = Product.objects.filter(seller=request.user, is_approved=True).order_by('-created_at')
        
        for product in products:
            writer.writerow([
                product.name_en or product.name_ar or 'Unnamed Product',
                product.code,
                product.description[:100] + '...' if len(product.description) > 100 else product.description,
                product.available_quantity,
                product.total_quantity,
                product.selling_price,
                product.purchase_price or 'N/A',
                product.product_link or 'N/A',
                'In Stock' if product.available_quantity > 0 else 'Out of Stock',
                product.created_at.strftime('%Y-%m-%d')
            ])
        
        # Create notification for successful inventory export
        create_seller_notification(
            seller=request.user,
            title="Inventory Exported Successfully",
            message=f"Successfully exported inventory data for {products.count()} products to CSV file.",
            notification_type='data_export',
            priority='low',
            related_object_type='product',
            related_url="/sellers/inventory/"
        )
        
        return response
    
    # Get all products with inventory information
    products = Product.objects.filter(seller=request.user, is_approved=True).order_by('-created_at')
    
    
    # Calculate inventory statistics
    total_inventory = sum(product.total_quantity for product in products)
    available_inventory = sum(product.available_quantity for product in products)
    in_delivery_inventory = max(0, total_inventory - available_inventory)
    
    # Calculate low stock items (products with 10 or fewer items)
    low_stock_count = 0
    out_of_stock_count = 0
    low_stock_products = []
    
    for product in products:
        if product.available_quantity <= 0:
            out_of_stock_count += 1
        elif product.available_quantity <= 10:
            low_stock_count += 1
            low_stock_products.append({
                'product': product,
                'total_quantity': product.available_quantity,
                'min_quantity': 10
            })
            
            # Create low stock notification if quantity is very low (5 or fewer)
            if product.available_quantity <= 5:
                create_seller_notification(
                    seller=request.user,
                    title="Low Stock Alert",
                    message=f"Product '{product.name_en}' is running very low on stock. Current quantity: {product.available_quantity}",
                    notification_type='inventory_low',
                    priority='high',
                    related_object_type='product',
                    related_object_id=product.id,
                    related_url=f"/sellers/products/{product.id}/"
                )
    
    # Get warehouses count (placeholder for now)
    warehouses_count = 0
    
    return render(request, 'sellers/inventory.html', {
        'products': products,
        'total_products': products.count(),
        'total_inventory': total_inventory,
        'available_inventory': available_inventory,
        'in_delivery_inventory': in_delivery_inventory,
        'low_stock_count': low_stock_count,
        'out_of_stock_count': out_of_stock_count,
        'low_stock_products': low_stock_products,
        'warehouses_count': warehouses_count,
    })

@login_required
def warehouses(request):
    """Redirect seller to inventory warehouses page."""
    if not has_seller_role(request.user):
        messages.error(request, "ليس لديك صلاحية للدخول لهذه الصفحة.")
        return redirect('dashboard:index')
    
    # Redirect to inventory warehouses page
    return redirect('inventory:warehouses')

@login_required
def redirect_to_notifications(request, notification_id=None):
    """Redirect sellers to the universal notifications app"""
    return redirect('notifications:index')

@login_required
def seller_list(request):
    """Admin view to list all sellers with their basic information."""
    # Check if user has admin permissions
    # Explicitly block Packaging Agent
    if request.user.has_role('Packaging Agent') and not (request.user.has_role('Admin') or request.user.has_role('Super Admin') or request.user.is_superuser):
        from utils.views import permission_denied_authenticated
        return permission_denied_authenticated(
            request,
            message="You don't have permission to access this page. This page is restricted to Admin and Super Admin only."
        )
    if not (request.user.has_role('Super Admin') or request.user.has_role('Admin') or request.user.is_superuser):
        messages.error(request, "You don't have permission to access this page.")
        return redirect('dashboard:index')
    
    from django.contrib.auth import get_user_model
    from roles.models import Role
    
    User = get_user_model()
    
    # Get seller role
    seller_role = Role.objects.filter(name='Seller').first()
    
    if seller_role:
        # Get all users with Seller role
        sellers = User.objects.filter(
            user_roles__role=seller_role,
            user_roles__is_active=True
        ).distinct().order_by('first_name', 'last_name')
    else:
        sellers = User.objects.none()
    
    # Handle search
    search_query = request.GET.get('search', '')
    if search_query:
        sellers = sellers.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(full_name__icontains=search_query)
        )
    
    # Create simple seller data list
    sellers_data = []
    for seller in sellers:
        seller_data = {
            'seller': seller,
        }
        sellers_data.append(seller_data)
    
    # Pagination
    paginator = Paginator(sellers_data, 20)  # Show 20 sellers per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'sellers': page_obj,
        'search_query': search_query,
        'total_sellers': sellers.count(),
    }
    
    return render(request, 'sellers/seller_list.html', context)

@login_required
def get_seller_products(request, seller_id):
    """Get seller products as JSON for modal display."""
    try:
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        seller = get_object_or_404(User, id=seller_id)
        products = Product.objects.filter(seller=seller).order_by('-created_at')
        
        products_data = []
        for product in products:
            products_data.append({
                'id': product.id,
                'name_en': product.name_en,
                'name_ar': product.name_ar,
                'code': product.code,
                'selling_price': float(product.selling_price),
                'stock_quantity': product.stock_quantity,
                'is_approved': product.is_approved,
                'created_at': product.created_at.strftime('%Y-%m-%d'),
            })
        
        return JsonResponse({
            'success': True,
            'products': products_data,
            'seller_name': seller.get_full_name() or seller.email
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
def seller_create(request):
    """Admin view to create a new seller."""
    # Check if user has admin permissions
    if not (request.user.has_role('Super Admin') or request.user.has_role('Admin') or request.user.is_superuser):
        messages.error(request, "You don't have permission to access this page.")
        return redirect('dashboard:index')

    from django.contrib.auth import get_user_model
    from roles.models import Role, UserRole

    User = get_user_model()

    if request.method == 'POST':
        # Get form data
        email = request.POST.get('email')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        phone = request.POST.get('phone', '')
        password = request.POST.get('password')

        # Validate email
        if User.objects.filter(email=email).exists():
            messages.error(request, 'A user with this email already exists.')
            return render(request, 'sellers/seller_create.html')

        try:
            # Create user
            user = User.objects.create_user(
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                phone=phone
            )

            # Assign Seller role
            seller_role = Role.objects.filter(name='Seller').first()
            if seller_role:
                UserRole.objects.create(user=user, role=seller_role, is_active=True)

            # Log the action
            AuditLog.objects.create(
                user=request.user,
                action='create_seller',
                details=f'Created seller: {email}'
            )

            messages.success(request, f'Seller {first_name} {last_name} created successfully.')
            return redirect('sellers:seller_list')

        except Exception as e:
            messages.error(request, f'Error creating seller: {str(e)}')

    return render(request, 'sellers/seller_create.html')

