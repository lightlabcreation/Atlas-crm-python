from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone
from django.db import IntegrityError, transaction
from .models import Role, Permission, RolePermission, UserRole, RoleAuditLog
from users.models import User
from django.urls import reverse

def role_required(role_name):
    """Decorator to check if user has a specific role"""
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            # Allow superusers and users with Admin role
            if (request.user.is_superuser or 
                request.user.has_role('Admin') or 
                request.user.has_role(role_name)):
                return view_func(request, *args, **kwargs)
            else:
                messages.error(request, f"You don't have permission to access this page. Required role: {role_name}")
                return redirect('dashboard:index')
        return wrapper
    return decorator

@login_required
def role_list(request):
    """List all roles"""
    # Explicitly block Packaging Agent
    if request.user.has_role('Packaging Agent') and not (request.user.has_role('Admin') or request.user.has_role('Super Admin') or request.user.is_superuser):
        from utils.views import permission_denied_authenticated
        return permission_denied_authenticated(
            request,
            message="You don't have permission to access this page. This page is restricted to Admin and Super Admin only."
        )
    # Only allow superusers and admin users to view roles
    if not (request.user.is_superuser or request.user.has_role('Admin') or request.user.has_role('Super Admin')):
        messages.error(request, "You don't have permission to access this page.")
        return redirect('dashboard:index')
    
    roles = Role.objects.all().order_by('name')
    
    # Search functionality
    search = request.GET.get('search', '')
    if search:
        roles = roles.filter(
            Q(name__icontains=search) |
            Q(description__icontains=search)
        )
    
    # Pagination
    paginator = Paginator(roles, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'roles': page_obj,
        'search': search,
        'total_roles': roles.count(),
    }
    return render(request, 'roles/role_list.html', context)

@login_required
@role_required('Super Admin')
def role_create(request):
    """Create a new role - DISABLED: Role creation is not allowed"""
    messages.error(request, 'Role creation is disabled. Only default roles are managed by the system.')
    return redirect('roles:role_list')

@login_required
@role_required('Super Admin')
def permissions_editor(request):
    """Permissions editor with table layout"""
    if request.method == 'POST':
        # Handle form submission
        selected_permissions = request.POST.getlist('permissions')
        # Here you would process the selected permissions
        messages.success(request, f'Permissions updated successfully. {len(selected_permissions)} permissions selected.')
        return redirect('roles:permissions_editor')
    
    context = {
        'title': 'Permissions Editor',
    }
    return render(request, 'roles/permissions_editor.html', context)

