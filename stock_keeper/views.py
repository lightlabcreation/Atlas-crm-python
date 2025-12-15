# stock_keeper/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils import timezone
from django.db.models import Count, Sum, Q, F
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from .models import (
    WarehouseInventory, InventoryMovement, 
    TrackingNumber, StockKeeperSession, StockAlert,
    StockKeeperTask, BarcodeScanHistory, PhysicalCountRecord
)
from inventory.models import Warehouse, InventoryRecord, WarehouseLocation
from orders.models import Order
from sellers.models import Product
from datetime import datetime, timedelta
import json
from .forms import StockKeeperTaskForm
from django.db import transaction

def is_stock_keeper(user):
    """Check if user is a stock keeper."""
    return user.is_authenticated and (user.has_role('Stock Keeper') or user.is_staff or user.is_superuser)

def is_warehouse_manager(user):
    """Check if user is a warehouse manager."""
    return user.groups.filter(name='Warehouse Managers').exists() or user.is_superuser

@login_required
@user_passes_test(is_stock_keeper)

def dashboard(request):
    """Stock Keeper Dashboard with warehouse-specific data."""
    today = timezone.now().date()
    
    # Get user's assigned warehouse (for now, use first active warehouse)
    warehouse = Warehouse.objects.filter(is_active=True).first()
    
    # If no warehouse exists, show a message and allow access to warehouse management
    if not warehouse:
        context = {
            'no_warehouse': True,
            'warehouses_count': Warehouse.objects.count(),
        }
        return render(request, 'stock_keeper/dashboard.html', context)
    
    # Get or create active session
    session, created = StockKeeperSession.objects.get_or_create(
        user=request.user,
        warehouse=warehouse,
        is_active=True,
        defaults={'shift_start': timezone.now()}
    )
    
    # Get today's statistics
    today_movements = InventoryMovement.objects.filter(
        processed_by=request.user,
        processed_at__date=today
    )
    
    # Get pending tasks (both movements and assigned tasks)
    pending_movements = InventoryMovement.objects.filter(
        status='pending',
        to_warehouse=warehouse
    ).count()
    
    pending_tasks = StockKeeperTask.objects.filter(
        assigned_to=request.user,
        status='pending'
    ).count()
    
    total_pending_tasks = pending_movements + pending_tasks
    
    stock_alerts = StockAlert.objects.filter(
        warehouse=warehouse,
        is_resolved=False
    ).count()
    
    completed_today = today_movements.filter(status='completed').count()
    
    # Use InventoryRecord instead of WarehouseInventory
    total_items = InventoryRecord.objects.filter(
        warehouse=warehouse
    ).aggregate(total=Sum('quantity'))['total'] or 0
    
    # Get urgent alerts
    urgent_alerts = StockAlert.objects.filter(
        warehouse=warehouse,
        is_resolved=False,
        priority__in=['high', 'urgent']
    )[:5]
    
    # Get pending movements
    pending_movements_list = InventoryMovement.objects.filter(
        status='pending',
        to_warehouse=warehouse
    )[:10]
    
    # Get assigned tasks
    assigned_tasks = StockKeeperTask.objects.filter(
        assigned_to=request.user,
        status__in=['pending', 'in_progress']
    ).order_by('priority', 'due_date')[:10]
    
    # Get recent barcode scans
    recent_scans = BarcodeScanHistory.objects.filter(
        user=request.user,
        scan_timestamp__date=today
    ).order_by('-scan_timestamp')[:5]
    
    # Get warehouse statistics - ALL REAL DATA
    warehouse_stats = {
        'total_products': InventoryRecord.objects.filter(warehouse=warehouse).values('product').distinct().count(),
        'low_stock_items': InventoryRecord.objects.filter(
            warehouse=warehouse,
            quantity__lte=10,
            quantity__gt=0
        ).count(),
        'out_of_stock_items': InventoryRecord.objects.filter(
            warehouse=warehouse,
            quantity=0
        ).count(),
        'total_warehouses': Warehouse.objects.filter(is_active=True).count(),
    }
    
    # Calculate near expiry items (if we have expiry tracking, otherwise use low stock as proxy)
    # For now, we'll use items with quantity <= 5 as "near expiry" proxy
    near_expiry_items = InventoryRecord.objects.filter(
        warehouse=warehouse,
        quantity__lte=5,
        quantity__gt=0
    ).count()
    
    # Get orders awaiting pick (real data)
    orders_awaiting_preparation = Order.objects.filter(
        workflow_status__in=['pick_and_pack', 'stockkeeper_approved', 'callcenter_approved']
    ).count()
    
    # Calculate stock status percentages for pie chart
    all_inventory = InventoryRecord.objects.filter(warehouse=warehouse)
    total_inventory_count = all_inventory.count()
    
    if total_inventory_count > 0:
        available_count = all_inventory.filter(quantity__gt=10).count()
        low_count = all_inventory.filter(quantity__lte=10, quantity__gt=0).count()
        out_of_stock_count = all_inventory.filter(quantity=0).count()
        
        available_percent = (available_count / total_inventory_count) * 100
        low_percent = (low_count / total_inventory_count) * 100
        out_of_stock_percent = (out_of_stock_count / total_inventory_count) * 100
    else:
        available_count = 0
        low_count = 0
        out_of_stock_count = 0
        available_percent = 0
        low_percent = 0
        out_of_stock_percent = 0
    
    # Get quantities by warehouse for bar chart (real data)
    warehouses_data = []
    all_warehouses = Warehouse.objects.filter(is_active=True).order_by('-id')[:5]  # Top 5 warehouses
    max_quantity = 0
    for wh in all_warehouses:
        wh_total = InventoryRecord.objects.filter(warehouse=wh).aggregate(total=Sum('quantity'))['total'] or 0
        if wh_total > max_quantity:
            max_quantity = wh_total
        warehouses_data.append({
            'name': wh.name,
            'total': wh_total
        })
    
    # Stock status data for pie chart
    stock_status = {
        'available_percent': round(available_percent, 1),
        'low_percent': round(low_percent, 1),
        'out_of_stock_percent': round(out_of_stock_percent, 1),
        'available_count': available_count,
        'low_count': low_count,
        'out_of_stock_count': out_of_stock_count,
    }
    
    context = {
        'warehouse': warehouse,
        'session': session,
        'total_inventory_count': total_inventory_count,
        'today_movements': today_movements,
        'total_pending_tasks': total_pending_tasks,
        'stock_alerts': stock_alerts,
        'completed_today': completed_today,
        'total_items': total_items,
        'urgent_alerts': urgent_alerts,
        'pending_movements_list': pending_movements_list,
        'assigned_tasks': assigned_tasks,
        'warehouses_data': warehouses_data,
        'max_warehouse_quantity': max_quantity if max_quantity > 0 else 1,  # Avoid division by zero
        'stock_status': stock_status,
        'recent_scans': recent_scans,
        'warehouse_stats': warehouse_stats,
        'near_expiry_items': near_expiry_items,
        'orders_awaiting_preparation': orders_awaiting_preparation,
        'no_warehouse': False,
    }
    
    return render(request, 'stock_keeper/dashboard.html', context)

