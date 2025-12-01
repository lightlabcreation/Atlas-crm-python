from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views.generic import View
from django.contrib.auth import get_user_model
from django_otp import devices_for_user
from django_otp.plugins.otp_totp.models import TOTPDevice
from django_otp.util import random_hex
import qrcode
import qrcode.image.svg
from io import BytesIO
import base64
import json
from .models import User2FAProfile, LoginAttempt

User = get_user_model()


@login_required
def setup_2fa(request):
    """Setup 2FA for the current user"""
    user = request.user
    
    # Get or create 2FA profile
    profile, created = User2FAProfile.objects.get_or_create(user=user)
    
    # Get existing TOTP device or create new one
    totp_device = TOTPDevice.objects.filter(user=user).first()
    
    if not totp_device:
        totp_device = TOTPDevice.objects.create(
            user=user,
            name=f"{user.email} - TOTP",
            confirmed=False
        )
    
    # Generate QR code
    qr_code_data = totp_device.config_url
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(qr_code_data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    image_base64 = base64.b64encode(buffer.getvalue()).decode()
    
    context = {
        'totp_device': totp_device,
        'qr_code': image_base64,
        'secret_key': totp_device.key,
        'profile': profile,
    }
    
    return render(request, 'users/setup_2fa.html', context)


@login_required
def verify_2fa_setup(request):
    """Verify 2FA setup with the provided token"""
    if request.method == 'POST':
        token = request.POST.get('token')
        user = request.user
        
        # Get the TOTP device
        totp_device = TOTPDevice.objects.filter(user=user, confirmed=False).first()
        
        if totp_device and totp_device.verify_token(token):
            # Confirm the device
            totp_device.confirmed = True
            totp_device.save()
            
            # Enable 2FA for user
            profile, created = User2FAProfile.objects.get_or_create(user=user)
            profile.is_enabled = True
            profile.generate_backup_codes()
            profile.save()
            
            messages.success(request, '2FA has been successfully enabled!')
            return JsonResponse({'success': True, 'message': '2FA enabled successfully'})
        else:
            return JsonResponse({'success': False, 'message': 'Invalid token. Please try again.'})
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})


@login_required
def disable_2fa(request):
    """Disable 2FA for the current user"""
    if request.method == 'POST':
        user = request.user
        
        # Get 2FA profile
        try:
            profile = user.twofa_profile
            profile.is_enabled = False
            profile.backup_codes = []
            profile.save()
            
            # Delete TOTP devices
            TOTPDevice.objects.filter(user=user).delete()
            
            messages.success(request, '2FA has been disabled successfully!')
            return JsonResponse({'success': True, 'message': '2FA disabled successfully'})
        except User2FAProfile.DoesNotExist:
            return JsonResponse({'success': False, 'message': '2FA is not enabled for this user'})
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})


@login_required
def backup_codes(request):
    """View and regenerate backup codes"""
    user = request.user
    
    try:
        profile = user.twofa_profile
    except User2FAProfile.DoesNotExist:
        messages.error(request, '2FA is not enabled for your account.')
        return redirect('users:profile')
    
    if request.method == 'POST' and 'regenerate' in request.POST:
        # Regenerate backup codes
        new_codes = profile.generate_backup_codes()
        messages.success(request, 'New backup codes have been generated!')
        return redirect('users:backup_codes')
    
    context = {
        'profile': profile,
        'backup_codes': profile.backup_codes,
    }
    
    return render(request, 'users/backup_codes.html', context)


def verify_2fa_login(request):
    """Verify 2FA token during login"""
    if request.method == 'POST':
        token = request.POST.get('token')
        user_id = request.session.get('2fa_user_id')
        
        if not user_id:
            return JsonResponse({'success': False, 'message': 'Session expired'})
        
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'User not found'})
        
        # Check if token is valid
        totp_device = TOTPDevice.objects.filter(user=user, confirmed=True).first()
        
        if totp_device and totp_device.verify_token(token):
            # 2FA verification successful
            request.session['2fa_verified'] = True
            request.session.pop('2fa_user_id', None)
            
            # Log successful login attempt
            LoginAttempt.objects.create(
                user=user,
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                success=True
            )
            
            return JsonResponse({'success': True, 'redirect_url': '/'})
        
        # Check backup codes
        try:
            profile = user.twofa_profile
            if profile.verify_backup_code(token):
                request.session['2fa_verified'] = True
                request.session.pop('2fa_user_id', None)
                
                # Log successful login attempt
                LoginAttempt.objects.create(
                    user=user,
                    ip_address=request.META.get('REMOTE_ADDR'),
                    user_agent=request.META.get('HTTP_USER_AGENT', ''),
                    success=True
                )
                
                return JsonResponse({'success': True, 'redirect_url': '/'})
        except User2FAProfile.DoesNotExist:
            pass
        
        # Log failed attempt
        LoginAttempt.objects.create(
            user=user,
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            success=False,
            failure_reason='Invalid 2FA token'
        )
        
        return JsonResponse({'success': False, 'message': 'Invalid token. Please try again.'})
    
    return render(request, 'users/verify_2fa_login.html')


@login_required
def security_logs(request):
    """View security logs for the current user"""
    user = request.user
    
    # Get recent login attempts
    login_attempts = LoginAttempt.objects.filter(user=user)[:20]
    
    context = {
        'login_attempts': login_attempts,
    }
    
    return render(request, 'users/security_logs.html', context)


@login_required
def get_2fa_status(request):
    """Get 2FA status for the current user"""
    user = request.user
    
    try:
        profile = user.twofa_profile
        return JsonResponse({
            'enabled': profile.is_enabled,
            'has_backup_codes': profile.has_backup_codes(),
            'backup_codes_count': len(profile.backup_codes)
        })
    except User2FAProfile.DoesNotExist:
        return JsonResponse({
            'enabled': False,
            'has_backup_codes': False,
            'backup_codes_count': 0
        })



















