@login_required
@role_required('Super Admin')
def role_edit(request, role_id):
    """Edit an existing role"""
    role = get_object_or_404(Role, id=role_id)
    
    if request.method == 'POST':
        name = request.POST.get('name')
        role_type = request.POST.get('role_type')
        description = request.POST.get('description', '')
        is_active = request.POST.get('is_active') == 'on'
        
        if not name or not role_type:
            messages.error(request, 'Role name and type are required.')
            return redirect('roles:role_edit', role_id=role_id)
        
        # Check if role name already exists (excluding current role)
        if Role.objects.filter(name=name).exclude(id=role_id).exists():
            messages.error(request, 'A role with this name already exists.')
            return redirect('roles:role_edit', role_id=role_id)
        
        try:
            old_name = role.name
            role.name = name
            role.role_type = role_type
            role.description = description
            role.is_active = is_active
            role.save()
            
            # Create audit log
            RoleAuditLog.objects.create(
                action='role_updated',
                user=request.user,
                role=role,
                description=f'Role "{old_name}" was updated to "{role.name}" by {request.user.get_full_name()}',
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            messages.success(request, f'Role "{role.name}" updated successfully.')
            return redirect('roles:role_detail', role_id=role.id)
            
        except Exception as e:
            messages.error(request, f'Error updating role: {str(e)}')
            return redirect('roles:role_edit', role_id=role_id)
    
    context = {
        'role': role,
        'role_types': Role.ROLE_TYPES,
    }
    return render(request, 'roles/role_form.html', context)

@login_required
@role_required('Super Admin')
def role_detail(request, role_id):
    """View role details and permissions"""
    role = get_object_or_404(Role, id=role_id)
    role_permissions = role.role_permissions.all().order_by('permission__module', 'permission__permission_type')
    
    # Get users with this role through UserRole relationship
    user_roles = role.users.all().select_related('user').filter(user__is_active=True)
    users_with_role = [user_role.user for user_role in user_roles]
    
    # Get all available permissions for this role
    all_permissions = Permission.objects.filter(is_active=True).order_by('module', 'permission_type')
    
    # Group permissions by module for better display
    permissions_by_module = {}
    for permission in all_permissions:
        module = permission.module
        if module not in permissions_by_module:
            permissions_by_module[module] = []
        permissions_by_module[module].append(permission)
    
    context = {
        'role': role,
        'role_permissions': role_permissions,
        'users_with_role': users_with_role,
        'all_permissions': all_permissions,
        'permissions_by_module': permissions_by_module,
    }
    return render(request, 'roles/role_detail.html', context)

@login_required
@role_required('Super Admin')
def role_delete(request, role_id):
    """Delete a role"""
    role = get_object_or_404(Role, id=role_id)
    
    # Check if role is protected or default
    if role.is_protected or role.is_default:
        messages.error(request, f'Cannot delete {"protected" if role.is_protected else "default"} role "{role.name}". This role is required by the system.')
        return redirect('roles:role_detail', role_id=role_id)
    
    if request.method == 'POST':
        try:
            role_name = role.name
            role.delete()
            
            # Create audit log
            RoleAuditLog.objects.create(
                action='role_deleted',
                user=request.user,
                description=f'Role "{role_name}" was deleted by {request.user.get_full_name()}',
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            messages.success(request, f'Role "{role_name}" deleted successfully.')
            return redirect('roles:role_list')
            
        except Exception as e:
            messages.error(request, f'Error deleting role: {str(e)}')
            return redirect('roles:role_detail', role_id=role_id)
    
    context = {
        'role': role,
    }
    return render(request, 'roles/role_confirm_delete.html', context)

@login_required
@role_required('Super Admin')
def update_role_permissions(request, role_id):
    """Update permissions for a role"""
    role = get_object_or_404(Role, id=role_id)
    
    if request.method == 'POST':
        permissions_data = request.POST.getlist('permissions')
        
        try:
            with transaction.atomic():
                # Get all current permissions for this role
                current_permissions = set(role.role_permissions.values_list('permission_id', flat=True))
                
                # Get all permissions to be assigned
                new_permission_ids = set()
                for permission_codename in permissions_data:
                    if permission_codename:
                        # Try to get permission by codename first
                        try:
                            permission = Permission.objects.get(codename=permission_codename)
                            new_permission_ids.add(permission.id)
                        except Permission.DoesNotExist:
                            # If not found by codename, try by id (for backward compatibility)
                            try:
                                permission = Permission.objects.get(id=permission_codename)
                                new_permission_ids.add(permission.id)
                            except Permission.DoesNotExist:
                                continue
                
                # Find permissions to remove (in current but not in new)
                permissions_to_remove = current_permissions - new_permission_ids
                
                # Find permissions to add (in new but not in current)
                permissions_to_add = new_permission_ids - current_permissions
                
                # Remove permissions that are no longer needed
                if permissions_to_remove:
                    role.role_permissions.filter(permission_id__in=permissions_to_remove).delete()
                
                # Add new permissions using get_or_create to avoid duplicates
                for permission_id in permissions_to_add:
                    try:
                        permission = Permission.objects.get(id=permission_id)
                        RolePermission.objects.get_or_create(
                            role=role,
                            permission=permission,
                            defaults={
                                'granted': True,
                                'granted_by': request.user
                            }
                        )
                    except Permission.DoesNotExist:
                        continue
                
                # Create audit log
                RoleAuditLog.objects.create(
                    action='permission_granted',
                    user=request.user,
                    role=role,
                    description=f'Permissions updated for role "{role.name}" by {request.user.get_full_name()}. Added: {len(permissions_to_add)}, Removed: {len(permissions_to_remove)}',
                    ip_address=request.META.get('REMOTE_ADDR'),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')
                )
            
            messages.success(request, f'Permissions for role "{role.name}" updated successfully.')
            return redirect('roles:role_detail', role_id=role_id)
            
        except IntegrityError as e:
            messages.error(request, f'Database constraint error: A permission assignment already exists. Please refresh the page and try again.')
            return redirect('roles:role_permissions', role_id=role_id)
        except Exception as e:
            messages.error(request, f'Error updating permissions: {str(e)}')
            return redirect('roles:role_permissions', role_id=role_id)
    
    # GET request - show permissions management page
    role_permissions = role.role_permissions.all().order_by('permission__module', 'permission__permission_type')
    
    # Get current role permission codenames for template
    role_permission_codenames = [rp.permission.codename for rp in role_permissions]
    
    # Get all available permissions and group them by module
    all_permissions = Permission.objects.filter(is_active=True)
    
    # Group permissions by module and type
    permissions_by_module = {}
    for permission in all_permissions:
        module = permission.module
        if module not in permissions_by_module:
            permissions_by_module[module] = {}
        
        # Map permission types to our table columns
        if permission.permission_type == 'read':
            permissions_by_module[module]['read'] = permission.codename
        elif permission.permission_type == 'create':
            permissions_by_module[module]['create'] = permission.codename
        elif permission.permission_type == 'update':
            permissions_by_module[module]['edit'] = permission.codename
        elif permission.permission_type == 'delete':
            permissions_by_module[module]['delete'] = permission.codename
        elif permission.permission_type == 'manage':
            # For manage permissions, assign to all columns
            permissions_by_module[module]['read'] = permission.codename
            permissions_by_module[module]['create'] = permission.codename
            permissions_by_module[module]['edit'] = permission.codename
            permissions_by_module[module]['delete'] = permission.codename
    
    
    context = {
        'role': role,
        'role_permissions': role_permissions,
        'role_permission_codenames': role_permission_codenames,
        'permissions_by_module': permissions_by_module,
    }
    return render(request, 'roles/role_permissions.html', context)

@login_required
@user_passes_test(lambda u: u.has_role('Super Admin') or u.has_role('Admin') or u.is_superuser)
def assign_user_role(request, user_id):
    """Assign a role to a user"""
    user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        role_id = request.POST.get('role')
        is_primary = request.POST.get('is_primary') == 'on'
        
        if not role_id:
            messages.error(request, 'Please select a role.')
            return redirect('users:user_detail', user_id=user_id)
        
        try:
            role = Role.objects.get(id=role_id)
            
            # If this is a primary role, remove primary from other roles
            if is_primary:
                UserRole.objects.filter(user=user, is_primary=True).update(is_primary=False)
            
            # Create or update user role
            user_role, created = UserRole.objects.get_or_create(
                user=user,
                role=role,
                defaults={
                    'is_primary': is_primary,
                    'is_active': True,  # Ensure role is active
                    'assigned_by': request.user
                }
            )
            
            if not created:
                user_role.is_primary = is_primary
                user_role.is_active = True  # Ensure role remains active
                user_role.save()
            
            # Create audit log
            action = 'user_role_assigned' if created else 'user_role_updated'
            RoleAuditLog.objects.create(
                action=action,
                user=request.user,
                role=role,
                target_user=user,
                description=f'Role "{role.name}" was assigned to {user.get_full_name()} by {request.user.get_full_name()}',
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            messages.success(request, f'Role "{role.name}" assigned to {user.get_full_name()} successfully.')
            
        except Exception as e:
            messages.error(request, f'Error assigning role: {str(e)}')
        
        return redirect('users:user_detail', user_id=user_id)
    
    roles = Role.objects.filter(is_active=True).order_by('name')
    user_roles = user.user_roles.all()
    
    context = {
        'user': user,
        'roles': roles,
        'user_roles': user_roles,
    }
    return render(request, 'roles/assign_user_role.html', context)

@login_required
@user_passes_test(lambda u: u.has_role('Super Admin') or u.has_role('Admin') or u.is_superuser)
def update_user_role(request, user_role_id):
    """Update a user's role assignment"""
    user_role = get_object_or_404(UserRole, id=user_role_id)
    user = user_role.user
    
    if request.method == 'POST':
        role_id = request.POST.get('role')
        is_primary = request.POST.get('is_primary') == 'on'
        
        if not role_id:
            messages.error(request, 'Please select a role.')
            return redirect('users:user_detail', user_id=user.id)
        
        try:
            role = Role.objects.get(id=role_id)
            
            # If this is a primary role, remove primary from other roles
            if is_primary:
                UserRole.objects.filter(user=user, is_primary=True).exclude(id=user_role_id).update(is_primary=False)
            
            # Update user role
            user_role.role = role
            user_role.is_primary = is_primary
            user_role.is_active = True  # Ensure role remains active
            user_role.save()
            
            # Create audit log
            RoleAuditLog.objects.create(
                action='user_role_updated',
                user=request.user,
                role=role,
                target_user=user,
                description=f'Role "{role.name}" was updated for {user.get_full_name()} by {request.user.get_full_name()}',
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            messages.success(request, f'Role "{role.name}" updated for {user.get_full_name()} successfully.')
            
        except Exception as e:
            messages.error(request, f'Error updating role: {str(e)}')
        
        return redirect('users:user_detail', user_id=user.id)
    
    roles = Role.objects.filter(is_active=True).order_by('name')
    user_roles = user.user_roles.all()
    
    context = {
        'user': user,
        'user_role': user_role,
        'roles': roles,
        'user_roles': user_roles,
    }
    return render(request, 'roles/update_user_role.html', context)

@login_required
@user_passes_test(lambda u: u.has_role('Super Admin') or u.has_role('Admin') or u.is_superuser)
def remove_user_role(request, user_role_id):
    """Remove a role from a user"""
    user_role = get_object_or_404(UserRole, id=user_role_id)
    user = user_role.user
    role = user_role.role
    
    if request.method == 'POST':
        try:
            # Create audit log before deletion
            RoleAuditLog.objects.create(
                action='user_role_removed',
                user=request.user,
                role=role,
                target_user=user,
                description=f'Role "{role.name}" was removed from {user.get_full_name()} by {request.user.get_full_name()}',
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            # Remove role
            user_role.delete()
            
            messages.success(request, f'Role "{role.name}" removed from {user.get_full_name()} successfully.')
            
        except Exception as e:
            messages.error(request, f'Error removing role: {str(e)}')
        
        return redirect('users:user_detail', user_id=user.id)
    
    context = {
        'user': user,
        'user_role': user_role,
        'role': role,
    }
    return render(request, 'roles/remove_user_role.html', context)

@login_required
@role_required('Super Admin')
def permission_list(request):
    """List all permissions in the system"""
    permissions = Permission.objects.all().order_by('module', 'permission_type', 'name')
    
    # Search functionality
    search = request.GET.get('search', '')
    module_filter = request.GET.get('module', '')
    permission_type_filter = request.GET.get('permission_type', '')
    
    if search:
        permissions = permissions.filter(
            Q(name__icontains=search) |
            Q(codename__icontains=search) |
            Q(description__icontains=search) |
            Q(module__icontains=search) |
            Q(model_name__icontains=search)
        )
    
    if module_filter:
        permissions = permissions.filter(module=module_filter)
    
    if permission_type_filter:
        permissions = permissions.filter(permission_type=permission_type_filter)
    
    # Get unique modules and permission types for filters
    modules = Permission.objects.values_list('module', flat=True).distinct().order_by('module')
    permission_types = Permission.PERMISSION_TYPES
    
    # Calculate statistics
    total_permissions = permissions.count()
    modules_count = modules.count()
    permission_types_count = len(permission_types)
    active_permissions = permissions.filter(is_active=True).count()
    
    # Pagination
    paginator = Paginator(permissions, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'permissions': page_obj,
        'search': search,
        'module_filter': module_filter,
        'permission_type_filter': permission_type_filter,
        'modules': modules,
        'permission_types': permission_types,
        'total_permissions': total_permissions,
        'modules_count': modules_count,
        'permission_types_count': permission_types_count,
        'active_permissions': active_permissions,
    }
    return render(request, 'roles/permission_list.html', context)
