from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.db.models import Q
from django.contrib import messages
from django.utils import timezone
from .models import Order, OrderItem
from .forms import OrderForm, OrderStatusUpdateForm, OrderImportForm
from users.models import User
from users.models import AuditLog
from sellers.models import Product
from settings.models import DeliveryCompany
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.urls import reverse_lazy
import csv
import io
from datetime import datetime


@login_required
def order_list(request):
    """View for listing all orders with comprehensive filtering."""
    # Security check - restrict access based on user role
    if request.user.has_role('Seller'):
        # Sellers should be redirected to their own orders page
        messages.error(request, "Please use the Seller Orders page to view your orders.")
        return redirect('sellers:orders')
    elif not (request.user.has_role('Admin') or request.user.has_role('Super Admin') or 
              request.user.has_role('Call Center Agent') or request.user.has_role('Call Center Manager') or
              request.user.has_role('Packaging Agent') or request.user.has_role('Stock Keeper') or
              request.user.has_role('Delivery Agent')):
        # Only admins, call center agents, call center managers, packaging agents, stock keepers, and delivery agents can access admin orders
        messages.error(request, "You don't have permission to view this page.")
        return redirect('dashboard:index')
    
    # Get filter parameters
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    workflow_status_filter = request.GET.get('workflow_status', '')
    seller_filter = request.GET.get('seller', '')
    agent_filter = request.GET.get('agent', '')
    emirate_filter = request.GET.get('emirate', '')
    date_filter = request.GET.get('date', '')
    amount_min = request.GET.get('amount_min', '')
    amount_max = request.GET.get('amount_max', '')
    payment_status_filter = request.GET.get('payment_status', '')
    sort_by = request.GET.get('sort', '-created_at')
    
    # Get all orders with related data
    orders = Order.objects.select_related('agent', 'seller', 'product').prefetch_related('items').all()
    
    # Apply filters
    if search_query:
        orders = orders.filter(
            Q(order_code__icontains=search_query) |
            Q(customer__icontains=search_query) |
            Q(customer_phone__icontains=search_query) |
            Q(seller__email__icontains=search_query) |
            Q(product__name_en__icontains=search_query) |
            Q(product__name_ar__icontains=search_query) |
            Q(notes__icontains=search_query)
        )
    
    if status_filter:
        orders = orders.filter(status=status_filter)
    
    if workflow_status_filter:
        orders = orders.filter(workflow_status=workflow_status_filter)
    
    if seller_filter:
        orders = orders.filter(seller_id=seller_filter)
    
    if agent_filter:
        orders = orders.filter(agent_id=agent_filter)
    
    if emirate_filter:
        orders = orders.filter(state=emirate_filter)
    
    if date_filter:
        today = timezone.now().date()
        if date_filter == 'today':
            orders = orders.filter(created_at__date=today)
        elif date_filter == 'yesterday':
            yesterday = today - timezone.timedelta(days=1)
            orders = orders.filter(created_at__date=yesterday)
        elif date_filter == 'week':
            week_ago = today - timezone.timedelta(days=7)
            orders = orders.filter(created_at__date__gte=week_ago)
        elif date_filter == 'month':
            orders = orders.filter(created_at__month=today.month, created_at__year=today.year)
        elif date_filter == 'quarter':
            quarter_start = today.replace(day=1, month=((today.month - 1) // 3) * 3 + 1)
            orders = orders.filter(created_at__date__gte=quarter_start)
        elif date_filter == 'year':
            orders = orders.filter(created_at__year=today.year)
    
    if amount_min:
        try:
            orders = orders.filter(price_per_unit__gte=float(amount_min))
        except ValueError:
            pass
    
    if amount_max:
        try:
            orders = orders.filter(price_per_unit__lte=float(amount_max))
        except ValueError:
            pass
    
    if payment_status_filter:
        # Since Order model doesn't have payment_status field, we'll skip this filter
        # You can implement payment status filtering through related Payment model if needed
        pass
    
    # Apply sorting
    orders = orders.order_by(sort_by)
    
    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(orders, 20)  # Show 20 orders per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get filter options
    from sellers.models import Seller
    sellers = Seller.objects.all().order_by('name')
    agents = User.objects.filter(
        user_roles__role__name__in=['Call Center Agent', 'Call Center Manager'],
        user_roles__is_active=True,
        is_active=True
    ).distinct().order_by('first_name', 'last_name')
    
    # Get unique emirates
    emirates = Order.objects.values_list('state', flat=True).distinct().exclude(state__isnull=True).exclude(state='')
    
    # Calculate statistics (before filtering for display)
    all_orders = Order.objects.all()
    total_orders = all_orders.count()
    pending_orders = all_orders.filter(status='pending').count()
    confirmed_orders = all_orders.filter(status='confirmed').count()
    processing_orders = all_orders.filter(status='processing').count()
    packaged_orders = all_orders.filter(status='packaged').count()
    shipped_orders = all_orders.filter(status='shipped').count()
    delivered_orders = all_orders.filter(status='delivered').count()
    cancelled_orders = all_orders.filter(status='cancelled').count()
    postponed_orders = all_orders.filter(status='postponed').count()
    
    # Payment statistics - Since Order model doesn't have payment_status field
    # These are placeholder values. You can implement real payment status filtering
    # through related Payment model if needed
    paid_orders = 0  # Placeholder
    pending_payment_orders = 0  # Placeholder
    
    # Revenue calculation - Use price_per_unit field instead of total_price_aed property
    from django.db.models import Sum, F
    total_revenue = all_orders.aggregate(
        total=Sum(F('price_per_unit') * F('quantity'))
    )['total'] or 0
    
    context = {
        'orders': page_obj,
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'confirmed_orders': confirmed_orders,
        'processing_orders': processing_orders,
        'packaged_orders': packaged_orders,
        'shipped_orders': shipped_orders,
        'delivered_orders': delivered_orders,
        'cancelled_orders': cancelled_orders,
        'postponed_orders': postponed_orders,
        'paid_orders': paid_orders,
        'pending_payment_orders': pending_payment_orders,
        'total_revenue': total_revenue,
        'sellers': sellers,
        'agents': agents,
        'emirates': emirates,
        'current_filters': {
            'search': search_query,
            'status': status_filter,
            'workflow_status': workflow_status_filter,
            'seller': seller_filter,
            'agent': agent_filter,
            'emirate': emirate_filter,
            'date': date_filter,
            'amount_min': amount_min,
            'amount_max': amount_max,
            'payment_status': payment_status_filter,
            'sort': sort_by,
        },
    }
    return render(request, 'orders/order_list.html', context)

@login_required
def order_detail(request, order_id):
    """Detail view for a specific order."""
    order = get_object_or_404(Order, id=order_id)
    
    # Security check - restrict access based on user role
    if request.user.has_role('Seller'):
        # Sellers can ONLY view orders they created
        if order.seller != request.user:
            messages.error(request, "You don't have permission to view this order.")
            return redirect('sellers:orders')
    elif not (request.user.has_role('Admin') or request.user.has_role('Super Admin') or 
              request.user.has_role('Call Center Agent') or request.user.has_role('Call Center Manager') or
              request.user.has_role('Packaging Agent') or request.user.has_role('Stock Keeper') or
              request.user.has_role('Delivery Agent')):
        # Only admins, call center agents, call center managers, packaging agents, stock keepers, and delivery agents can access admin orders
        messages.error(request, "You don't have permission to view this order.")
        return redirect('dashboard:index')
    
    # Get order items for display
    order_items = order.items.all()
    
    # Create formset for editing (if needed)
    from .forms import OrderItemFormSet
    order_item_formset = OrderItemFormSet(instance=order)
    
    context = {
        'order': order,
        'order_items': order_items,
        'order_item_formset': order_item_formset,
    }
    return render(request, 'orders/order_detail.html', context)

@login_required
def create_order(request):
    """View for creating a new order."""
    # Only sellers, admins, and call center staff can create orders
    if not (request.user.has_role('Seller') or 
        request.user.has_role('Admin') or 
        request.user.has_role('Super Admin') or
        request.user.has_role('Call Center Agent') or 
        request.user.has_role('Call Center Manager') or
        request.user.has_role('Packaging Agent') or 
        request.user.has_role('Stock Keeper') or
        request.user.has_role('Delivery Agent')):
        messages.error(request, "You don't have permission to create orders.")
        return redirect('orders:list')
        
    # Debug user roles
    print("=== CREATE ORDER PERMISSION DEBUG ===")
    print(f"User: {request.user}")
    print(f"Primary role: {request.user.primary_role.name if request.user.primary_role else None}")
    print(f"Has Seller role: {request.user.has_role('Seller')}")
    print(f"Has Admin role: {request.user.has_role('Admin')}")
    print(f"Has Call Center Agent role: {request.user.has_role('Call Center Agent')}")
    print(f"All roles: {list(request.user.user_roles.values_list('role__name', flat=True))}")
    print("====================================")
    
    if request.method == 'POST':
        # Debug: Print all POST data
        print("=== CREATE ORDER POST DATA DEBUG ===")
        print(f"Request method: {request.method}")
        print(f"Request user: {request.user}")
        print(f"Request user role: {request.user.primary_role.name if request.user.primary_role else 'No role'}")
        
        for key, value in request.POST.items():
            print(f"POST[{key}]: {value}")
        print("=====================================")
        
        form = OrderForm(request.POST, user=request.user)
        
        # Debug form validation
        print("=== FORM VALIDATION DEBUG ===")
        print(f"Form is valid: {form.is_valid()}")
        if not form.is_valid():
            print(f"Form errors: {form.errors}")
        print("=============================")
        
        if form.is_valid():
            order = form.save(commit=False)
            
            # Get user's primary role
            user_role = request.user.primary_role.name if request.user.primary_role else None
            
            # Set the seller based on user role
            if user_role == 'Seller':
                order.seller = request.user
                order.seller_email = request.user.email
                # Ensure status is set to pending for sellers
                order.status = 'pending'
                # Ensure workflow status is set correctly
                order.workflow_status = 'seller_submitted'
            elif user_role in ['Admin', 'Super Admin']:
                # For admins, use the selected seller
                selected_seller = form.cleaned_data.get('seller')
                if selected_seller:
                    order.seller = selected_seller
                    order.seller_email = selected_seller.email
                else:
                    # If no seller selected, use current user
                    order.seller = request.user
                    order.seller_email = request.user.email
                # Set workflow status for admin-created orders
                order.workflow_status = 'callcenter_review'
            else:
                # For other roles, use current user
                order.seller = request.user
                order.seller_email = request.user.email
                # Set workflow status for other roles
                order.workflow_status = 'callcenter_review'
            
            # Generate order code if not provided
            if not order.order_code:
                order.order_code = _generate_order_code()
            
            # Handle agent assignment
            assignment_type = request.POST.get('assignment_type', 'auto')
            
            if assignment_type == 'manual':
                # Manual assignment - use selected agent
                if order.agent:
                    order.assigned_at = timezone.now()
            else:
                # Auto assignment - distribute among available agents
                order.agent = _get_next_available_agent()
                if order.agent:
                    order.assigned_at = timezone.now()
            
            order.save()
            
            # Process multiple products
            product_ids = request.POST.getlist('product_ids[]')
            quantities = request.POST.getlist('quantities[]')
            prices = request.POST.getlist('prices[]')
            
            if product_ids and quantities and prices:
                # Remove existing order items (if any)
                order.items.all().delete()
                
                # Create order items for each product
                for i in range(len(product_ids)):
                    if product_ids[i] and quantities[i] and prices[i]:
                        try:
                            product = Product.objects.get(id=product_ids[i])
                            quantity = int(quantities[i])
                            price = float(prices[i])
                            
                            # Create order item
                            OrderItem.objects.create(
                                order=order,
                                product=product,
                                quantity=quantity,
                                price=price
                            )
                            
                            # Set the first product as the main product for backward compatibility
                            if i == 0:
                                order.product = product
                                order.quantity = quantity
                                order.price_per_unit = price
                                order.save()
                                
                        except (Product.DoesNotExist, ValueError) as e:
                            print(f"Error creating order item: {e}")
                            continue
            
            # Calculate total price
            total_price = order.total_price
            
            # Create audit log
            AuditLog.objects.create(
                user=request.user,
                action='create',
                entity_type='Order',
                entity_id=str(order.id),
                description=f"Created new order {order.order_code}"
            )
            
            messages.success(request, f"Order {order.order_code} created successfully!")
            
            # Redirect based on user role
            if user_role == 'Seller':
                return redirect('sellers:order_detail', order_id=order.id)
            else:
                return redirect('orders:detail', order_id=order.id)
    else:
        form = OrderForm(user=request.user)
    
    # Get available products
    products = Product.objects.filter(is_approved=True)
    
    return render(request, 'orders/create_order.html', {
        'form': form,
        'products': products
    })

@login_required
def update_order(request, order_id):
    """View for updating an existing order."""
    order = get_object_or_404(Order, id=order_id)
    
    # Check if user has permission to edit this order
    if not _can_edit_order(request.user, order):
        if order.status == 'confirmed':
            messages.error(request, f"Order {order.order_code} is confirmed and cannot be edited.")
        else:
            messages.error(request, "You don't have permission to edit this order.")
        return redirect('orders:detail', order_id=order.id)
    
    if request.method == 'POST':
        # Clean POST data to remove problematic fields
        post_data = request.POST.copy()
        # Remove any fields that might cause issues
        problematic_fields = ['is_active', 'is_approved', 'created_at', 'updated_at']
        for field in problematic_fields:
            if field in post_data:
                del post_data[field]
        
        form = OrderForm(post_data, instance=order, user=request.user)
        
        # Debug form validation
        print("=== FORM VALIDATION DEBUG ===")
        print(f"Form is valid: {form.is_valid()}")
        if not form.is_valid():
            print(f"Form errors: {form.errors}")
        print("=============================")
        
        if form.is_valid():
            # Save the form
            updated_order = form.save(commit=False)
            
            # Handle seller updates based on user role
            user_role = request.user.primary_role.name if request.user.primary_role else None
            
            # Debug logging
            print(f"Form data - Agent: {form.cleaned_data.get('agent')}")
            print(f"Form data - Seller: {form.cleaned_data.get('seller')}")
            print(f"User role: {user_role}")
            print(f"Original order agent: {order.agent}")
            print(f"Form agent field value: {form.cleaned_data.get('agent')}")
            
            # Handle agent field update
            agent_value = form.cleaned_data.get('agent')
            print(f"Agent value from form: {agent_value}")
            print(f"Agent value type: {type(agent_value)}")
            
            # Check if agent field was submitted in the form data
            if 'agent' in request.POST:
                print(f"Agent field found in POST data: {request.POST.get('agent')}")
                if request.POST.get('agent'):  # If agent value is not empty
                    updated_order.agent = agent_value
                    updated_order.assigned_at = timezone.now()
                    print(f"Setting agent to: {agent_value}")
                else:  # If agent value is empty (clearing assignment)
                    updated_order.agent = None
                    updated_order.assigned_at = None
                    print("Clearing agent assignment")
            else:
                # If agent field was not submitted, preserve original
                updated_order.agent = order.agent
                updated_order.assigned_at = order.assigned_at
                print(f"Agent field not in POST data, preserving original agent: {order.agent}")
            
            # Handle seller updates based on user role
            if user_role in ['Admin', 'Super Admin', 'Call Center Manager']:
                # Admins and managers can change seller
                if form.cleaned_data.get('seller'):
                    updated_order.seller = form.cleaned_data['seller']
                    updated_order.seller_email = form.cleaned_data['seller'].email
                    print(f"Setting seller to: {form.cleaned_data['seller']}")
            elif user_role == 'Seller':
                # Sellers can only update basic order details, not seller or agent
                # Preserve original seller information
                updated_order.seller = order.seller
                updated_order.seller_email = order.seller_email
                print("Seller - preserving original seller information")
            
            # Auto-set seller email from seller if not set
            if updated_order.seller and not updated_order.seller_email:
                updated_order.seller_email = updated_order.seller.email
                print(f"Auto-setting seller email to: {updated_order.seller_email}")
            
            # Ensure the agent field is properly set
            print(f"Final agent value before save: {updated_order.agent}")
            print(f"Final seller value before save: {updated_order.seller}")
            
            # Save the order
            updated_order.save()
            print(f"Order saved successfully with agent: {updated_order.agent}")
            
            # Recalculate total price
            total_price = updated_order.quantity * updated_order.price_per_unit
            
            # Create audit log
            AuditLog.objects.create(
                user=request.user,
                action='update',
                entity_type='Order',
                entity_id=str(updated_order.id),
                description=f"Updated order {updated_order.order_code}"
            )
            
            messages.success(request, f"Order {updated_order.order_code} updated successfully!")
            print(f"Redirecting to order detail: {updated_order.id}")
            return redirect('orders:detail', order_id=updated_order.id)
    else:
        form = OrderForm(instance=order, user=request.user)
    
    # Get available products
    products = Product.objects.filter(is_approved=True)
    
    return render(request, 'orders/edit_order.html', {
        'form': form,
        'order': order,
        'products': products
    })


@login_required
def update_order_status_ajax(request, order_id):
    """AJAX endpoint for updating order status from the order list."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method'})
    
    order = get_object_or_404(Order, id=order_id)
    
    # Check if user has permission to update order status
    user_role = request.user.primary_role.name if request.user.primary_role else None
    can_update = (
        request.user.is_superuser or
        user_role in ['Admin', 'Super Admin', 'Call Center Agent', 'Call Center Manager'] or
        (user_role == 'Seller' and order.seller == request.user)
    )
    
    if not can_update:
        return JsonResponse({'success': False, 'error': 'Permission denied'})
    
    try:
        # Get the new status
        new_status = request.POST.get('status')
        if not new_status:
            return JsonResponse({'success': False, 'error': 'Status is required'})
        
        # Validate status
        valid_statuses = [choice[0] for choice in Order.STATUS_CHOICES]
        if new_status not in valid_statuses:
            return JsonResponse({'success': False, 'error': 'Invalid status'})
        
        # Get additional fields
        cancelled_reason = request.POST.get('cancelled_reason', '')
        tracking_number = request.POST.get('tracking_number', '')
        
        # Validate required fields
        if new_status == 'cancelled' and not cancelled_reason:
            return JsonResponse({'success': False, 'error': 'Cancellation reason is required'})
        
        if new_status in ['shipped', 'delivered'] and not tracking_number:
            return JsonResponse({'success': False, 'error': 'Tracking number is required'})
        
        # Update order
        old_status = order.status
        order.status = new_status
        order.updated_at = timezone.now()
        
        # Set additional fields
        if new_status == 'cancelled':
            order.cancelled_reason = cancelled_reason
        elif new_status in ['shipped', 'delivered']:
            order.tracking_number = tracking_number
        
        # Auto-advance workflow based on status changes
        if new_status == 'confirmed' and old_status != 'confirmed':
            if order.workflow_status == 'callcenter_review':
                order.workflow_status = 'callcenter_approved'
        elif new_status == 'packaged':
            if order.workflow_status == 'packaging_completed':
                order.workflow_status = 'ready_for_delivery'
        elif new_status == 'shipped':
            if order.workflow_status == 'ready_for_delivery':
                order.workflow_status = 'delivery_in_progress'
        elif new_status == 'delivered':
            if order.workflow_status == 'delivery_in_progress':
                order.workflow_status = 'delivery_completed'
        
        order.save()
        
        # Create audit log
        AuditLog.objects.create(
            user=request.user,
            action='status_change',
            entity_type='Order',
            entity_id=str(order.id),
            description=f"Order status changed from {old_status} to {new_status} via AJAX"
        )
        
        return JsonResponse({
            'success': True, 
            'message': f'Order {order.order_code} status updated to {new_status}',
            'new_status': new_status,
            'workflow_status': order.workflow_status
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
def order_dashboard(request):
    """Dashboard with order metrics and charts."""
    # Different users see different metrics
    user_role = request.user.primary_role.name if request.user.primary_role else None
    if user_role == 'Seller':
        orders = Order.objects.filter(seller_email=request.user.email)
    elif user_role in ['Super Admin', 'Admin']:
        orders = Order.objects.all()
    else:
        orders = Order.objects.all()
    
    # Get status counts for charts
    status_counts = {status: orders.filter(status=status_code).count() 
                    for status_code, status in Order.STATUS_CHOICES}
    
    # Get recent orders
    recent_orders = orders.order_by('-date')[:10]
    
    return render(request, 'orders/dashboard.html', {
        'total_orders': orders.count(),
        'status_counts': status_counts,
        'recent_orders': recent_orders,
    })

# Helper functions
def _can_edit_order(user, order):
    """Check if user can edit the order."""
    user_role = user.primary_role.name if user.primary_role else None
    
    # No one can edit confirmed orders (except Super Admin)
    if order.status == 'confirmed' and user_role != 'Super Admin':
        return False
    
    # Super admin can edit any order
    if user_role == 'Super Admin':
        return True
    
    # Admin can edit orders except confirmed ones
    if user_role == 'Admin':
        return order.status != 'confirmed'
    
    # Seller can only edit their own orders in certain statuses
    if user_role == 'Seller' and order.seller == user:
        return order.status in ['pending', 'processing']
    
    # Call center agents can edit certain order statuses
    if user_role in ['Call Center Manager', 'Call Center Agent']:
        return order.status in ['pending', 'processing']
    
    return False

def _can_update_status(user, order):
    """Check if user can update the order status."""
    user_role = user.primary_role.name if user.primary_role else None
    # Super admin and admin can update any order status
    if user_role in ['Super Admin', 'Admin']:
        return True
    
    # Sellers CANNOT update order status (removed this permission)
    # if user_role == 'Seller' and order.seller == user:
    #     return order.status in ['pending', 'processing', 'confirmed', 'cancelled']
    
    # Call center can update confirmation statuses
    if user_role in ['Call Center Manager', 'Call Center Agent']:
        return order.status in ['pending', 'processing', 'confirmed']
    
    # Packaging team can update packaging statuses
    if user_role == 'Packaging':
        return order.status in ['confirmed', 'processing', 'shipped']
    
    # Delivery team can update delivery statuses
    if user_role == 'Delivery':
        return order.status in ['shipped', 'delivered', 'returned']
    
    return False

def _generate_order_code():
    """Generate a shorter order code with # prefix"""
    import random
    from django.utils import timezone
    
    # Get the next order number
    today = timezone.now().date()
    year = today.year
    month = today.month
    day = today.day
    
    # Create a shorter format: #YYMMDDXXX (e.g., #250122001)
    date_part = f"{year % 100:02d}{month:02d}{day:02d}"
    
    # Find the next sequential number for today
    existing_orders_today = Order.objects.filter(
        order_code__startswith=f"#{date_part}"
    ).count()
    
    order_number = existing_orders_today + 1
    code = f"#{date_part}{order_number:03d}"
    
    # Ensure code is unique
    while Order.objects.filter(order_code=code).exists():
        order_number += 1
        code = f"#{date_part}{order_number:03d}"
    
    return code

class OrderListView(LoginRequiredMixin, ListView):
    model = Order
    template_name = 'orders/order_list.html'
    context_object_name = 'orders'
    paginate_by = 10

    def get_queryset(self):
        # Different users see different sets of orders
        user_role = self.request.user.primary_role.name if self.request.user.primary_role else None
        
        # If user has no role, show all orders (default behavior)
        if not user_role:
            queryset = Order.objects.all().order_by('-date')
        elif user_role in ['Super Admin', 'Admin']:
            queryset = Order.objects.all().order_by('-date')
        elif user_role == 'Seller':
            # Sellers see orders assigned to them
            queryset = Order.objects.filter(seller=self.request.user).order_by('-date')
        elif user_role in ['Call Center Manager', 'Call Center Agent']:
            # Call center sees pending and confirmed orders for follow-up
            queryset = Order.objects.filter(
                status__in=['pending', 'processing', 'confirmed']
            ).order_by('-date')
        elif user_role == 'Packaging':
            # Packaging team sees orders ready for packaging
            queryset = Order.objects.filter(
                status__in=['confirmed', 'processing']
            ).order_by('-date')
        elif user_role == 'Delivery':
            # Delivery team sees orders ready for delivery and in delivery
            queryset = Order.objects.filter(
                status__in=['shipped', 'delivered']
            ).order_by('-date')
        else:
            # Other roles see all orders for reference
            queryset = Order.objects.all().order_by('-date')

        # Apply filters
        search_query = self.request.GET.get('search')
        status_filter = self.request.GET.get('status')
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')

        if search_query:
            queryset = queryset.filter(
                Q(order_code__icontains=search_query) |
                Q(customer__icontains=search_query) |
                Q(customer_phone__icontains=search_query) |
                Q(product__name_en__icontains=search_query)
            )

        if status_filter:
            queryset = queryset.filter(status=status_filter)

        if date_from:
            queryset = queryset.filter(date__date__gte=date_from)

        if date_to:
            queryset = queryset.filter(date__date__lte=date_to)

        return queryset.select_related('product')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_choices'] = Order.STATUS_CHOICES
        
        # Get search parameters for form persistence
        context['search_query'] = self.request.GET.get('search', '')
        context['status_filter'] = self.request.GET.get('status', '')
        context['date_from'] = self.request.GET.get('date_from', '')
        context['date_to'] = self.request.GET.get('date_to', '')
        
        # Get total count for display
        context['total_orders'] = self.get_queryset().count()
        
        return context

class OrderDetailView(LoginRequiredMixin, DetailView):
    model = Order
    template_name = 'orders/order_detail.html'
    context_object_name = 'order'

class OrderCreateView(LoginRequiredMixin, CreateView):
    model = Order
    form_class = OrderForm
    template_name = 'orders/create_order.html'
    success_url = reverse_lazy('orders:list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        order = form.save(commit=False)
        
        # Ensure date is set for new orders
        if not order.date:
            from django.utils import timezone
            order.date = timezone.now()
        
        # Set the seller email based on user role
        user_role = self.request.user.primary_role.name if self.request.user.primary_role else None
        if user_role == 'Seller':
            order.seller_email = self.request.user.email
            order.seller = self.request.user
        elif form.cleaned_data.get('seller_email'):
            order.seller_email = form.cleaned_data['seller_email']
        
        # Set workflow status to seller submitted
        order.workflow_status = 'seller_submitted'
        
        # Generate order code if not provided
        if not order.order_code:
            order.order_code = _generate_order_code()
        
        order.save()
        
        # Create audit log
        AuditLog.objects.create(
            user=self.request.user,
            action='create',
            entity_type='Order',
            entity_id=str(order.id),
            description=f"Created new order {order.order_code}"
        )
        
        messages.success(self.request, f"Order {order.order_code} created successfully!")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get available products
        products = Product.objects.all()
        context['products'] = products
        return context

class OrderUpdateView(LoginRequiredMixin, UpdateView):
    model = Order
    form_class = OrderForm
    template_name = 'orders/order_form.html'
    success_url = reverse_lazy('orders:list')

    def form_valid(self, form):
        messages.success(self.request, 'Order updated successfully.')
        return super().form_valid(form)

@login_required
def delete_order(request, order_id):
    """Delete an order (Admin, Super Admin, or Seller for their own orders with pending status)."""
    order = get_object_or_404(Order, id=order_id)
    
    # Check if user has permission to delete orders
    can_delete = False
    
    # Super users and Super Admins can delete any order
    if request.user.is_superuser or request.user.has_role('Super Admin'):
        can_delete = True
    # Sellers can delete their own orders ONLY if status is pending
    elif request.user.has_role('Seller'):
        # Check if the order belongs to this seller
        if order.seller == request.user or (order.product and order.product.seller == request.user):
            # Sellers can only delete orders with pending status
            if order.status == 'pending':
                can_delete = True
            else:
                messages.error(request, "يمكن للسيلر ان يحذف الطلبية اذا لساتاه في pending فقط. / Sellers can only delete orders with pending status.")
                return redirect('orders:list')
    
    if not can_delete:
        messages.error(request, "You don't have permission to delete this order.")
        return redirect('orders:list')
    
    if request.method == 'POST':
        try:
            order_code = order.order_code
            order.delete()
            
            # Create audit log
            AuditLog.objects.create(
                user=request.user,
                action='delete',
                entity_type='Order',
                entity_id=str(order_id),
                description=f"Deleted order {order_code}"
            )
            
            messages.success(request, f"Order {order_code} has been deleted successfully.")
            return redirect('orders:list')
        except Exception as e:
            messages.error(request, f"Error deleting order: {str(e)}")
            return redirect('orders:detail', order_id=order.id)
    
    return render(request, 'orders/delete_order_confirm.html', {'order': order})

@login_required
def download_template(request):
    """Download CSV template for order import."""
    # Create the response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="orders_import_template.csv"'
    
    # Create CSV writer
    writer = csv.writer(response)
    
    # Write header row based on the template format
    writer.writerow([
        'Order Code',  # Order Code/Number
        'Customer Name',  # Customer Name
        'Mobile Number',  # Customer Phone
        'Shipping Address',  # Shipping Address
        'Product ID/Code',  # Product ID
        'Quantity',  # Quantity
        'Price Per Unit (AED)',  # Price Per Unit
        'Product Variant',  # Product variant
        'Notes',  # Order Notes
        'Product Link',  # Product Link
        'Order Date (YYYY-MM-DD)'  # Order Date
    ])
    
    # Add a sample row
    writer.writerow([
        '#250122001',  # Order Code - Updated to new format
        'John Doe',  # Customer Name
        '+971501234567',  # Mobile Number
        '123 Main Street, Dubai',  # Shipping Address
        'PROD-001',  # Product ID/Code
        '2',  # Quantity
        '299.00',  # Price Per Unit
        'Blue',  # Product Variant
        'Handle with care',  # Notes
        'https://example.com/product',  # Product Link
        '2025-01-22'  # Order Date
    ])
    
    return response

@login_required
def import_orders(request):
    """Import orders from CSV file with improved error handling and validation."""
    if request.method == 'POST':
        form = OrderImportForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            try:
                file = request.FILES.get('file')
                if not file:
                    messages.error(request, 'No file was uploaded.')
                    return render(request, 'orders/import_orders.html', {'form': form})
                
                # Validate file type
                if not file.name.lower().endswith('.csv'):
                    messages.error(request, 'Please upload a CSV file (.csv extension).')
                    return render(request, 'orders/import_orders.html', {'form': form})
                
                # Check file size (max 5MB) 
                if file.size > 5 * 1024 * 1024:
                    messages.error(request, 'File size must be less than 5MB.')
                    return render(request, 'orders/import_orders.html', {'form': form})
                
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
                        return render(request, 'orders/import_orders.html', {'form': form})
                
                csv_data = csv.reader(io.StringIO(decoded_file))
                
                # Validate header row
                try:
                    header = next(csv_data)
                    expected_columns = ['Order Code', 'Customer Name', 'Mobile Number', 'Shipping Address', 'Product ID/Code', 'Quantity', 'Price']
                    
                    # Log the actual headers for debugging
                    print(f"CSV Headers: {header}")
                    print(f"Expected columns: {expected_columns}")
                    print(f"Header length: {len(header)}")
                    
                    # More flexible header validation - check if we have the essential columns
                    essential_columns = ['Customer Name', 'Mobile Number', 'Shipping Address', 'Product Link']
                    found_essential = 0
                    
                    for col in essential_columns:
                        if any(col.lower() in h.lower() for h in header):
                            found_essential += 1
                    
                    if found_essential < 4:  # Need all 4 essential columns
                        messages.error(request, f'CSV file must have all essential columns: Customer Name, Mobile Number, Shipping Address, Product Link. Found {found_essential} essential columns.')
                        return render(request, 'orders/import_orders.html', {'form': form})
                    
                except StopIteration:
                    messages.error(request, 'CSV file is empty or invalid.')
                    return render(request, 'orders/import_orders.html', {'form': form})
                
                success_count = 0
                error_count = 0
                warnings = []
                errors = []
                
                for row_num, row in enumerate(csv_data, start=2):  # Start from 2 because we skipped header
                    try:
                        # Skip empty rows
                        if not row or all(cell.strip() == '' for cell in row):
                            continue
                        
                        # Ensure we have minimum required data
                        if len(row) < 4:  # Need at least 4 columns for essential data
                            errors.append(f"Row {row_num}: Insufficient columns (need at least 4: Customer Name, Mobile Number, Shipping Address, Product ID/Code)")
                            error_count += 1
                            continue
                        
                        # Parse row data with flexible validation
                        # Try to find columns by content rather than position
                        order_code = None
                        customer_name = None
                        mobile_number = None
                        address = None
                        product_id = None
                        quantity = 1
                        price = 0.0
                        product_variant = ''
                        notes = ''
                        order_date_str = ''
                        
                        # Parse each column based on content
                        for i, cell in enumerate(row):
                            cell_value = cell.strip() if cell else ''
                            if not cell_value:
                                continue
                                
                            # Try to identify column type by content
                            if i == 0:  # First column - could be Order Code or Customer Name
                                if cell_value.startswith('SKU-') or cell_value.startswith('ORD-'):
                                    order_code = cell_value
                                else:
                                    customer_name = cell_value
                            elif i == 1:  # Second column
                                if not customer_name:
                                    customer_name = cell_value
                                elif not mobile_number and (cell_value.isdigit() or cell_value.startswith('+') or cell_value.startswith('0')):
                                    mobile_number = cell_value
                                else:
                                    address = cell_value
                            elif i == 2:  # Third column
                                if not mobile_number and (cell_value.isdigit() or cell_value.startswith('+') or cell_value.startswith('0')):
                                    mobile_number = cell_value
                                elif not address:
                                    address = cell_value
                                elif not product_id:
                                    product_id = cell_value
                            elif i == 3:  # Fourth column
                                if not address:
                                    address = cell_value
                                elif not product_id:
                                    product_id = cell_value
                                elif not mobile_number and (cell_value.isdigit() or cell_value.startswith('+') or cell_value.startswith('0')):
                                    mobile_number = cell_value
                            elif i == 4:  # Fifth column
                                if not product_id:
                                    product_id = cell_value
                                elif not mobile_number and (cell_value.isdigit() or cell_value.startswith('+') or cell_value.startswith('0')):
                                    mobile_number = cell_value
                            elif i == 5:  # Sixth column - could be quantity or price
                                try:
                                    if '.' in cell_value:  # Likely price
                                        price = float(cell_value)
                                    else:  # Likely quantity
                                        quantity = int(float(cell_value))
                                except (ValueError, TypeError):
                                    pass
                            elif i == 6:  # Seventh column - could be price or quantity
                                try:
                                    if '.' in cell_value:  # Likely price
                                        price = float(cell_value)
                                    else:  # Likely quantity
                                        quantity = int(float(cell_value))
                                except (ValueError, TypeError):
                                    pass
                            elif i == 7:  # Eighth column
                                product_variant = cell_value
                            elif i == 8:  # Ninth column
                                notes = cell_value
                            elif i == 9:  # Tenth column
                                order_date_str = cell_value
                        
                        # Set default values if not found
                        if not customer_name:
                            customer_name = 'Unknown Customer'
                        if not mobile_number:
                            mobile_number = '0000000000'
                        if not address:
                            address = 'Address not provided'
                        if not product_id:
                            product_id = 'Unknown Product'
                        
                        # Ensure quantity and price are valid
                        if quantity <= 0:
                            quantity = 1
                        if price < 0:
                            price = 0.0
                        
                        # Validate required fields
                        if not customer_name or customer_name == 'Unknown Customer':
                            errors.append(f"Row {row_num}: Customer name is required")
                            error_count += 1
                            continue
                        
                        if not mobile_number:
                            errors.append(f"Row {row_num}: Mobile number is required")
                            error_count += 1
                            continue
                        
                        if not address:
                            errors.append(f"Row {row_num}: Shipping address is required")
                            error_count += 1
                            continue
                        
                        if not product_id:
                            errors.append(f"Row {row_num}: Product ID/Code is required. Use the exact product code or name from the system.")
                            error_count += 1
                            continue
                        
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
                        
                        # Find product by ID or code (prioritize exact code match)
                        product = None
                        if product_id:
                            product_id_clean = product_id.strip()
                            
                            # First try to find by exact code match (highest priority)
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
                        
                        # Check if product was found - if not, create order without product
                        if not product:
                            # Log warning but continue processing
                            warnings.append(f"Row {row_num}: Product not found for ID/Code '{product_id}'. Order will be created without product link.")
                            # Continue without product - order will be created with product=None
                        
                        # Check if order already exists
                        if order_code and Order.objects.filter(order_code=order_code).exists():
                            errors.append(f"Row {row_num}: Order code '{order_code}' already exists")
                            error_count += 1
                            continue
                        
                        # Determine the seller for this order
                        user_role = request.user.primary_role.name if request.user.primary_role else None
                        
                        if user_role == 'Seller':
                            seller = request.user
                        elif user_role in ['Admin', 'Super Admin']:
                            # For admins, use the selected seller from the form
                            seller = form.cleaned_data.get('seller') or request.user
                        else:
                            seller = request.user
                        
                        # Prepare notes with Product Variant if provided
                        order_notes = notes
                        if product_variant:
                            if order_notes:
                                order_notes = f"{order_notes}\nProduct Variant: {product_variant}"
                            else:
                                order_notes = f"Product Variant: {product_variant}"
                        
                        # Check if there are multiple variants separated by commas
                        variants = []
                        if product_variant:
                            # Split by comma and clean each variant
                            variants = [variant.strip() for variant in product_variant.split(',') if variant.strip()]
                        
                        # If multiple variants, create separate orders for each variant
                        if len(variants) > 1:
                            for i, variant in enumerate(variants):
                                # Create unique order code for each variant
                                variant_order_code = f"{order_code or _generate_order_code()}-V{i+1}" if order_code else _generate_order_code()
                                
                                # Prepare notes for this variant
                                variant_notes = order_notes
                                if variant_notes:
                                    variant_notes = f"{variant_notes}\nProduct Variant: {variant}"
                                else:
                                    variant_notes = f"Product Variant: {variant}"
                                
                                # Create order for this variant
                                order = Order.objects.create(
                                    order_code=variant_order_code,
                                    customer=customer_name,
                                    customer_phone=mobile_number,
                                    shipping_address=address,
                                    street_address='',  # Street address not available in CSV import
                                    product=product,
                                    quantity=quantity,
                                    price_per_unit=price,
                                    notes=variant_notes,
                                    date=order_date,
                                    status='pending',
                                    seller=seller,
                                    seller_email=seller.email
                                )
                                
                                # Create audit log for this variant
                                AuditLog.objects.create(
                                    user=request.user,
                                    action='import',
                                    entity_type='Order',
                                    entity_id=str(order.id),
                                    description=f"Imported order {order.order_code} from CSV with product: {product.name_en if product else 'Unknown'} (Code: {product.code if product else 'Unknown'}) - Variant: {variant}"
                                )
                        else:
                            # Single variant or no variants - create single order
                            order = Order.objects.create(
                                order_code=order_code or _generate_order_code(),
                                customer=customer_name,
                                customer_phone=mobile_number,
                                shipping_address=address,
                                street_address='',  # Street address not available in CSV import
                                product=product,
                                quantity=quantity,
                                price_per_unit=price,
                                notes=order_notes,
                                date=order_date,
                                status='pending',
                                seller=seller,
                                seller_email=seller.email
                            )
                            
                            # Create audit log
                            AuditLog.objects.create(
                                user=request.user,
                                action='import',
                                entity_type='Order',
                                entity_id=str(order.id),
                                description=f"Imported order {order.order_code} from CSV with product: {product.name_en if product else 'Unknown'} (Code: {product.code if product else 'Unknown'})"
                            )
                        
                        success_count += 1
                        
                        # Create audit log
                        AuditLog.objects.create(
                            user=request.user,
                            action='import',
                            entity_type='Order',
                            entity_id=str(order.id),
                            description=f"Imported order {order.order_code} from CSV with product: {product.name_en} (Code: {product.code})"
                        )
                        
                    except Exception as e:
                        errors.append(f"Row {row_num}: {str(e)}")
                        error_count += 1
                
                # Show results
                if success_count > 0:
                    messages.success(request, f'Successfully imported {success_count} orders.')
                
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
                
                return redirect('orders:list')
                
            except Exception as e:
                messages.error(request, f'Error processing file: {str(e)}')
                print(f"Import error: {e}")
        else:
            messages.error(request, 'Please correct the errors below.')
            print(f"Form errors: {form.errors}")
    else:
        form = OrderImportForm(user=request.user)
    
    return render(request, 'orders/import_orders.html', {'form': form})


@login_required
def distribute_orders(request):
    """Distribute unassigned orders to available agents using round-robin method."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid request method'})
    
    try:
        # Get unassigned orders (excluding cancelled, completed, delivered)
        unassigned_orders = Order.objects.filter(
            agent__isnull=True,
            status__in=['pending', 'processing', 'confirmed']
        ).order_by('date')
        
        if not unassigned_orders.exists():
            return JsonResponse({
                'success': False, 
                'message': 'لا توجد طلبات غير معينة للتوزيع'
            })
        
        # Get available agents (Call Center Agent or Agent role)
        from roles.models import UserRole, Role
        agent_role = Role.objects.filter(name__in=['Call Center Agent', 'Agent']).first()
        
        if not agent_role:
            return JsonResponse({
                'success': False, 
                'message': 'لا توجد أدوار للوكلاء في النظام'
            })
        
        available_agents = User.objects.filter(
            user_roles__role=agent_role,
            user_roles__is_active=True,
            is_active=True
        ).distinct()
        
        if not available_agents.exists():
            return JsonResponse({
                'success': False, 
                'message': 'لا توجد وكلاء متاحين في النظام'
            })
        
        # Convert to list for round-robin distribution
        agents_list = list(available_agents)
        agent_index = 0
        distributed_count = 0
        
        for order in unassigned_orders:
            # Assign agent using round-robin
            assigned_agent = agents_list[agent_index % len(agents_list)]
            order.agent = assigned_agent
            order.assigned_at = timezone.now()
            order.save()
            
            # Create audit log
            AuditLog.objects.create(
                user=request.user,
                action='assign_agent',
                entity_type='Order',
                entity_id=str(order.id),
                description=f"Auto-assigned order {order.order_code} to agent {assigned_agent.get_full_name() or assigned_agent.username}"
            )
            
            distributed_count += 1
            agent_index += 1
        
        message = f'تم توزيع {distributed_count} طلب بنجاح على {len(agents_list)} وكيل'
        
        return JsonResponse({
            'success': True,
            'message': message,
            'distributed_count': distributed_count,
            'agents_count': len(agents_list)
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'خطأ في توزيع الطلبات: {str(e)}'
        })


@login_required
def callcenter_approve_order(request, order_id):
    """Call Center Agent approves an order for packaging."""
    order = get_object_or_404(Order, id=order_id)
    
    # Check if user has permission to approve orders
    user_role = request.user.primary_role.name if request.user.primary_role else None
    if user_role not in ['Call Center Agent', 'Call Center Manager', 'Admin', 'Super Admin']:
        messages.error(request, "You don't have permission to approve orders.")
        return redirect('orders:detail', order_id=order.id)
    
    # Check if order is in correct status
    if order.workflow_status != 'callcenter_review':
        messages.error(request, f"Order {order.order_code} is not in Call Center Review status.")
        return redirect('orders:detail', order_id=order.id)
    
    if request.method == 'POST':
        # Update order workflow status
        order.workflow_status = 'callcenter_approved'
        order.status = 'confirmed'  # Also update main status
        order.save()
        
        # Create workflow log
        from .models import OrderWorkflowLog
        OrderWorkflowLog.objects.create(
            order=order,
            from_status='callcenter_review',
            to_status='callcenter_approved',
            user=request.user,
            notes='Call Center Agent approved order for packaging'
        )
        
        # Create audit log
        AuditLog.objects.create(
            user=request.user,
            action='approve',
            entity_type='Order',
            entity_id=str(order.id),
            description=f"Call Center Agent approved order {order.order_code} for packaging"
        )
        
        messages.success(request, f"Order {order.order_code} approved successfully! Ready for packaging.")
        return redirect('orders:detail', order_id=order.id)
    
    return render(request, 'orders/callcenter_approve.html', {
        'order': order
    })


@login_required
def order_invoice(request, order_id):
    """View for generating order invoice."""
    order = get_object_or_404(Order, id=order_id)
    context = {
        'order': order,
    }
    return render(request, 'orders/order_invoice.html', context)


def public_order_view(request, order_code):
    """Public view for order details via QR code."""
    order = get_object_or_404(Order, order_code=order_code)
    context = {
        'order': order,
    }
    return render(request, 'orders/public_order_view.html', context)


@login_required
def get_states_for_city_api(request):
    """API endpoint to get states for a city - requires authentication."""
    city_name = request.GET.get('city', '')
    if not city_name:
        return JsonResponse({'success': False, 'error': 'City name is required'})
    
    from .area_utils import get_states_for_city
    states = get_states_for_city(city_name)
    states_list = [{'value': state[0], 'label': state[1]} for state in states]
    
    return JsonResponse({
        'success': True,
        'states': states_list
    })

@login_required
def available_agents_count(request):
    """API endpoint to get count of available Call Center Agents - requires authentication."""
    try:
        # Get all active Call Center Agents
        agents_count = User.objects.filter(
            user_roles__role__name='Call Center Agent',
            user_roles__is_active=True,
            is_active=True
        ).distinct().count()
        
        return JsonResponse({'count': agents_count})
    except Exception as e:
        return JsonResponse({'count': 0, 'error': str(e)})


def _get_next_available_agent():
    """Get the next available Call Center Agent for auto assignment."""
    try:
        # Get all active Call Center Agents
        agents = User.objects.filter(
            user_roles__role__name='Call Center Agent',
            user_roles__is_active=True,
            is_active=True
        ).distinct()
        
        if not agents.exists():
            return None
        
        # Get agent with least assigned orders
        from django.db.models import Count
        agents_with_counts = agents.annotate(
            assigned_orders_count=Count('assigned_orders', distinct=True)
        ).order_by('assigned_orders_count', 'id')
        
        return agents_with_counts.first()
        
    except Exception as e:
        print(f"Error getting next available agent: {e}")
        return None

@login_required
def change_order_seller(request, order_id):
    """Change seller for a specific order."""
    order = get_object_or_404(Order, id=order_id)
    
    # Check if user has permission to change seller
    if not (request.user.is_superuser or request.user.has_role('Admin') or request.user.has_role('Super Admin')):
        messages.error(request, "You don't have permission to change seller.")
        return redirect('orders:detail', order_id=order_id)
    
    if request.method == 'POST':
        new_seller_id = request.POST.get('new_seller')
        if new_seller_id:
            try:
                new_seller = User.objects.get(id=new_seller_id)
                old_seller = order.seller
                
                # Update order
                order.seller = new_seller
                order.seller_email = new_seller.email
                order.save()
                
             
                OrderWorkflowLog.objects.create(
                    order=order,
                    from_status=order.workflow_status,
                    to_status=order.workflow_status,
                    user=request.user,
                    notes=f'Seller changed from {old_seller.get_full_name() if old_seller else "None"} to {new_seller.get_full_name()}'
                )
                
                messages.success(request, f'Seller successfully changed to {new_seller.get_full_name()}.')
                return redirect('orders:detail', order_id=order_id)
                
            except User.DoesNotExist:
                messages.error(request, 'Selected seller not found.')
        else:
            messages.error(request, 'Please select a seller.')
    
    # Get all sellers
    sellers = User.objects.filter(user_roles__role__name='Seller', user_roles__is_active=True).distinct().order_by('first_name', 'last_name')
    
    context = {
        'order': order,
        'sellers': sellers,
    }
    
    return render(request, 'orders/change_seller.html', context)