@login_required
@user_passes_test(is_stock_keeper)
def task_management(request):
    """Task management interface for stock keepers."""
    warehouse = Warehouse.objects.filter(is_active=True).first()
    if not warehouse:
        messages.error(request, 'No active warehouse found.')
        return redirect('stock_keeper:dashboard')
    
    # Get filter parameters
    status_filter = request.GET.get('status', '')
    priority_filter = request.GET.get('priority', '')
    task_type_filter = request.GET.get('task_type', '')
    
    # Get user's tasks
    tasks = StockKeeperTask.objects.filter(assigned_to=request.user)
    
    # Apply filters
    if status_filter:
        tasks = tasks.filter(status=status_filter)
    if priority_filter:
        tasks = tasks.filter(priority=priority_filter)
    if task_type_filter:
        tasks = tasks.filter(task_type=task_type_filter)
    
    # Pagination
    paginator = Paginator(tasks, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Statistics
    stats = {
        'total_tasks': tasks.count(),
        'pending_tasks': tasks.filter(status='pending').count(),
        'in_progress_tasks': tasks.filter(status='in_progress').count(),
        'completed_today': tasks.filter(
            status='completed',
            completed_at__date=timezone.now().date()
        ).count(),
        'overdue_tasks': tasks.filter(
            status__in=['pending', 'in_progress'],
            due_date__lt=timezone.now()
        ).count(),
    }
    
    context = {
        'page_obj': page_obj,
        'stats': stats,
        'warehouse': warehouse,
        'status_filter': status_filter,
        'priority_filter': priority_filter,
        'task_type_filter': task_type_filter,
    }
    
    return render(request, 'stock_keeper/task_management.html', context)

@login_required
@user_passes_test(is_stock_keeper)
def start_task(request, task_id):
    """Start a task."""
    task = get_object_or_404(StockKeeperTask, id=task_id, assigned_to=request.user)
    
    if task.status == 'pending':
        task.start_task()
        messages.success(request, f'Task "{task.title}" started successfully.')
    else:
        messages.warning(request, f'Task "{task.title}" is already {task.get_status_display()}.')
    
    return redirect('stock_keeper:task_management')

@login_required
@user_passes_test(is_stock_keeper)
def complete_task(request, task_id):
    """Complete a task."""
    task = get_object_or_404(StockKeeperTask, id=task_id, assigned_to=request.user)
    
    if request.method == 'POST':
        completion_notes = request.POST.get('completion_notes', '')
        task.complete_task(completion_notes)
        
        # Update session statistics
        session = StockKeeperSession.objects.filter(
            user=request.user,
            is_active=True
        ).first()
        if session:
            session.tasks_completed += 1
            session.save()
        
        messages.success(request, f'Task "{task.title}" completed successfully.')
        return redirect('stock_keeper:task_management')
    
    return render(request, 'stock_keeper/complete_task.html', {'task': task})

@login_required
@user_passes_test(is_stock_keeper)
def edit_task(request, task_id):
    """Edit a task."""
    task = get_object_or_404(StockKeeperTask, id=task_id, assigned_to=request.user)
    
    if request.method == 'POST':
        form = StockKeeperTaskForm(request.POST, instance=task)
        if form.is_valid():
            form.save()
            messages.success(request, 'Task updated successfully.')
            return redirect('stock_keeper:task_management')
    else:
        form = StockKeeperTaskForm(instance=task)
    
    context = {
        'form': form,
        'task': task,
        'title': 'Edit Task'
    }
    return render(request, 'stock_keeper/task_form.html', context)

@login_required
@user_passes_test(is_stock_keeper)
def task_info(request, task_id):
    """View task information."""
    task = get_object_or_404(StockKeeperTask, id=task_id, assigned_to=request.user)
    
    context = {
        'task': task,
        'title': 'Task Information'
    }
    return render(request, 'stock_keeper/task_info.html', context)

@login_required
@csrf_exempt
def delete_task(request, task_id):
    """Delete a task."""
    if request.method == 'POST':
        try:
            task = get_object_or_404(StockKeeperTask, id=task_id, assigned_to=request.user)
            task_name = task.title
            task.delete()
            
            return JsonResponse({
                'success': True,
                'message': f'Task "{task_name}" deleted successfully.'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error deleting task: {str(e)}'
            }, status=500)
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'}, status=405)

@login_required
@user_passes_test(is_stock_keeper)
def cycle_count(request):
    """Cycle counting interface."""
    warehouse = Warehouse.objects.filter(is_active=True).first()
    if not warehouse:
        messages.error(request, 'No active warehouse found.')
        return redirect('stock_keeper:dashboard')
    
    # Get active count sessions
    active_sessions = PhysicalCountRecord.objects.filter(
        user=request.user,
        warehouse=warehouse
    ).values('count_session_id').distinct()
    
    # Get recent counts for display
    recent_counts = PhysicalCountRecord.objects.filter(
        user=request.user,
        warehouse=warehouse
    ).select_related('product', 'warehouse').order_by('-count_timestamp')[:10]
    
    # Group by session for display
    recent_sessions = []
    for session_id in active_sessions:
        session_records = PhysicalCountRecord.objects.filter(
            count_session_id=session_id['count_session_id'],
            user=request.user,
            warehouse=warehouse
        )
        if session_records.exists():
            first_record = session_records.first()
            total_items = session_records.count()
            completed_items = session_records.filter(counted_quantity__isnull=False).count()
            
            recent_sessions.append({
                'id': session_id['count_session_id'],
                'warehouse': warehouse,
                'start_date': first_record.count_timestamp,
                'counted_by': request.user,
                'total_items': total_items,
                'completed_items': completed_items,
                'status': 'completed' if completed_items == total_items else 'in_progress'
            })
    
    context = {
        'warehouse': warehouse,
        'active_sessions': active_sessions,
        'recent_counts': recent_sessions,
    }
    
    return render(request, 'stock_keeper/cycle_count.html', context)

@login_required
@user_passes_test(is_stock_keeper)
def start_count_session(request):
    """Start a new count session."""
    warehouse = Warehouse.objects.filter(is_active=True).first()
    if not warehouse:
        messages.error(request, 'No active warehouse found.')
        return redirect('stock_keeper:dashboard')
    
    if request.method == 'POST':
        section = request.POST.get('section', '')
        total_locations = request.POST.get('total_locations', 0)
        start_time = request.POST.get('start_time', '')
        estimated_duration = request.POST.get('estimated_duration', '')
        count_notes = request.POST.get('count_notes', '')
        
        # Generate session ID
        session_id = f"COUNT-{timezone.now().strftime('%Y%m%d')}-{request.user.id:03d}"
        
        # Create count session task
        task = StockKeeperTask.objects.create(
            task_type='count',
            assigned_to=request.user,
            warehouse=warehouse,
            title=f"Cycle Count - {section}",
            description=f"Physical count of {section} with {total_locations} locations. Duration: {estimated_duration} hours. Notes: {count_notes}",
            priority='normal',
            status='in_progress',
            started_at=timezone.now(),
            created_by=request.user,
        )
        
        messages.success(request, f'Count session "{session_id}" started for {section}.')
        return redirect('stock_keeper:cycle_count_session', session_id=session_id)
    
    context = {
        'warehouse': warehouse,
        'current_time': timezone.now(),
    }
    
    return render(request, 'stock_keeper/start_count_session.html', context)

@login_required
@user_passes_test(is_stock_keeper)
def cycle_count_session(request, session_id):
    """Active cycle count session."""
    # Get all active warehouses
    warehouses = Warehouse.objects.filter(is_active=True)
    
    # Get selected warehouse from session without defaulting to first
    selected_warehouse = request.session.get('selected_warehouse')
    
    warehouse = None
    if selected_warehouse:
        warehouse = Warehouse.objects.filter(id=selected_warehouse, is_active=True).first()
    
    # Check if there are any warehouses at all
    if not warehouses.exists():
        messages.error(request, 'No active warehouse found.')
        return redirect('stock_keeper:dashboard')
    
    # Initialize variables with defaults
    count_records = PhysicalCountRecord.objects.none()
    products = InventoryRecord.objects.none()
    total_locations = 0
    completed_locations = 0
    progress_percentage = 0
    
    # Only fetch data if a warehouse is selected
    if warehouse:
        # Get count records for this session
        count_records = PhysicalCountRecord.objects.filter(
            count_session_id=session_id,
            user=request.user,
            warehouse=warehouse
        )
        
        # Get products that need counting
        products = InventoryRecord.objects.filter(
            warehouse=warehouse
        ).select_related('product')
        
        # Calculate progress
        total_locations = products.count()
        completed_locations = count_records.count()
        progress_percentage = (completed_locations / total_locations * 100) if total_locations > 0 else 0
    
    # Find or create related StockKeeperTask for this cycle count session
    task = None
    try:
        # First try to find existing task
        task = StockKeeperTask.objects.filter(
            task_type='count',
            assigned_to=request.user,
            warehouse=warehouse,
            status__in=['pending', 'in_progress']
        ).first()
        
        # If no task found, create one automatically
        if not task and warehouse:
            task = StockKeeperTask.objects.create(
                title=f"Cycle Count Session {session_id}",
                description=f"Automatic cycle count task for session {session_id}",
                task_type='count',
                priority='normal',
                status='in_progress',
                assigned_to=request.user,
                warehouse=warehouse,
                due_date=timezone.now() + timezone.timedelta(days=1),
                reference_id=session_id
            )
            messages.success(request, f'Created cycle count task automatically for session {session_id}')
            
    except Exception as e:
        # If there's any error creating the task, we'll handle it gracefully
        print(f"Error creating/finding task: {e}")
        pass
    
    context = {
        'session_id': session_id,
        'warehouse': warehouse,
        'warehouses': warehouses,
        'selected_warehouse': selected_warehouse,
        'count_records': count_records,
        'products': products,
        'total_locations': total_locations,
        'completed_locations': completed_locations,
        'progress_percentage': progress_percentage,
        'task': task,  # Pass the related task (or None if creation failed)
        # Add the variables the template expects
        'session': {
            'count_session_id': session_id,
            'total_items': total_locations,
            'counted_items': completed_locations,
            'count_timestamp': timezone.now(),
            'counted_by': request.user,
            'section': 'General',
        },
        'current_item': products.first() if products.exists() else None,
        'recent_counts': count_records[:5] if count_records.exists() else [],
    }
    
    return render(request, 'stock_keeper/cycle_count_session.html', context)

@login_required
@user_passes_test(is_stock_keeper)
def cycle_count_details(request, session_id):
    """View detailed information about a cycle count session."""
    warehouse = Warehouse.objects.filter(is_active=True).first()
    if not warehouse:
        messages.error(request, 'No active warehouse found.')
        return redirect('stock_keeper:dashboard')
    
    # Get count records for this session
    count_records = PhysicalCountRecord.objects.filter(
        count_session_id=session_id,
        user=request.user,
        warehouse=warehouse
    ).select_related('product').order_by('-count_timestamp')
    
    # Calculate session statistics
    total_items = count_records.count()
    completed_items = count_records.filter(counted_quantity__isnull=False).count()
    pending_items = total_items - completed_items
    
    # Calculate accuracy if we have both system and counted quantities
    accuracy_records = count_records.filter(
        system_quantity__isnull=False,
        counted_quantity__isnull=False
    )
    
    if accuracy_records.exists():
        total_expected = sum(record.system_quantity for record in accuracy_records if record.system_quantity)
        total_counted = sum(record.counted_quantity for record in accuracy_records if record.counted_quantity)
        accuracy_percentage = (total_counted / total_expected * 100) if total_expected > 0 else 0
    else:
        accuracy_percentage = 0
    
    # Get session info from first record
    session_info = None
    if count_records.exists():
        first_record = count_records.first()
        session_info = {
            'id': session_id,
            'warehouse': warehouse,
            'start_date': first_record.count_timestamp,
            'counted_by': request.user,
            'total_items': total_items,
            'completed_items': completed_items,
            'pending_items': pending_items,
            'accuracy_percentage': round(accuracy_percentage, 1),
            'status': 'completed' if completed_items == total_items else 'in_progress'
        }
    
    context = {
        'session_id': session_id,
        'session_info': session_info,
        'count_records': count_records,
        'warehouse': warehouse,
    }
    
    return render(request, 'stock_keeper/cycle_count_details.html', context)

@login_required
@user_passes_test(is_stock_keeper)
def record_count(request, session_id):
    """Record a count for a specific product."""
    if request.method == 'POST':
        try:
            product_id = request.POST.get('product_id')
            location_code = request.POST.get('location_code', '')
            # Convert to integers with proper error handling
            system_quantity_str = request.POST.get('system_quantity', '0')
            counted_quantity_str = request.POST.get('counted_quantity', '0')
            system_quantity = int(system_quantity_str) if system_quantity_str else None
            counted_quantity = int(counted_quantity_str) if counted_quantity_str else None
            condition_status = request.POST.get('condition_status', 'good')
            count_notes = request.POST.get('count_notes', '')
            
            # Get warehouse ID from request or use the first active warehouse
            warehouse_id = request.POST.get('warehouse_id')
            if warehouse_id:
                warehouse = get_object_or_404(Warehouse, id=warehouse_id, is_active=True)
            else:
                warehouse = Warehouse.objects.filter(is_active=True).first()
                if not warehouse:
                    return JsonResponse({
                        'success': False,
                        'message': 'No active warehouse selected. Please select a warehouse first.'
                    })
            
            product = get_object_or_404(Product, id=product_id)
            
            # Create or update count record
            count_record, created = PhysicalCountRecord.objects.get_or_create(
                count_session_id=session_id,
                user=request.user,
                warehouse=warehouse,
                product=product,
                location_code=location_code,
                defaults={
                    'system_quantity': system_quantity,
                    'counted_quantity': counted_quantity,
                    'condition_status': condition_status,
                    'count_notes': count_notes,
                }
            )
            
            if not created:
                count_record.counted_quantity = counted_quantity
                count_record.condition_status = condition_status
                count_record.count_notes = count_notes
                count_record.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Count recorded successfully',
                'variance': count_record.variance,
            })
        except ValueError as e:
            return JsonResponse({
                'success': False,
                'message': f'Invalid quantity value: {str(e)}',
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error recording count: {str(e)}',
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

@login_required
@user_passes_test(is_stock_keeper)
def submit_count_variance(request, session_id):
    """Submit count variances for review."""
    if request.method == 'POST':
        variances = request.POST.getlist('variances[]')
        
        # Process variances (this would typically create adjustment records)
        for variance_data in variances:
            # Parse variance data and create adjustment records
            pass
        
        messages.success(request, 'Count variances submitted for review.')
        return redirect('stock_keeper:cycle_count_session', session_id=session_id)
    
    return redirect('stock_keeper:cycle_count_session', session_id=session_id)

@login_required
@user_passes_test(is_stock_keeper)
def cycle_count_sessions(request):
    """List all cycle count sessions for the user."""
    warehouse = Warehouse.objects.filter(is_active=True).first()
    if not warehouse:
        messages.error(request, 'No active warehouse found.')
        return redirect('stock_keeper:dashboard')
    
    # Get all count sessions for the user
    sessions = PhysicalCountRecord.objects.filter(
        user=request.user,
        warehouse=warehouse
    ).values('count_session_id').distinct().order_by('-count_session_id')
    
    # Get session details
    session_details = []
    for session in sessions:
        session_id = session['count_session_id']
        records = PhysicalCountRecord.objects.filter(
            count_session_id=session_id,
            user=request.user,
            warehouse=warehouse
        )
        
        total_products = records.count()
        completed_products = records.filter(counted_quantity__isnull=False).count()
        total_variance = sum(abs(record.variance) for record in records if record.variance is not None)
        
        session_details.append({
            'session_id': session_id,
            'total_products': total_products,
            'completed_products': completed_products,
            'total_variance': total_variance,
            'progress': (completed_products / total_products * 100) if total_products > 0 else 0,
            'created_date': records.first().count_timestamp if records.exists() else None,
        })
    
    context = {
        'warehouse': warehouse,
        'sessions': session_details,
    }
    
    return render(request, 'stock_keeper/cycle_count_sessions.html', context)

@login_required
@user_passes_test(is_stock_keeper)
def submit_count(request):
    """Submit a count for the current item."""
    if request.method == 'POST':
        try:
            product_id = request.POST.get('product_id')
            counted_quantity = int(request.POST.get('counted_quantity', 0))
            condition = request.POST.get('condition', 'good')
            notes = request.POST.get('notes', '')
            session_id = request.POST.get('session_id')
            
            # Get warehouse from session or use first active warehouse
            warehouse = Warehouse.objects.filter(is_active=True).first()
            if not warehouse:
                return JsonResponse({
                    'success': False,
                    'message': 'No active warehouse found.'
                })
            
            product = get_object_or_404(Product, id=product_id)
            
            # Get system quantity from inventory if available
            inventory = InventoryRecord.objects.filter(
                product=product,
                warehouse=warehouse
            ).first()
            system_quantity = inventory.quantity if inventory else 0
            
            # Create or update count record
            count_record, created = PhysicalCountRecord.objects.get_or_create(
                count_session_id=session_id,
                user=request.user,
                warehouse=warehouse,
                product=product,
                defaults={
                    'system_quantity': system_quantity,
                    'counted_quantity': counted_quantity,
                    'condition_status': condition,
                    'count_notes': notes,
                }
            )
            
            if not created:
                count_record.counted_quantity = counted_quantity
                count_record.condition_status = condition
                count_record.count_notes = notes
                count_record.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Count submitted successfully',
                'variance': count_record.variance,
            })
        except ValueError as e:
            return JsonResponse({
                'success': False,
                'message': f'Invalid quantity value: {str(e)}',
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error submitting count: {str(e)}',
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

@login_required
@user_passes_test(is_stock_keeper)
@csrf_exempt
def complete_session(request):
    """Complete the current cycle count session."""
    if request.method == 'POST':
        try:
            session_id = request.POST.get('session_id')
            
            if not session_id:
                return JsonResponse({
                    'success': False,
                    'message': 'Session ID is required.'
                })
            
            # Get warehouse from session or use first active warehouse
            warehouse = Warehouse.objects.filter(is_active=True).first()
            if not warehouse:
                return JsonResponse({
                    'success': False,
                    'message': 'No active warehouse found.'
                })
            
            # Mark all records for this session as completed
            try:
                # Get all records for this session
                session_records = PhysicalCountRecord.objects.filter(
                    count_session_id=session_id,
                    user=request.user,
                    warehouse=warehouse
                )
                
                if not session_records.exists():
                    return JsonResponse({
                        'success': False,
                        'message': 'No records found for this session.',
                    })
                
                # Mark session as completed by updating all records
                # We could add a status field to PhysicalCountRecord if needed
                # For now, we'll just return success
                
                return JsonResponse({
                    'success': True,
                    'message': f'Session {session_id} completed successfully with {session_records.count()} records',
                })
                
            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'message': f'Error processing session: {str(e)}',
                })
                
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error completing session: {str(e)}',
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})




