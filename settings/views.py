from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Country, DeliveryCompany, SystemSetting
from users.models import User
from roles.models import Role
import json

def is_admin(user):
    return user.is_staff or user.has_perm('settings.change_systemsetting')

@login_required
def settings_dashboard(request):
    """Main settings dashboard with overview of all settings sections"""
    context = {
        'total_countries': Country.objects.count(),
        'total_delivery_companies': DeliveryCompany.objects.count(),
        'total_users': User.objects.count(),
        'total_roles': Role.objects.count(),
    }
    return render(request, 'settings/dashboard.html', context)

@login_required
@user_passes_test(is_admin)
def countries_management(request):
    """Manage countries with CRUD operations"""
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'add':
            name_en = request.POST.get('name_en')
            name_ar = request.POST.get('name_ar')
            code = request.POST.get('code')
            currency = request.POST.get('currency')
            timezone = request.POST.get('timezone')
            
            try:
                Country.objects.create(
                    name_en=name_en,
                    name_ar=name_ar,
                    code=code,
                    currency=currency,
                    timezone=timezone
                )
                messages.success(request, 'Country added successfully!')
            except Exception as e:
                messages.error(request, f'Error adding country: {str(e)}')
                
        elif action == 'delete':
            country_id = request.POST.get('country_id')
            try:
                country = Country.objects.get(id=country_id)
                country.delete()
                messages.success(request, 'Country deleted successfully!')
            except Country.DoesNotExist:
                messages.error(request, 'Country not found!')
    
    # Get countries with search and pagination
    search_query = request.GET.get('search', '')
    countries = Country.objects.all()
    
    if search_query:
        countries = countries.filter(
            Q(name_en__icontains=search_query) |
            Q(name_ar__icontains=search_query) |
            Q(code__icontains=search_query)
        )
    
    paginator = Paginator(countries, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
    }
    return render(request, 'settings/countries.html', context)

@login_required
@user_passes_test(is_admin)
def delivery_companies_management(request):
    """Manage delivery companies with CRUD operations"""
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'add':
            name_en = request.POST.get('name_en')
            name_ar = request.POST.get('name_ar')
            code = request.POST.get('code')
            base_cost = request.POST.get('base_cost')
            api_key = request.POST.get('api_key', '')
            
            try:
                company = DeliveryCompany.objects.create(
                    name_en=name_en,
                    name_ar=name_ar,
                    code=code,
                    base_cost=base_cost,
                    api_key=api_key
                )
                
                # Add countries
                countries = request.POST.getlist('countries')
                for country_id in countries:
                    country = Country.objects.get(id=country_id)
                    company.countries.add(country)
                
                messages.success(request, 'Delivery company added successfully!')
            except Exception as e:
                messages.error(request, f'Error adding delivery company: {str(e)}')
                
        elif action == 'delete':
            company_id = request.POST.get('company_id')
            try:
                company = DeliveryCompany.objects.get(id=company_id)
                company.delete()
                messages.success(request, 'Delivery company deleted successfully!')
            except DeliveryCompany.DoesNotExist:
                messages.error(request, 'Delivery company not found!')
    
    # Get delivery companies with search and pagination
    search_query = request.GET.get('search', '')
    companies = DeliveryCompany.objects.all()
    
    if search_query:
        companies = companies.filter(
            Q(name_en__icontains=search_query) |
            Q(name_ar__icontains=search_query) |
            Q(code__icontains=search_query)
        )
    
    paginator = Paginator(companies, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'countries': Country.objects.filter(is_active=True),
    }
    return render(request, 'settings/delivery_companies.html', context)


@login_required
@user_passes_test(is_admin)
def fees_management(request):
    """Manage system-wide fees"""
    if request.method == 'POST':
        try:
            # Get fee values from form
            fees = {
                'upsell_fee': request.POST.get('upsell_fee', '0'),
                'confirmation_fee': request.POST.get('confirmation_fee', '0'),
                'cancellation_fee': request.POST.get('cancellation_fee', '0'),
                'fulfillment_fee': request.POST.get('fulfillment_fee', '0'),
                'shipping_fee': request.POST.get('shipping_fee', '0'),
                'return_fee': request.POST.get('return_fee', '0'),
                'warehouse_fee': request.POST.get('warehouse_fee', '0'),
            }
            
            # Save each fee to SystemSetting
            for key, value in fees.items():
                setting, created = SystemSetting.objects.get_or_create(
                    key=key,
                    defaults={'description': f'Default {key.replace("_", " ").title()}'}
                )
                setting.value = value
                setting.save()
            
            messages.success(request, 'Fees updated successfully!')
        except Exception as e:
            messages.error(request, f'Error updating fees: {str(e)}')
    
    # Get current fee values
    fee_settings = {}
    for key in ['upsell_fee', 'confirmation_fee', 'cancellation_fee', 'fulfillment_fee', 'shipping_fee', 'return_fee', 'warehouse_fee']:
        try:
            setting = SystemSetting.objects.get(key=key)
            fee_settings[key] = setting.value
        except SystemSetting.DoesNotExist:
            fee_settings[key] = '0'
    
    context = {
        'fees': fee_settings,
    }
    return render(request, 'settings/fees.html', context)

@login_required
def delete_own_account(request):
    """Allow users to delete their own account (except sellers)."""
    if request.method == 'POST':
        try:
            # Prevent sellers from deleting their own account
            if request.user.has_role('Seller'):
                return JsonResponse({
                    'success': False,
                    'message': 'Sellers cannot delete their own accounts. Please contact support for account management.'
                })
            
            # Prevent superusers from deleting their own account
            if request.user.is_superuser:
                return JsonResponse({
                    'success': False,
                    'message': 'Superusers cannot delete their own accounts.'
                })
            
            # Log the deletion attempt
            from users.models import AuditLog
            AuditLog.objects.create(
                user=request.user,
                action='self_delete_account',
                entity_type='user',
                entity_id=str(request.user.id),
                description=f"User attempted to delete their own account: {request.user.email}",
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            # Delete the user account
            user_email = request.user.email
            request.user.delete()
            
            return JsonResponse({
                'success': True,
                'message': 'Your account has been deleted successfully.',
                'redirect_url': '/'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error deleting account: {str(e)}'
            })
    
    return JsonResponse({
        'success': False,
        'message': 'Invalid request method.'
    })


@login_required
@user_passes_test(is_admin)
def audit_logs(request):
    """View audit logs for privileged actions."""
    from users.models import AuditLog

    # Get filter parameters
    user_filter = request.GET.get('user', '')
    action_filter = request.GET.get('action', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')

    # Base queryset
    logs = AuditLog.objects.all().select_related('user').order_by('-timestamp')

    # Apply filters
    if user_filter:
        logs = logs.filter(
            Q(user__email__icontains=user_filter) |
            Q(user__first_name__icontains=user_filter) |
            Q(user__last_name__icontains=user_filter)
        )

    if action_filter:
        logs = logs.filter(action__icontains=action_filter)

    if date_from:
        logs = logs.filter(timestamp__date__gte=date_from)

    if date_to:
        logs = logs.filter(timestamp__date__lte=date_to)

    # Pagination
    paginator = Paginator(logs, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Get distinct action types for filter dropdown
    action_types = AuditLog.objects.values_list('action', flat=True).distinct()

    context = {
        'page_obj': page_obj,
        'user_filter': user_filter,
        'action_filter': action_filter,
        'date_from': date_from,
        'date_to': date_to,
        'action_types': action_types,
    }

    return render(request, 'settings/audit_logs.html', context)