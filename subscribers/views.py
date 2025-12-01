from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone
from users.models import User
from .models import Subscriber
from .forms import SubscriberForm

@login_required
def subscribers_list(request):
    """Display all users and subscribers in a table format"""
    
    # Get search and filter parameters
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    country_filter = request.GET.get('country', '')
    sort_by = request.GET.get('sort_by', '-date_joined')
    
    # Start with all users
    users = User.objects.all()
    
    # Apply search filter
    if search_query:
        users = users.filter(
            Q(full_name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(phone_number__icontains=search_query) |
            Q(company_name__icontains=search_query)
        )
    
    # Apply status filter
    if status_filter:
        if status_filter == 'active':
            users = users.filter(is_active=True)
        elif status_filter == 'inactive':
            users = users.filter(is_active=False)
        elif status_filter == 'pending':
            users = users.filter(approval_status='pending')
    
    # Apply country filter
    if country_filter:
        users = users.filter(country__icontains=country_filter)
    
    # Apply sorting
    if sort_by == 'name':
        users = users.order_by('full_name')
    elif sort_by == 'email':
        users = users.order_by('email')
    elif sort_by == 'date_joined':
        users = users.order_by('date_joined')
    elif sort_by == '-date_joined':
        users = users.order_by('-date_joined')
    else:
        users = users.order_by('-date_joined')
    
    # Pagination
    paginator = Paginator(users, 25)  # Show 25 users per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get unique countries for filter dropdown
    countries = User.objects.exclude(country__isnull=True).exclude(country='').values_list('country', flat=True).distinct().order_by('country')
    
    # Get statistics
    total_users = User.objects.count()
    active_users = User.objects.filter(is_active=True).count()
    pending_users = User.objects.filter(approval_status='pending').count()
    recent_users = User.objects.filter(date_joined__gte=timezone.now() - timezone.timedelta(days=30)).count()
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'status_filter': status_filter,
        'country_filter': country_filter,
        'sort_by': sort_by,
        'countries': countries,
        'total_users': total_users,
        'active_users': active_users,
        'pending_users': pending_users,
        'recent_users': recent_users,
    }
    
    return render(request, 'subscribers/subscribers.html', context)

@login_required
def add_user(request):
    """Add a new user/subscriber"""
    if request.method == 'POST':
        form = SubscriberForm(request.POST)
        if form.is_valid():
            subscriber = form.save()
            messages.success(request, f'User "{subscriber.full_name}" has been added successfully!')
            return redirect('subscribers:list')
    else:
        form = SubscriberForm()
    
    context = {
        'form': form,
        'title': 'Add New User'
    }
    
    return render(request, 'subscribers/add_user.html', context)

@login_required
def view_details(request, user_id):
    """View detailed information about a user"""
    user_obj = get_object_or_404(User, id=user_id)
    
    # Get user's primary and secondary roles
    primary_role = user_obj.primary_role
    user_roles = user_obj.user_roles.filter(is_active=True)
    # Get secondary roles (all roles except primary)
    secondary_roles = user_roles.filter(is_primary=False)
    
    # Get user's recent activity from audit logs
    from users.models import AuditLog
    recent_activities = AuditLog.objects.filter(user=user_obj).order_by('-timestamp')[:10]
    
    # Get user statistics
    login_count = AuditLog.objects.filter(user=user_obj, action='login').count()
    last_login = user_obj.last_login
    
    # Additional user information 
    total_roles = user_roles.count()
    account_age = timezone.now() - user_obj.date_joined
    
    context = {
        'user_obj': user_obj,  # Use same variable name as users app
        'edited_user': user_obj,  # Use for Quick Actions instead of 'user'
        'primary_role': primary_role,
        'secondary_roles': secondary_roles,
        'user_roles': user_roles,
        'recent_activities': recent_activities,
        'login_count': login_count,
        'last_login': last_login,
        'total_roles': total_roles,
        'account_age': account_age,
    }
    
    return render(request, 'subscribers/user_detail.html', context)

@login_required
def edit_user(request, user_id):
    """Edit user information"""
    user_obj = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        from users.forms import UserChangeForm
        form = UserChangeForm(request.POST, request.FILES, instance=user_obj)
        if form.is_valid():
            form.save()
            messages.success(request, f'User "{user_obj.full_name}" has been updated successfully!')
            return redirect('subscribers:view_details', user_id=user_obj.id)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        from users.forms import UserChangeForm
        form = UserChangeForm(instance=user_obj)
    
    # Get user's current roles for display
    user_roles = user_obj.user_roles.filter(is_active=True)
    primary_role = user_obj.primary_role
    # Get secondary roles (all roles except primary)
    secondary_roles = user_roles.filter(is_primary=False)
    
    context = {
        'user_obj': user_obj,  # Use same variable name as users app
        'edited_user': user_obj,  # Use for Quick Actions instead of 'user'
        'form': form,
        'user_roles': user_roles,
        'primary_role': primary_role,
        'secondary_roles': secondary_roles,
        'title': 'Edit User'
    }
    
    return render(request, 'subscribers/edit_user.html', context)