@login_required
@user_passes_test(is_stock_keeper)
def warehouse_list(request):
    """List all warehouses."""
    if request.method == 'POST' and request.POST.get('action') == 'add_warehouse':
        name = request.POST.get('name')
        location = request.POST.get('location', '')
        capacity = request.POST.get('capacity')
        
        if name:
            warehouse = Warehouse.objects.create(
                name=name,
                location=location or name,
                is_active=True
            )
            messages.success(request, f'Warehouse "{name}" added successfully.')
            return redirect('stock_keeper:warehouses')
        else:
            messages.error(request, 'Warehouse name is required.')
    
    warehouses = Warehouse.objects.filter(is_active=True)
    
    # Enhance warehouses with inventory data using InventoryRecord
    total_products = 0
    total_units = 0
    
    for warehouse in warehouses:
        # Get inventory for this warehouse using InventoryRecord
        inventory = InventoryRecord.objects.filter(warehouse=warehouse)
        
        # Calculate totals
        warehouse.total_items = inventory.count()
        warehouse.total_quantity = inventory.aggregate(total=Sum('quantity'))['total'] or 0
        warehouse.low_stock_items = inventory.filter(quantity__lte=10).count()
        
        # Calculate capacity and utilization (example values)
        warehouse.capacity = 25000  # This should come from Warehouse model
        warehouse.current = warehouse.total_quantity
        warehouse.utilization = (warehouse.current / warehouse.capacity * 100) if warehouse.capacity > 0 else 0
        
        total_products += warehouse.total_items
        total_units += warehouse.total_quantity
        
        # Set empty product types since Product model doesn't have categories
        warehouse.product_types = []
    
    context = {
        'warehouses': warehouses,
        'total_products': total_products,
        'total_units': total_units,
    }
    
    return render(request, 'stock_keeper/warehouse_list.html', context)

