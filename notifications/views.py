from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone
from .models import Notification
from django.contrib.auth import get_user_model

User = get_user_model()

@login_required
def notifications_list(request):
    """Main notifications page for all users"""
    
    # Get user's notifications
    notifications = Notification.get_user_notifications(
        user=request.user,
        include_expired=False
    )
    
    # Get filters from request
    notification_type = request.GET.get('type', '')
    priority = request.GET.get('priority', '')
    status = request.GET.get('status', '')
    search = request.GET.get('search', '')
    
    # Apply filters
    if notification_type:
        notifications = notifications.filter(notification_type=notification_type)
    
    if priority:
        notifications = notifications.filter(priority=priority)
    
    if status == 'unread':
        notifications = notifications.filter(is_read=False)
    elif status == 'read':
        notifications = notifications.filter(is_read=True)
    
    if search:
        notifications = notifications.filter(
            Q(title__icontains=search) | Q(message__icontains=search)
        )
    
    # Get statistics
    total_notifications = notifications.count()
    unread_count = notifications.filter(is_read=False).count()
    read_count = total_notifications - unread_count
    
    # Handle mark all as read
    if request.method == 'POST' and 'mark_all_read' in request.POST:
        notifications.filter(is_read=False).update(
            is_read=True, 
            read_at=timezone.now()
        )
        messages.success(request, "All notifications marked as read.")
        return redirect('notifications:index')
    
    # Handle mark individual notification as read
    if request.method == 'POST' and 'mark_read' in request.POST:
        notification_id = request.POST.get('mark_read')
        try:
            notification = Notification.objects.get(
                id=notification_id, 
                user=request.user
            )
            notification.mark_as_read()
            messages.success(request, "Notification marked as read.")
        except Notification.DoesNotExist:
            messages.error(request, "Notification not found.")
        return redirect('notifications:index')
    
    # Handle delete notification
    if request.method == 'POST' and 'delete_notification' in request.POST:
        notification_id = request.POST.get('delete_notification')
        try:
            notification = Notification.objects.get(
                id=notification_id, 
                user=request.user
            )
            notification.delete()
            messages.success(request, "Notification deleted successfully.")
        except Notification.DoesNotExist:
            messages.error(request, "Notification not found.")
        return redirect('notifications:index')
    
    # Handle archive notification
    if request.method == 'POST' and 'archive_notification' in request.POST:
        notification_id = request.POST.get('archive_notification')
        try:
            notification = Notification.objects.get(
                id=notification_id, 
                user=request.user
            )
            notification.archive()
            messages.success(request, "Notification archived successfully.")
        except Notification.DoesNotExist:
            messages.error(request, "Notification not found.")
        return redirect('notifications:index')
    
    # Pagination
    paginator = Paginator(notifications, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get notification types and priorities for filter dropdowns
    notification_types = Notification.NOTIFICATION_TYPES
    priority_levels = Notification.PRIORITY_LEVELS
    
    context = {
        'notifications': page_obj,
        'page_obj': page_obj,
        'total_notifications': total_notifications,
        'unread_count': unread_count,
        'read_count': read_count,
        'notification_types': notification_types,
        'priority_levels': priority_levels,
        'current_filters': {
            'type': notification_type,
            'priority': priority,
            'status': status,
            'search': search,
        }
    }
    
    return render(request, 'notifications/notifications_list.html', context)

@login_required
def get_notifications_ajax(request):
    """AJAX endpoint to get notifications for navbar"""
    try:
        # Get unread notifications count
        unread_count = Notification.get_user_notifications(
            user=request.user,
            unread_only=True
        ).count()
        
        # Get recent notifications (last 5)
        recent_notifications = Notification.get_user_notifications(
            user=request.user,
            limit=5
        )
        
        notification_data = []
        for notification in recent_notifications:
            notification_data.append({
                'id': notification.id,
                'title': notification.title,
                'message': notification.message,
                'type': notification.notification_type,
                'priority': notification.priority,
                'is_read': notification.is_read,
                'created_at': notification.created_at.strftime('%Y-%m-%d %H:%M'),
                'age': notification.age,
                'related_url': notification.related_url,
            })
        
        return JsonResponse({
            'success': True,
            'notifications': notification_data,
            'unread_count': unread_count,
            'total_count': recent_notifications.count()
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@login_required
def mark_notification_read(request, notification_id):
    """Mark a specific notification as read"""
    try:
        notification = get_object_or_404(
            Notification, 
            id=notification_id, 
            user=request.user
        )
        
        if not notification.is_read:
            notification.mark_as_read()
            return JsonResponse({
                'success': True,
                'message': 'Notification marked as read'
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Notification already read'
            })
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@login_required
def mark_all_notifications_read(request):
    """Mark all user notifications as read"""
    try:
        unread_notifications = Notification.get_user_notifications(
            user=request.user,
            unread_only=True
        )
        
        count = unread_notifications.count()
        unread_notifications.update(
            is_read=True,
            read_at=timezone.now()
        )
        
        return JsonResponse({
            'success': True,
            'message': f'{count} notifications marked as read',
            'count': count
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@login_required
def notification_detail(request, notification_id):
    """View detailed notification information"""
    notification = get_object_or_404(
        Notification, 
        id=notification_id, 
        user=request.user
    )
    
    # Mark as read when viewed
    if not notification.is_read:
        notification.mark_as_read()
    
    context = {
        'notification': notification,
    }
    
    return render(request, 'notifications/notification_detail.html', context)

@login_required
def archived_notifications(request):
    """View archived notifications"""
    archived_notifications = Notification.objects.filter(
        user=request.user,
        is_archived=True
    ).order_by('-created_at')
    
    # Handle unarchive
    if request.method == 'POST' and 'unarchive_notification' in request.POST:
        notification_id = request.POST.get('unarchive_notification')
        try:
            notification = Notification.objects.get(
                id=notification_id, 
                user=request.user
            )
            notification.unarchive()
            messages.success(request, "Notification unarchived successfully.")
        except Notification.DoesNotExist:
            messages.error(request, "Notification not found.")
        return redirect('notifications:archived')
    
    # Pagination
    paginator = Paginator(archived_notifications, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'notifications': page_obj,
        'page_obj': page_obj,
        'total_archived': archived_notifications.count(),
    }
    
    return render(request, 'notifications/archived_notifications.html', context)

@login_required
def notification_settings(request):
    """User notification preferences and settings"""
    if request.method == 'POST':
        # Handle notification preference updates
        # This can be expanded based on your needs
        messages.success(request, "Notification settings updated successfully.")
        return redirect('notifications:settings')
    
    context = {
        'user': request.user,
        'notification_types': Notification.NOTIFICATION_TYPES,
        'priority_levels': Notification.PRIORITY_LEVELS,
    }
    
    return render(request, 'notifications/notification_settings.html', context)
