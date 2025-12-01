from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Q
from .models import ProductDeletionRequest, Product
from .forms import ProductDeletionRequestForm
from notifications.models import Notification

def has_admin_role(user):
    """Check if user has admin role"""
    return (
        user.is_superuser or
        user.has_role('Admin') or
        user.has_role('Super Admin')
    )

@login_required
def deletion_requests_list(request):
    """List all product deletion requests for admin review"""
    if not has_admin_role(request.user):
        messages.error(request, "You don't have permission to access this page.")
        return redirect('dashboard:index')
    
    # Get all deletion requests
    requests = ProductDeletionRequest.objects.select_related('product', 'seller').all()
    
    # Filter by status if provided
    status_filter = request.GET.get('status', '')
    if status_filter:
        requests = requests.filter(status=status_filter)
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        requests = requests.filter(
            Q(product__name_en__icontains=search_query) |
            Q(product__name_ar__icontains=search_query) |
            Q(seller__first_name__icontains=search_query) |
            Q(seller__last_name__icontains=search_query) |
            Q(seller__email__icontains=search_query)
        )
    
    # Order by requested date (newest first)
    requests = requests.order_by('-requested_at')
    
    # Statistics
    total_requests = requests.count()
    pending_requests = requests.filter(status='pending').count()
    approved_requests = requests.filter(status='approved').count()
    rejected_requests = requests.filter(status='rejected').count()
    
    context = {
        'requests': requests,
        'total_requests': total_requests,
        'pending_requests': pending_requests,
        'approved_requests': approved_requests,
        'rejected_requests': rejected_requests,
        'status_filter': status_filter,
        'search_query': search_query,
    }
    
    return render(request, 'sellers/admin/deletion_requests_list.html', context)

@login_required
def deletion_request_detail(request, request_id):
    """View details of a specific deletion request"""
    if not has_admin_role(request.user):
        messages.error(request, "You don't have permission to access this page.")
        return redirect('dashboard:index')
    
    deletion_request = get_object_or_404(ProductDeletionRequest, id=request_id)
    
    context = {
        'deletion_request': deletion_request,
    }
    
    return render(request, 'sellers/admin/deletion_request_detail.html', context)

@login_required
def approve_deletion_request(request, request_id):
    """Approve a product deletion request"""
    if not has_admin_role(request.user):
        messages.error(request, "You don't have permission to perform this action.")
        return redirect('dashboard:index')
    
    deletion_request = get_object_or_404(ProductDeletionRequest, id=request_id)
    
    if deletion_request.status != 'pending':
        messages.error(request, "This request has already been processed.")
        return redirect('sellers:deletion_request_detail', request_id=request_id)
    
    if request.method == 'POST':
        admin_notes = request.POST.get('admin_notes', '')
        
        # Update the deletion request
        deletion_request.status = 'approved'
        deletion_request.reviewed_by = request.user
        deletion_request.reviewed_at = timezone.now()
        deletion_request.admin_notes = admin_notes
        deletion_request.save()
        
        # Delete the product
        product_name = deletion_request.product.name_en
        deletion_request.product.delete()
        
        # Create notification for seller
        Notification.objects.create(
            user=deletion_request.seller,
            title="Product Deletion Approved",
            message=f"Your request to delete product '{product_name}' has been approved and the product has been deleted.",
            notification_type='product_deletion_approved',
            priority='medium',
            related_object_type='product',
            related_object_id=deletion_request.product.id,
            related_url="/sellers/products/"
        )
        
        messages.success(request, f"Product '{product_name}' has been approved for deletion and deleted successfully.")
        return redirect('sellers:deletion_requests_list')
    
    return render(request, 'sellers/admin/approve_deletion_request.html', {
        'deletion_request': deletion_request,
    })

@login_required
def reject_deletion_request(request, request_id):
    """Reject a product deletion request"""
    if not has_admin_role(request.user):
        messages.error(request, "You don't have permission to perform this action.")
        return redirect('dashboard:index')
    
    deletion_request = get_object_or_404(ProductDeletionRequest, id=request_id)
    
    if deletion_request.status != 'pending':
        messages.error(request, "This request has already been processed.")
        return redirect('sellers:deletion_request_detail', request_id=request_id)
    
    if request.method == 'POST':
        admin_notes = request.POST.get('admin_notes', '')
        
        # Update the deletion request
        deletion_request.status = 'rejected'
        deletion_request.reviewed_by = request.user
        deletion_request.reviewed_at = timezone.now()
        deletion_request.admin_notes = admin_notes
        deletion_request.save()
        
        # Create notification for seller
        Notification.objects.create(
            user=deletion_request.seller,
            title="Product Deletion Rejected",
            message=f"Your request to delete product '{deletion_request.product.name_en}' has been rejected. Reason: {admin_notes}",
            notification_type='product_deletion_rejected',
            priority='medium',
            related_object_type='product',
            related_object_id=deletion_request.product.id,
            related_url="/sellers/products/"
        )
        
        messages.success(request, f"Product deletion request for '{deletion_request.product.name_en}' has been rejected.")
        return redirect('sellers:deletion_requests_list')
    
    return render(request, 'sellers/admin/reject_deletion_request.html', {
        'deletion_request': deletion_request,
    })