@login_required
@user_passes_test(is_stock_keeper)
def warehouse_detail(request, warehouse_id):
    """Warehouse detail view with inventory."""
    warehouse = get_object_or_404(Warehouse, id=warehouse_id)
    
    # Get inventory for this warehouse using InventoryRecord
    inventory = InventoryRecord.objects.filter(
        warehouse=warehouse
    ).select_related('product').order_by('-quantity')
    
    # Calculate totals
    total_items = inventory.count()
    low_stock_items = inventory.filter(quantity__lte=10).count()
    
    # Apply filters
    search = request.GET.get('search', '')
    if search:
        inventory = inventory.filter(
            Q(product__name_en__icontains=search) |
            Q(product__name_ar__icontains=search) |
            Q(location__zone__icontains=search)
        )
    
    status_filter = request.GET.get('status', '')
    if status_filter:
        if status_filter == 'low_stock':
            inventory = inventory.filter(quantity__lte=10)
        elif status_filter == 'out_of_stock':
            inventory = inventory.filter(quantity=0)
        elif status_filter == 'overstocked':
            inventory = inventory.filter(quantity__gte=100)
    
    # Handle location management
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'add_location':
            zone = request.POST.get('zone')
            shelf = request.POST.get('shelf')
            description = request.POST.get('description', '')
            if zone and shelf:
                WarehouseLocation.objects.create(
                    warehouse=warehouse,
                    zone=zone,
                    shelf=shelf,
                    description=description
                )
                messages.success(request, f'Location {zone}-{shelf} added successfully.')
                return redirect('stock_keeper:warehouse_detail', warehouse_id=warehouse_id)
        elif action == 'delete_location':
            location_id = request.POST.get('location_id')
            if location_id:
                try:
                    location = WarehouseLocation.objects.get(id=location_id, warehouse=warehouse)
                    location.delete()
                    messages.success(request, 'Location deleted successfully.')
                except WarehouseLocation.DoesNotExist:
                    messages.error(request, 'Location not found.')
                return redirect('stock_keeper:warehouse_detail', warehouse_id=warehouse_id)
    
    # Pagination
    paginator = Paginator(inventory, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get all locations for this warehouse
    locations = WarehouseLocation.objects.filter(warehouse=warehouse).order_by('zone', 'shelf')
    
    # Create location map (color-coded by utilization)
    location_map = {}
    for loc in locations:
        loc_inventory = InventoryRecord.objects.filter(location=loc, warehouse=warehouse)
        total_qty = loc_inventory.aggregate(total=Sum('quantity'))['total'] or 0
        item_count = loc_inventory.count()
        location_map[loc.id] = {
            'location': loc,
            'total_quantity': total_qty,
            'item_count': item_count,
            'utilization': min(100, (total_qty / 100) * 100) if total_qty > 0 else 0  # Simple utilization calculation
        }
    
    context = {
        'warehouse': warehouse,
        'page_obj': page_obj,
        'total_items': total_items,
        'low_stock_items': low_stock_items,
        'search_query': search,
        'status_filter': status_filter,
        'locations': locations,
        'location_map': location_map,
    }
    
    return render(request, 'stock_keeper/warehouse_detail.html', context)

@login_required
@user_passes_test(is_stock_keeper)
def warehouse_report(request, warehouse_id):
    """Generate warehouse report."""
    from django.http import HttpResponse
    import csv
    from io import StringIO
    
    warehouse = get_object_or_404(Warehouse, id=warehouse_id)
    inventory = InventoryRecord.objects.filter(warehouse=warehouse).select_related('product')
    
    # Create CSV response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="warehouse_{warehouse.name}_report.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Warehouse Report', warehouse.name])
    writer.writerow(['Generated', timezone.now().strftime('%Y-%m-%d %H:%M:%S')])
    writer.writerow([])
    writer.writerow(['Product ID', 'Product Name', 'SKU', 'Quantity', 'Location', 'Last Updated'])
    
    for inv in inventory:
        writer.writerow([
            f'P{inv.product.id:03d}',
            inv.product.name_en,
            inv.product.code or 'N/A',
            inv.quantity,
            inv.location.zone if inv.location else 'N/A',
            inv.last_updated.strftime('%Y-%m-%d %H:%M:%S') if inv.last_updated else 'N/A'
        ])
    
    return response


@login_required
@user_passes_test(is_stock_keeper)
def receive_stock(request):
    """Stock receiving interface."""
    # Get receiving type filter
    receiving_type = request.GET.get('type', 'client_stock')  # client_stock or sourcing
    
    if request.method == 'POST':
        # Handle stock receiving
        product_id = request.POST.get('product_id')
        quantity = int(request.POST.get('quantity', 0))
        warehouse_id = request.POST.get('warehouse_id')
        location_code = request.POST.get('location_code', '')
        condition = request.POST.get('condition', 'good')
        notes = request.POST.get('notes', '')
        reference_number = request.POST.get('reference_number', '')
        
        if product_id and quantity > 0 and warehouse_id:
            product = get_object_or_404(Product, id=product_id)
            warehouse = get_object_or_404(Warehouse, id=warehouse_id)
            
            # Create movement record
            movement = InventoryMovement.objects.create(
                movement_type='stock_in',
                product=product,
                quantity=quantity,
                to_warehouse=warehouse,
                to_location=location_code,
                created_by=request.user,
                processed_by=request.user,
                status='completed',
                condition=condition,
                notes=notes,
                reason='Stock receiving',
                reference_number=reference_number or f'SIR-{timezone.now().strftime("%Y-%m%d")}-{movement.id if "movement" in locals() else ""}',
                reference_type='Client Stock-In' if receiving_type == 'client_stock' else 'Sourcing Purchase'
            )
            
            # Update inventory
            inventory, created = InventoryRecord.objects.get_or_create(
                product=product,
                warehouse=warehouse,
                defaults={'quantity': 0}
            )
            inventory.quantity += quantity
            inventory.save()
            
            messages.success(request, f'Successfully received {quantity} units of {product.name_en}')
            return redirect('stock_keeper:receive_stock')
    
    # Apply date filter
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    search_query = request.GET.get('search', '')

    # Get recent receivings (completed stock_in movements)
    recent_receivings = InventoryMovement.objects.filter(
        movement_type='stock_in',
        status='completed'
    ).select_related('product', 'to_warehouse', 'processed_by', 'product__seller').order_by('-created_at')

    # Apply search filter
    if search_query:
        recent_receivings = recent_receivings.filter(
            Q(reference_number__icontains=search_query) |
            Q(product__name_en__icontains=search_query) |
            Q(product__name_ar__icontains=search_query) |
            Q(product__code__icontains=search_query) |
            Q(tracking_number__icontains=search_query)
        )

    # Filter by receiving type
    if receiving_type == 'client_stock':
        recent_receivings = recent_receivings.filter(
            Q(reference_type='Client Stock-In') | Q(reference_type='') | Q(reference_type__isnull=True)
        )
    elif receiving_type == 'sourcing':
        recent_receivings = recent_receivings.filter(reference_type='Sourcing Purchase')

    # Apply date filter
    if date_from:
        recent_receivings = recent_receivings.filter(created_at__date__gte=date_from)
    if date_to:
        recent_receivings = recent_receivings.filter(created_at__date__lte=date_to)

    # Limit results (show more if searching)
    if search_query:
        recent_receivings = recent_receivings[:50]
    else:
        recent_receivings = recent_receivings[:10]
    
    # Get pending receiving tasks
    pending_receiving = InventoryMovement.objects.filter(
        movement_type='stock_in',
        status='pending'
    ).select_related('product', 'to_warehouse')
    
    # Get products and warehouses for form
    products = Product.objects.all().order_by('name_en')
    warehouses = Warehouse.objects.filter(is_active=True).order_by('name')
    
    # Get sourcing requests for Sourcing Purchase
    from sourcing.models import SourcingRequest
    sourcing_requests = SourcingRequest.objects.filter(
        status__in=['delivered', 'completed']
    ).order_by('-created_at')[:20] if receiving_type == 'sourcing' else []
    
    context = {
        'pending_receiving': pending_receiving,
        'recent_receivings': recent_receivings,
        'products': products,
        'warehouses': warehouses,
        'receiving_type': receiving_type,
        'sourcing_requests': sourcing_requests,
        'date_from': date_from,
        'date_to': date_to,
        'search_query': search_query,
    }

    return render(request, 'stock_keeper/receive_stock.html', context)

@login_required
@user_passes_test(is_stock_keeper)
def ship_orders(request):
    """Order shipping interface."""
    if request.method == 'POST':
        action = request.POST.get('action')

        # Handle start picking action first
        if action == 'start_picking':
            order_id = request.POST.get('order_id')
            if order_id:
                try:
                    order = Order.objects.get(id=order_id)
                    # Update workflow status to packaging_in_progress
                    order.workflow_status = 'packaging_in_progress'
                    order.save()
                    messages.success(request, f'Started picking for order {order.order_code}')
                except Order.DoesNotExist:
                    messages.error(request, 'Order not found')
                except Exception as e:
                    messages.error(request, f'Error starting order: {str(e)}')
            return redirect('stock_keeper:ship_orders')

        # Handle order shipping
        order_id = request.POST.get('order_id')
        product_id = request.POST.get('product_id')
        try:
            quantity = int(request.POST.get('quantity', 0))
        except (ValueError, TypeError):
            quantity = 0
        warehouse_id = request.POST.get('warehouse_id')

        if order_id and product_id and quantity > 0 and warehouse_id:
            order = get_object_or_404(Order, id=order_id)
            product = get_object_or_404(Product, id=product_id)
            warehouse = get_object_or_404(Warehouse, id=warehouse_id)
            
            # Check if enough stock
            inventory = InventoryRecord.objects.filter(
                product=product,
                warehouse=warehouse
            ).first()
            
            if inventory and inventory.quantity >= quantity:
                # Create movement record
                movement = InventoryMovement.objects.create(
                    movement_type='stock_out',
                    product=product,
                    quantity=quantity,
                    from_warehouse=warehouse,
                    created_by=request.user,
                    processed_by=request.user,
                    status='completed',
                    reference_number=order.order_code,
                    reference_type='Order',
                    reason='Order fulfillment'
                )
                
                # Update inventory
                inventory.quantity -= quantity
                inventory.save()
                
                # Update order status
                order.status = 'shipped'
                order.save()
                
                messages.success(request, f'Successfully shipped {quantity} units of {product.name_en} for order {order.order_code}')
            else:
                messages.error(request, 'Insufficient stock for shipping')
            
            return redirect('stock_keeper:ship_orders')
    
    # Get status filter
    status_filter = request.GET.get('status', 'pending')
    
    # Apply date filter
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    # Get orders ready for shipping
    if status_filter == 'ready':
        # Orders ready for packing (packaging completed)
        ready_orders = Order.objects.filter(
            workflow_status__in=['packaging_completed', 'ready_for_delivery']
        ).select_related('seller').prefetch_related('items__product').order_by('-created_at')
    else:
        # Pending orders (awaiting preparation - pick_and_pack or stockkeeper_approved)
        ready_orders = Order.objects.filter(
            workflow_status__in=['pick_and_pack', 'stockkeeper_approved', 'callcenter_approved']
        ).select_related('seller').prefetch_related('items__product').order_by('-created_at')
    
    # Apply date filter
    if date_from:
        ready_orders = ready_orders.filter(created_at__date__gte=date_from)
    if date_to:
        ready_orders = ready_orders.filter(created_at__date__lte=date_to)

    # Get warehouses for form
    warehouses = Warehouse.objects.filter(is_active=True).order_by('name')
    
    # Count orders by status
    pending_count = Order.objects.filter(workflow_status__in=['pick_and_pack', 'stockkeeper_approved', 'callcenter_approved']).count()
    ready_count = Order.objects.filter(workflow_status__in=['packaging_completed', 'ready_for_delivery']).count()
    
    context = {
        'ready_orders': ready_orders,
        'warehouses': warehouses,
        'status_filter': status_filter,
        'pending_count': pending_count,
        'ready_count': ready_count,
        'date_from': date_from,
        'date_to': date_to,
    }
    
    return render(request, 'stock_keeper/ship_orders.html', context)

@login_required
@user_passes_test(is_stock_keeper)
def transfer_stock(request):
    """Stock transfer interface."""
    if request.method == 'POST':
        # Handle stock transfer
        product_id = request.POST.get('product_id')
        quantity = int(request.POST.get('quantity', 0))
        from_warehouse_id = request.POST.get('from_warehouse_id')
        to_warehouse_id = request.POST.get('to_warehouse_id')
        from_location = request.POST.get('from_location', '')
        to_location = request.POST.get('to_location', '')
        notes = request.POST.get('notes', '')
        
        if product_id and quantity > 0 and from_warehouse_id and to_warehouse_id:
            product = get_object_or_404(Product, id=product_id)
            from_warehouse = get_object_or_404(Warehouse, id=from_warehouse_id)
            to_warehouse = get_object_or_404(Warehouse, id=to_warehouse_id)
            
            # Check if enough stock in source warehouse
            from_inventory = InventoryRecord.objects.filter(
                product=product,
                warehouse=from_warehouse
            ).first()
            
            if from_inventory and from_inventory.quantity >= quantity:
                # Create movement record
                movement = InventoryMovement.objects.create(
                    movement_type='transfer',
                    product=product,
                    quantity=quantity,
                    from_warehouse=from_warehouse,
                    to_warehouse=to_warehouse,
                    from_location=from_location,
                    to_location=to_location,
                    created_by=request.user,
                    processed_by=request.user,
                    status='completed',
                    notes=notes,
                    reason='Inter-warehouse transfer'
                )
                
                # Update source inventory
                from_inventory.quantity -= quantity
                from_inventory.save()
                
                # Update destination inventory
                to_inventory, created = InventoryRecord.objects.get_or_create(
                    product=product,
                    warehouse=to_warehouse,
                    defaults={'quantity': 0}
                )
                to_inventory.quantity += quantity
                # Note: location is a ForeignKey, not a CharField
                # If location_code is needed, it should be handled through WarehouseLocation model
                to_inventory.save()
                
                messages.success(request, f'Successfully transferred {quantity} units of {product.name_en} from {from_warehouse.name} to {to_warehouse.name}')
            else:
                messages.error(request, 'Insufficient stock for transfer')
            
            return redirect('stock_keeper:transfer_stock')
    
    # Get pending transfer requests
    pending_transfers = InventoryMovement.objects.filter(
        movement_type='transfer',
        status='pending'
    ).select_related('product', 'from_warehouse', 'to_warehouse')
    
    # Get products and warehouses for form
    products = Product.objects.all().order_by('name_en')
    warehouses = Warehouse.objects.filter(is_active=True).order_by('name')
    
    context = {
        'pending_transfers': pending_transfers,
        'products': products,
        'warehouses': warehouses,
    }
    
    return render(request, 'stock_keeper/transfer_stock.html', context)

@login_required
@user_passes_test(is_stock_keeper)
def inventory_log(request):
    """Wrapper to show movement history as Inventory Log."""
    return movement_history(request)

@login_required
@user_passes_test(is_stock_keeper)
def return_orders(request):
    """Returns processing page: scan barcode, restock good items, log damaged."""
    # Get filters
    status_filter = request.GET.get('status', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    search_query = request.GET.get('search', '')
    
    if request.method == 'POST':
        try:
            order_code = request.POST.get('order_code', '').strip()
            product_id = request.POST.get('product_id')
            good_qty = int(request.POST.get('good_qty', 0) or 0)
            damaged_qty = int(request.POST.get('damaged_qty', 0) or 0)
            damage_reason = request.POST.get('damage_reason', '')

            if not order_code or not product_id or (good_qty + damaged_qty) <= 0:
                messages.error(request, 'Invalid return data.')
                return redirect('stock_keeper:return_orders')

            warehouse = Warehouse.objects.filter(is_active=True).first()
            product = get_object_or_404(Product, id=product_id)

            # Restock good quantity
            if good_qty > 0 and warehouse:
                InventoryMovement.objects.create(
                    movement_type='stock_in',
                    product=product,
                    quantity=good_qty,
                    to_warehouse=warehouse,
                    status='completed',
                    reference_number=order_code,
                    reference_type='Return',
                    reason='Return restock',
                    created_by=request.user,
                    processed_by=request.user,
                )
                inv, _ = InventoryRecord.objects.get_or_create(product=product, warehouse=warehouse, defaults={'quantity': 0})
                inv.quantity += good_qty
                inv.save()

            # Log damaged quantity
            if damaged_qty > 0 and warehouse:
                InventoryMovement.objects.create(
                    movement_type='adjustment',
                    product=product,
                    quantity=damaged_qty,
                    to_warehouse=warehouse,
                    status='completed',
                    reference_number=order_code,
                    reference_type='Return',
                    reason=f'Damaged: {damage_reason}',
                    created_by=request.user,
                    processed_by=request.user,
                )

            messages.success(request, 'Return processed successfully.')
            return redirect('stock_keeper:return_orders')
        except Exception as e:
            messages.error(request, f'Error processing return: {str(e)}')
            return redirect('stock_keeper:return_orders')

    # Get status filter
    status_filter = request.GET.get('status', 'awaiting')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    search_query = request.GET.get('search', '')
    
    # Get return orders (movements with reference_type='Return')
    return_movements = InventoryMovement.objects.filter(
        reference_type='Return'
    ).select_related('product', 'to_warehouse', 'processed_by', 'product__seller').order_by('-created_at')
    
    # Apply search filter
    if search_query:
        return_movements = return_movements.filter(
            Q(reference_number__icontains=search_query) |
            Q(product__name_en__icontains=search_query) |
            Q(reason__icontains=search_query) |
            Q(product__seller__email__icontains=search_query)
        )
    
    # Filter by status
    if status_filter == 'completed':
        return_movements = return_movements.filter(status='completed')
    else:
        return_movements = return_movements.filter(status__in=['pending', 'in_progress'])
    
    # Apply date filter
    if date_from:
        return_movements = return_movements.filter(created_at__date__gte=date_from)
    if date_to:
        return_movements = return_movements.filter(created_at__date__lte=date_to)
    
    # Get summary counts
    total_returns = InventoryMovement.objects.filter(reference_type='Return').count()
    awaiting_inspection = InventoryMovement.objects.filter(
        reference_type='Return',
        status__in=['pending', 'in_progress']
    ).count()
    completed_returns = InventoryMovement.objects.filter(
        reference_type='Return',
        status='completed'
    ).count()
    
    products = Product.objects.all().order_by('name_en')
    
    context = {
        'products': products,
        'return_movements': return_movements,
        'status_filter': status_filter,
        'total_returns': total_returns,
        'awaiting_inspection': awaiting_inspection,
        'completed_returns': completed_returns,
        'date_from': date_from,
        'date_to': date_to,
        'search_query': search_query,
    }
    
    return render(request, 'stock_keeper/return_orders.html', context)

@login_required
@user_passes_test(is_stock_keeper)
def movement_history(request):
    """Movement history view."""
    # Handle export
    if request.GET.get('export') == 'excel':
        return export_movement_history_excel(request)
    
    movements = InventoryMovement.objects.select_related(
        'product', 'from_warehouse', 'to_warehouse', 'created_by', 'processed_by'
    ).order_by('-created_at')
    
    # Apply search filter
    search_query = request.GET.get('search', '')
    if search_query:
        movements = movements.filter(
            Q(product__name_en__icontains=search_query) |
            Q(product__code__icontains=search_query) |
            Q(reference_number__icontains=search_query) |
            Q(tracking_number__icontains=search_query)
        )
    
    # Apply filters
    movement_type = request.GET.get('type', '')
    if movement_type:
        movements = movements.filter(movement_type=movement_type)
    
    warehouse_id = request.GET.get('warehouse', '')
    if warehouse_id:
        movements = movements.filter(
            Q(from_warehouse_id=warehouse_id) | Q(to_warehouse_id=warehouse_id)
        )
    
    date_from = request.GET.get('date_from', '')
    if date_from:
        movements = movements.filter(created_at__date__gte=date_from)
    
    date_to = request.GET.get('date_to', '')
    if date_to:
        movements = movements.filter(created_at__date__lte=date_to)
    
    # Pagination
    paginator = Paginator(movements, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    warehouses = Warehouse.objects.filter(is_active=True)
    
    context = {
        'movements': page_obj,
        'warehouses': warehouses,
        'movement_type_filter': movement_type,
        'warehouse_filter': warehouse_id,
        'date_from': date_from,
        'date_to': date_to,
        'search_query': search_query,
    }
    
    return render(request, 'stock_keeper/movement_history.html', context)

@login_required
def export_movement_history_excel(request):
    """Export movement history to Excel - RESTRICTED TO SUPER ADMIN ONLY."""
    from django.http import HttpResponse
    import csv
    from io import StringIO
    from users.models import AuditLog

    # SECURITY: Restrict data export to Super Admin only (P0 CRITICAL requirement)
    if not request.user.is_superuser:
        from utils.views import permission_denied_authenticated
        AuditLog.objects.create(
            user=request.user,
            action='unauthorized_export_attempt',
            entity_type='inventory_movement',
            description=f"Unauthorized attempt to export movement history by {request.user.email}",
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        return permission_denied_authenticated(
            request,
            message="Data export is restricted to Super Admin only for security compliance."
        )
    
    movements = InventoryMovement.objects.select_related(
        'product', 'from_warehouse', 'to_warehouse', 'processed_by'
    ).order_by('-created_at')
    
    # Apply same filters as view
    search_query = request.GET.get('search', '')
    if search_query:
        movements = movements.filter(
            Q(product__name_en__icontains=search_query) |
            Q(product__code__icontains=search_query) |
            Q(reference_number__icontains=search_query)
        )
    
    movement_type = request.GET.get('type', '')
    if movement_type:
        movements = movements.filter(movement_type=movement_type)
    
    warehouse_id = request.GET.get('warehouse', '')
    if warehouse_id:
        movements = movements.filter(
            Q(from_warehouse_id=warehouse_id) | Q(to_warehouse_id=warehouse_id)
        )
    
    date_from = request.GET.get('date_from', '')
    if date_from:
        movements = movements.filter(created_at__date__gte=date_from)
    
    date_to = request.GET.get('date_to', '')
    if date_to:
        movements = movements.filter(created_at__date__lte=date_to)
    
    # Create CSV response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="stock_history.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Log ID', 'Date & Time', 'Type', 'SKU', 'Product', 'Quantity', 'Warehouse', 'User', 'Reference'])
    
    for m in movements:
        warehouse_name = ''
        if m.to_warehouse:
            warehouse_name = m.to_warehouse.name
        elif m.from_warehouse:
            warehouse_name = m.from_warehouse.name
        
        writer.writerow([
            f'LOG-{m.id:03d}',
            m.created_at.strftime('%Y-%m-%d %H:%M'),
            m.get_movement_type_display(),
            m.product.code or 'N/A',
            m.product.name_en,
            f"{'+' if m.movement_type == 'stock_in' else '-'}{m.quantity}",
            warehouse_name or 'N/A',
            m.processed_by.get_full_name() or m.processed_by.username,
            m.reference_number or 'N/A'
        ])

    # Audit log for successful export (P0 CRITICAL security requirement)
    AuditLog.objects.create(
        user=request.user,
        action='data_export',
        entity_type='inventory_movement',
        description=f"Exported {movements.count()} inventory movements to CSV",
        ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT', '')
    )

    return response

@login_required
@user_passes_test(is_stock_keeper)
def alerts(request):
    """Stock alerts view."""
    # Get all warehouses
    warehouses = Warehouse.objects.filter(is_active=True)
    
    # Get stock information for all warehouses using InventoryRecord
    warehouse_stock_data = []
    for warehouse in warehouses:
        # Get inventory records for this warehouse using InventoryRecord
        inventory_records = InventoryRecord.objects.filter(warehouse=warehouse)
        
        # Calculate stock statistics
        total_items = inventory_records.count()
        low_stock_items = inventory_records.filter(quantity__lte=10).count()
        out_of_stock_items = inventory_records.filter(quantity=0).count()
        
        # Get existing alerts for this warehouse
        warehouse_alerts = StockAlert.objects.filter(
            warehouse=warehouse,
            is_resolved=False
        ).count()
        
        warehouse_stock_data.append({
            'warehouse': warehouse,
            'total_items': total_items,
            'low_stock_items': low_stock_items,
            'out_of_stock_items': out_of_stock_items,
            'alerts_count': warehouse_alerts,
        })
    
    # Get all alerts
    alerts = StockAlert.objects.select_related(
        'product', 'warehouse', 'resolved_by'
    ).order_by('-created_at')
    
    # Apply filters
    warehouse_filter = request.GET.get('warehouse', '')
    if warehouse_filter:
        alerts = alerts.filter(warehouse_id=warehouse_filter)
    
    alert_type = request.GET.get('type', '')
    if alert_type:
        alerts = alerts.filter(alert_type=alert_type)
    
    priority = request.GET.get('priority', '')
    if priority:
        alerts = alerts.filter(priority=priority)
    
    resolved = request.GET.get('resolved', '')
    if resolved == 'true':
        alerts = alerts.filter(is_resolved=True)
    elif resolved == 'false':
        alerts = alerts.filter(is_resolved=False)
    
    # Pagination
    paginator = Paginator(alerts, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'warehouse_stock_data': warehouse_stock_data,
        'alerts': page_obj,
        'warehouse_filter': warehouse_filter,
        'alert_type_filter': alert_type,
        'priority_filter': priority,
        'resolved_filter': resolved,
    }
    
    return render(request, 'stock_keeper/alerts.html', context)

@login_required
@user_passes_test(is_stock_keeper)
def resolve_alert(request, alert_id):
    """Resolve a stock alert."""
    alert = get_object_or_404(StockAlert, id=alert_id)
    alert.resolve(request.user)
    messages.success(request, f'Alert "{alert.alert_type}" has been resolved.')
    return redirect('stock_keeper:alerts')

# API Views for AJAX
@login_required
@csrf_exempt
def api_search_product(request):
    """API endpoint for product search."""
    if request.method == 'POST':
        data = json.loads(request.body)
        search_term = data.get('search', '')
        
        products = Product.objects.filter(
            Q(name_en__icontains=search_term) |
            Q(name_ar__icontains=search_term) |
            Q(code__icontains=search_term)
        )[:10]
        
        results = []
        for product in products:
            results.append({
                'id': product.id,
                'name': product.name_en,
                'code': product.code,
                'image': product.image.url if product.image else '',
            })
        
        return JsonResponse({'results': results})
    
    return JsonResponse({'error': 'Invalid request'})

@login_required
def api_get_inventory(request, product_id):
    """API endpoint to get inventory for a product."""
    product = get_object_or_404(Product, id=product_id)
    inventory = InventoryRecord.objects.filter(
        product=product
    ).select_related('warehouse')
    
    results = []
    for inv in inventory:
        results.append({
            'warehouse_id': inv.warehouse.id,
            'warehouse_name': inv.warehouse.name,
            'quantity': inv.quantity,
            'location': inv.location.zone if inv.location else '',
            'is_low_stock': inv.is_low_stock,
        })
    
    return JsonResponse({'inventory': results})

# Additional API endpoints for stock keeper operations
@login_required
@csrf_exempt
def api_get_movement(request, movement_id):
    """API endpoint to get movement details."""
    movement = get_object_or_404(InventoryMovement, id=movement_id)
    
    return JsonResponse({
        'id': movement.id,
        'tracking_number': movement.tracking_number,
        'movement_type': movement.movement_type,
        'status': movement.status,
        'quantity': movement.quantity,
        'product': {
            'id': movement.product.id,
            'name': movement.product.name_en,
            'code': movement.product.code,
        },
        'from_warehouse': {
            'id': movement.from_warehouse.id,
            'name': movement.from_warehouse.name,
        } if movement.from_warehouse else None,
        'to_warehouse': {
            'id': movement.to_warehouse.id,
            'name': movement.to_warehouse.name,
        } if movement.to_warehouse else None,
        'reference_number': movement.reference_number,
        'reason': movement.reason,
        'notes': movement.notes,
    })

@login_required
@csrf_exempt
def api_get_order(request, order_id):
    """API endpoint to get order details."""
    order = get_object_or_404(Order, id=order_id)
    
    return JsonResponse({
        'id': order.id,
        'order_code': order.order_code,
        'customer_name': order.customer_name,
        'product': {
            'id': order.product.id,
            'name': order.product.name_en,
            'code': order.product.code,
        },
        'quantity': order.quantity,
        'priority': order.priority,
        'status': order.status,
    })

@login_required
@csrf_exempt
def api_get_transfer(request, transfer_id):
    """API endpoint to get transfer details."""
    transfer = get_object_or_404(InventoryMovement, id=transfer_id, movement_type='transfer')
    
    return JsonResponse({
        'id': transfer.id,
        'tracking_number': transfer.tracking_number,
        'quantity': transfer.quantity,
        'product': {
            'id': transfer.product.id,
            'name': transfer.product.name_en,
            'code': transfer.product.code,
        },
        'from_warehouse': {
            'id': transfer.from_warehouse.id,
            'name': transfer.from_warehouse.name,
        },
        'to_warehouse': {
            'id': transfer.to_warehouse.id,
            'name': transfer.to_warehouse.name,
        },
        'reason': transfer.reason,
        'notes': transfer.notes,
    })

@login_required
@csrf_exempt
def api_receive_stock(request):
    """API endpoint to process stock receiving."""
    if request.method == 'POST':
        data = json.loads(request.body)
        movement_id = data.get('movement_id')
        received_quantity = data.get('received_quantity')
        condition = data.get('condition', 'good')
        location = data.get('location', '')
        notes = data.get('notes', '')
        
        try:
            movement = InventoryMovement.objects.get(id=movement_id)
            product = movement.product
            warehouse = movement.to_warehouse
            
            # Update movement status
            movement.status = 'completed'
            movement.processed_by = request.user
            movement.processed_at = timezone.now()
            movement.condition = condition
            movement.notes = notes
            movement.save()
            
            # Update inventory
            inventory, created = InventoryRecord.objects.get_or_create(
                product=product,
                warehouse=warehouse,
                defaults={'quantity': 0}
            )
            inventory.quantity += received_quantity
            # Note: location is a ForeignKey, not a CharField
            # If location is needed, it should be handled through WarehouseLocation model
            inventory.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Successfully received {received_quantity} units of {product.name_en}'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

@login_required
@csrf_exempt
def api_pick_order(request):
    """API endpoint to process order picking."""
    if request.method == 'POST':
        data = json.loads(request.body)
        order_id = data.get('order_id')
        picked_quantity = data.get('picked_quantity')
        pick_location = data.get('pick_location', '')
        condition = data.get('condition', 'good')
        notes = data.get('notes', '')
        
        try:
            order = Order.objects.get(id=order_id)
            product = order.product
            
            # Get warehouse (assuming first active warehouse for now)
            warehouse = Warehouse.objects.filter(is_active=True).first()
            
            # Check if enough stock
            inventory = InventoryRecord.objects.filter(
                product=product,
                warehouse=warehouse
            ).first()
            
            if not inventory or inventory.quantity < picked_quantity:
                return JsonResponse({
                    'success': False,
                    'message': 'Insufficient stock for picking'
                })
            
            # Create movement record
            movement = InventoryMovement.objects.create(
                movement_type='stock_out',
                product=product,
                quantity=picked_quantity,
                from_warehouse=warehouse,
                created_by=request.user,
                processed_by=request.user,
                status='completed',
                reference_number=order.order_code,
                reference_type='Order',
                reason='Order fulfillment',
                notes=notes
            )
            
            # Update inventory
            inventory.quantity -= picked_quantity
            inventory.save()
            
            # Update order status
            order.status = 'shipped'
            order.save()
            
            # Generate shipping label
            shipping_label = {
                'order_code': order.order_code,
                'customer_name': order.customer_name or 'N/A',
                'address': order.shipping_address or 'N/A',
                'tracking_number': movement.tracking_number,
                'barcode': movement.tracking_number,
            }
            
            return JsonResponse({
                'success': True,
                'message': f'Successfully picked {picked_quantity} units for order {order.order_code}',
                'shipping_label': shipping_label
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

@login_required
@csrf_exempt
def api_complete_transfer(request):
    """API endpoint to complete transfer."""
    if request.method == 'POST':
        data = json.loads(request.body)
        transfer_id = data.get('transfer_id')
        transferred_quantity = data.get('transferred_quantity')
        from_location = data.get('from_location', '')
        to_location = data.get('to_location', '')
        packaging_type = data.get('packaging_type', '')
        notes = data.get('notes', '')
        
        try:
            transfer = InventoryMovement.objects.get(id=transfer_id, movement_type='transfer')
            
            # Update transfer status
            transfer.status = 'completed'
            transfer.processed_by = request.user
            transfer.processed_at = timezone.now()
            transfer.notes = notes
            transfer.save()
            
            # Update source inventory
            from_inventory = InventoryRecord.objects.filter(
                product=transfer.product,
                warehouse=transfer.from_warehouse
            ).first()
            
            if from_inventory:
                from_inventory.quantity -= transferred_quantity
                from_inventory.save()
            
            # Update destination inventory
            to_inventory, created = InventoryRecord.objects.get_or_create(
                product=transfer.product,
                warehouse=transfer.to_warehouse,
                defaults={'quantity': 0}
            )
            to_inventory.quantity += transferred_quantity
            if to_location:
                to_inventory.location_code = to_location
            to_inventory.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Successfully transferred {transferred_quantity} units from {transfer.from_warehouse.name} to {transfer.to_warehouse.name}'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

@csrf_exempt
def api_warehouse_products(request, warehouse_id):
    """API endpoint to get products for a specific warehouse."""
    if request.method == 'GET':
        try:
            warehouse = Warehouse.objects.get(id=warehouse_id, is_active=True)
            inventory = InventoryRecord.objects.filter(
                warehouse=warehouse
            ).select_related('product')
            
            products = []
            for inv in inventory:
                products.append({
                    'id': inv.product.id,
                    'name_en': inv.product.name_en,
                    'name_ar': inv.product.name_ar,
                    'code': inv.product.code,
                    'quantity': inv.quantity,
                    'location_code': inv.location.zone if inv.location else '',
                })
            
            return JsonResponse({
                'success': True,
                'products': products
            })
        except Warehouse.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Warehouse not found'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

@login_required
@csrf_exempt
def api_product_warehouse_details(request, product_id, warehouse_id):
    """API endpoint to get product details for a specific warehouse."""
    if request.method == 'GET':
        try:
            product = Product.objects.get(id=product_id)
            warehouse = Warehouse.objects.get(id=warehouse_id, is_active=True)
            inventory = InventoryRecord.objects.get(
                product=product,
                warehouse=warehouse
            )
            
            return JsonResponse({
                'success': True,
                'product': {
                    'id': product.id,
                    'name_en': product.name_en,
                    'name_ar': product.name_ar,
                    'code': product.code,
                },
                'inventory': {
                    'quantity': inventory.quantity,
                    'location_code': inventory.location.zone if inventory.location else '',
                    'min_stock_level': 10,  # Default value
                    'max_stock_level': 100,  # Default value
                }
            })
        except (Product.DoesNotExist, Warehouse.DoesNotExist, InventoryRecord.DoesNotExist):
            return JsonResponse({
                'success': False,
                'message': 'Product or warehouse not found'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

@login_required
@user_passes_test(is_stock_keeper)
def accept_product(request, product_id):
    """Accept a product from seller and add to inventory."""
    if request.method == 'POST':
        try:
            with transaction.atomic():
                product = get_object_or_404(Product, id=product_id)
                
                # Get the first active warehouse
                warehouse = Warehouse.objects.filter(is_active=True).first()
                if not warehouse:
                    messages.error(request, 'No active warehouse found.')
                    return redirect('stock_keeper:dashboard')
                
                # Create inventory movement
                movement = InventoryMovement.objects.create(
                    movement_type='stock_in',
                    status='completed',
                    product=product,
                    quantity=1,  # Default quantity, can be adjusted
                    to_warehouse=warehouse,
                    reference_number=f'PROD-{product.id}',
                    reference_type='Product Acceptance',
                    created_by=request.user,
                    processed_by=request.user,
                    processed_at=timezone.now(),
                    notes=f'Product accepted from seller: {product.seller.email if product.seller else "Unknown"}'
                )
                
                # Update or create inventory record
                inventory_record, created = InventoryRecord.objects.get_or_create(
                    product=product,
                    warehouse=warehouse,
                    defaults={
                        'quantity': 1,
                        'last_updated': timezone.now()
                    }
                )
                
                if not created:
                    inventory_record.quantity += 1
                    inventory_record.last_updated = timezone.now()
                    inventory_record.save()
                
                messages.success(request, f'Product "{product.name_en}" has been accepted and added to inventory.')
                
        except Exception as e:
            messages.error(request, f'Error accepting product: {str(e)}')
    
    return redirect('stock_keeper:product_acceptance')

@login_required
@user_passes_test(is_stock_keeper)
def product_acceptance(request):
    """Display inventory management - all products in inventory."""
    # Get all inventory records with related data
    inventory_records = InventoryRecord.objects.select_related(
        'product', 'warehouse', 'location', 'product__seller'
    ).order_by('-last_updated')
    
    # Apply search filter
    search_query = request.GET.get('search', '')
    if search_query:
        inventory_records = inventory_records.filter(
            Q(product__name_en__icontains=search_query) |
            Q(product__name_ar__icontains=search_query) |
            Q(product__code__icontains=search_query)
        )
    
    # Apply warehouse filter
    warehouse_filter = request.GET.get('warehouse', '')
    if warehouse_filter:
        inventory_records = inventory_records.filter(warehouse_id=warehouse_filter)
    
    # Apply status filter
    status_filter = request.GET.get('status', '')
    if status_filter == 'in_stock':
        inventory_records = inventory_records.filter(quantity__gt=0)
    elif status_filter == 'out_of_stock':
        inventory_records = inventory_records.filter(quantity=0)
    elif status_filter == 'low_stock':
        inventory_records = inventory_records.filter(quantity__lte=10, quantity__gt=0)
    
    # Apply date filter (Select Period)
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    if date_from:
        inventory_records = inventory_records.filter(last_updated__date__gte=date_from)
    if date_to:
        inventory_records = inventory_records.filter(last_updated__date__lte=date_to)
    
    # Pagination
    paginator = Paginator(inventory_records, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get all warehouses for filter
    warehouses = Warehouse.objects.filter(is_active=True)
    
    # Get all products for add modal
    products = Product.objects.all().order_by('name_en')[:100]  # Limit to 100 for performance
    
    # Handle stock report export
    if request.GET.get('export') == 'stock_report':
        return export_stock_report(request)
    
    context = {
        'inventory_records': page_obj,
        'warehouses': warehouses,
        'products': products,
        'search_query': search_query,
        'warehouse_filter': warehouse_filter,
        'status_filter': status_filter,
        'date_from': date_from,
        'date_to': date_to,
    }
    
    return render(request, 'stock_keeper/product_acceptance.html', context)

@login_required
def export_stock_report(request):
    """Export stock report (low stock, out of stock, near expiry) - RESTRICTED TO SUPER ADMIN ONLY."""
    from django.http import HttpResponse
    import csv
    from datetime import timedelta
    from users.models import AuditLog

    # SECURITY: Restrict data export to Super Admin only (P0 CRITICAL requirement)
    if not request.user.is_superuser:
        from utils.views import permission_denied_authenticated
        AuditLog.objects.create(
            user=request.user,
            action='unauthorized_export_attempt',
            entity_type='stock_report',
            description=f"Unauthorized attempt to export stock report by {request.user.email}",
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        return permission_denied_authenticated(
            request,
            message="Data export is restricted to Super Admin only for security compliance."
        )
    
    warehouse_filter = request.GET.get('warehouse', '')
    inventory_records = InventoryRecord.objects.select_related('product', 'warehouse', 'location')
    
    if warehouse_filter:
        inventory_records = inventory_records.filter(warehouse_id=warehouse_filter)
    
    # Filter for low stock, out of stock, and near expiry
    low_stock = inventory_records.filter(quantity__lte=10, quantity__gt=0)
    out_of_stock = inventory_records.filter(quantity=0)
    near_expiry = inventory_records.filter(
        expiry_date__lte=timezone.now() + timedelta(days=30),
        quantity__gt=0
    ) if hasattr(InventoryRecord, 'expiry_date') else inventory_records.none()
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="stock_report.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Stock Report', timezone.now().strftime('%Y-%m-%d %H:%M:%S')])
    writer.writerow([])
    
    # Out of Stock
    writer.writerow(['OUT OF STOCK'])
    writer.writerow(['Product ID', 'Product Name', 'SKU', 'Warehouse', 'Location', 'Quantity'])
    for record in out_of_stock:
        writer.writerow([
            f'P{record.product.id:03d}',
            record.product.name_en,
            record.product.code or 'N/A',
            record.warehouse.name,
            record.location.zone if record.location else 'N/A',
            record.quantity
        ])
    
    writer.writerow([])
    # Low Stock
    writer.writerow(['LOW STOCK (≤10)'])
    writer.writerow(['Product ID', 'Product Name', 'SKU', 'Warehouse', 'Location', 'Quantity'])
    for record in low_stock:
        writer.writerow([
            f'P{record.product.id:03d}',
            record.product.name_en,
            record.product.code or 'N/A',
            record.warehouse.name,
            record.location.zone if record.location else 'N/A',
            record.quantity
        ])
    
    if near_expiry.exists():
        writer.writerow([])
        # Near Expiry
        writer.writerow(['NEAR EXPIRY (≤30 days)'])
        writer.writerow(['Product ID', 'Product Name', 'SKU', 'Warehouse', 'Expiry Date', 'Quantity'])
        for record in near_expiry:
            writer.writerow([
                f'P{record.product.id:03d}',
                record.product.name_en,
                record.product.code or 'N/A',
                record.warehouse.name,
                record.expiry_date.strftime('%Y-%m-%d') if record.expiry_date else 'N/A',
                record.quantity
            ])

    # Audit log for successful export (P0 CRITICAL security requirement)
    total_records = low_stock.count() + out_of_stock.count() + near_expiry.count()
    AuditLog.objects.create(
        user=request.user,
        action='data_export',
        entity_type='stock_report',
        description=f"Exported stock report with {total_records} alert records to CSV",
        ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT', '')
    )

    return response

@login_required
@user_passes_test(is_stock_keeper)
def view_inventory_record(request, record_id):
    """View inventory record details."""
    record = get_object_or_404(InventoryRecord, id=record_id)
    
    # Get movement history for this record
    movements = InventoryMovement.objects.filter(
        Q(product=record.product, to_warehouse=record.warehouse) |
        Q(product=record.product, from_warehouse=record.warehouse)
    ).order_by('-created_at')[:10]
    
    # If AJAX request, return HTML snippet
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        from django.template.loader import render_to_string
        html = render_to_string('stock_keeper/inventory_record_detail.html', {
            'record': record,
            'movements': movements,
        }, request=request)
        return JsonResponse({'success': True, 'html': html})
    
    context = {
        'record': record,
        'movements': movements,
    }
    
    return render(request, 'stock_keeper/inventory_record_detail.html', context)

@login_required
@user_passes_test(is_stock_keeper)
def edit_inventory_record(request, record_id):
    """Edit inventory record quantity."""
    record = get_object_or_404(InventoryRecord, id=record_id)
    
    if request.method == 'POST':
        try:
            new_quantity = int(request.POST.get('quantity', 0))
            location_id = request.POST.get('location_id', '')
            notes = request.POST.get('notes', '')
            
            old_quantity = record.quantity
            quantity_change = new_quantity - old_quantity
            
            # Update inventory record
            record.quantity = new_quantity
            if location_id:
                try:
                    location = WarehouseLocation.objects.get(id=location_id)
                    record.location = location
                except WarehouseLocation.DoesNotExist:
                    pass
            record.save()
            
            # Create movement record
            if quantity_change != 0:
                movement_type = 'stock_in' if quantity_change > 0 else 'stock_out'
                InventoryMovement.objects.create(
                    movement_type=movement_type,
                    product=record.product,
                    quantity=abs(quantity_change),
                    to_warehouse=record.warehouse if quantity_change > 0 else None,
                    from_warehouse=record.warehouse if quantity_change < 0 else None,
                    status='completed',
                    created_by=request.user,
                    processed_by=request.user,
                    notes=notes or f'Inventory adjustment: {old_quantity} → {new_quantity}',
                    reason='Manual adjustment'
                )
            
            messages.success(request, f'Inventory record updated successfully.')
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': 'Inventory updated successfully',
                    'quantity': record.quantity
                })
            
            return redirect('stock_keeper:product_acceptance')
            
        except ValueError:
            messages.error(request, 'Invalid quantity value.')
        except Exception as e:
            messages.error(request, f'Error updating inventory: {str(e)}')
    
    # GET request - return JSON for AJAX
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        locations = WarehouseLocation.objects.filter(warehouse=record.warehouse)
        return JsonResponse({
            'success': True,
            'record': {
                'id': record.id,
                'product_name': record.product.name_en,
                'quantity': record.quantity,
                'location_id': record.location.id if record.location else None,
                'warehouse_name': record.warehouse.name,
            },
            'locations': [{'id': loc.id, 'name': f"{loc.zone}-{loc.shelf}"} for loc in locations]
        })
    
    locations = WarehouseLocation.objects.filter(warehouse=record.warehouse)
    context = {
        'record': record,
        'locations': locations,
    }
    return render(request, 'stock_keeper/edit_inventory_record.html', context)

@login_required
@user_passes_test(is_stock_keeper)
@require_POST
def delete_inventory_record(request, record_id):
    """Delete inventory record."""
    record = get_object_or_404(InventoryRecord, id=record_id)
    product_name = record.product.name_en
    
    try:
        # Create movement record for deletion
        InventoryMovement.objects.create(
            movement_type='adjustment',
            product=record.product,
            quantity=record.quantity,
            from_warehouse=record.warehouse,
            status='completed',
            created_by=request.user,
            processed_by=request.user,
            notes=f'Inventory record deleted',
            reason='Record deletion'
        )
        
        record.delete()
        messages.success(request, f'Inventory record for "{product_name}" has been deleted.')
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': 'Inventory record deleted successfully'
            })
        
    except Exception as e:
        messages.error(request, f'Error deleting inventory record: {str(e)}')
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'message': str(e)
            })
    
    return redirect('stock_keeper:product_acceptance')

@login_required
@user_passes_test(is_stock_keeper)
def add_inventory_record(request):
    """Add new inventory record."""
    if request.method == 'POST':
        try:
            product_id = request.POST.get('product_id')
            warehouse_id = request.POST.get('warehouse_id')
            quantity = int(request.POST.get('quantity', 0))
            location_id = request.POST.get('location_id', '')
            
            product = get_object_or_404(Product, id=product_id)
            warehouse = get_object_or_404(Warehouse, id=warehouse_id)
            
            # Check if record already exists
            existing_record = InventoryRecord.objects.filter(
                product=product,
                warehouse=warehouse
            ).first()
            
            if existing_record:
                existing_record.quantity += quantity
                existing_record.save()
                record = existing_record
            else:
                # Create new inventory record
                record = InventoryRecord.objects.create(
                    product=product,
                    warehouse=warehouse,
                    quantity=quantity
                )
                if location_id:
                    try:
                        location = WarehouseLocation.objects.get(id=location_id)
                        record.location = location
                        record.save()
                    except WarehouseLocation.DoesNotExist:
                        pass
            
            # Create movement record
            InventoryMovement.objects.create(
                movement_type='stock_in',
                product=product,
                quantity=quantity,
                to_warehouse=warehouse,
                status='completed',
                created_by=request.user,
                processed_by=request.user,
                notes=f'New inventory record created',
                reason='Manual addition'
            )
            
            messages.success(request, f'Inventory record added successfully.')
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': 'Inventory record added successfully'
                })
            
            return redirect('stock_keeper:product_acceptance')
            
        except ValueError:
            messages.error(request, 'Invalid quantity value.')
        except Exception as e:
            messages.error(request, f'Error adding inventory record: {str(e)}')
    
    # GET request
    products = Product.objects.all().order_by('name_en')
    warehouses = Warehouse.objects.filter(is_active=True)
    
    context = {
        'products': products,
        'warehouses': warehouses,
    }
    
    return render(request, 'stock_keeper/add_inventory_record.html', context)