@login_required
def delete_user(request, user_id):
    """Delete a user"""
    user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        user_name = user.full_name
        user.delete()
        messages.success(request, f'User "{user_name}" has been deleted successfully!')
        return redirect('subscribers:list')
    
    context = {
        'user': user,
        'title': 'Delete User'
    }
    
    return render(request, 'subscribers/delete_user.html', context)

@login_required
def toggle_user_status(request, user_id):
    """Toggle user active/inactive status"""
    if request.method == 'POST':
        user = get_object_or_404(User, id=user_id)
        user.is_active = not user.is_active
        user.save()
        
        status = 'activated' if user.is_active else 'deactivated'
        return JsonResponse({
            'success': True,
            'message': f'User has been {status} successfully!',
            'is_active': user.is_active
        })
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

@login_required
def pending_users_list(request):
    """Display pending users awaiting approval"""
    
    # Get search parameters
    search_query = request.GET.get('search', '')
    
    # Start with pending users
    pending_users = User.objects.filter(approval_status='pending').order_by('-date_joined')
    
    # Apply search filter
    if search_query:
        pending_users = pending_users.filter(
            Q(full_name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(phone_number__icontains=search_query) |
            Q(company_name__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(pending_users, 20)  # Show 20 pending users per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get statistics
    total_pending = User.objects.filter(approval_status='pending').count()
    total_users = User.objects.count()
    recent_pending = User.objects.filter(
        approval_status='pending',
        date_joined__gte=timezone.now() - timezone.timedelta(days=7)
    ).count()
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'total_pending': total_pending,
        'total_users': total_users,
        'recent_pending': recent_pending,
    }
    
    return render(request, 'subscribers/pending_users.html', context)

@login_required
def get_user_id_images(request, user_id):
    """Get user ID images and bank info for modal display"""
    user = get_object_or_404(User, id=user_id)
    
    data = {
        'id': user.id,
        'name': user.full_name,
        'email': user.email,
        'phone': user.phone_number,
        'front_image': user.id_front_image.url if user.id_front_image else None,
        'back_image': user.id_back_image.url if user.id_back_image else None,
        'has_front_image': bool(user.id_front_image),
        'has_back_image': bool(user.id_back_image),
        # Bank Information
        'bank_name': user.bank_name,
        'account_holder_name': user.account_holder_name,
        'account_number': user.account_number,
        'iban_confirmation': user.iban_confirmation,
        'has_bank_info': bool(user.bank_name or user.account_number),
    }
    
    return JsonResponse(data)

@login_required
def approve_user(request, user_id):
    """Approve a pending user"""
    if request.method == 'POST':
        user = get_object_or_404(User, id=user_id, approval_status='pending')
        
        # Approve the user
        user.approval_status = 'approved'
        user.is_active = True
        user.approved_by = request.user
        user.approved_at = timezone.now()
        user.save()
        
        # Send approval email
        try:
            from users.email_utils import send_approval_email
            send_approval_email(user, request.user)
        except Exception as e:
            print(f"Error sending approval email: {e}")
        
        return JsonResponse({
            'success': True,
            'message': f'User "{user.full_name}" has been approved successfully!'
        })
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

@login_required
def reject_user(request, user_id):
    """Reject a pending user"""
    if request.method == 'POST':
        import json
        data = json.loads(request.body)
        reason = data.get('reason', '')
        
        user = get_object_or_404(User, id=user_id, approval_status='pending')
        
        # Reject the user
        user.approval_status = 'rejected'
        user.rejection_reason = reason
        user.is_active = False
        user.save()
        
        # Send rejection email
        try:
            from users.email_utils import send_rejection_email
            send_rejection_email(user, reason)
        except Exception as e:
            print(f"Error sending rejection email: {e}")
        
        return JsonResponse({
            'success': True,
            'message': f'User "{user.full_name}" has been rejected.'
        })
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

@login_required
def export_users(request):
    """Export users data to CSV"""
    import csv
    from django.http import HttpResponse
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="users_export.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Full Name', 'Email', 'Phone Number', 'Business Name', 'Country', 'Date Joined', 'Status'])
    
    users = User.objects.all().order_by('-date_joined')
    for user in users:
        writer.writerow([
            user.full_name,
            user.email,
            user.phone_number,
            user.company_name or '',
            user.country or '',
            user.date_joined.strftime('%Y-%m-%d'),
            'Active' if user.is_active else 'Inactive'
        ])
    
    return response 