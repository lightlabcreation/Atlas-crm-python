from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views import View
import json
from .models import User, AuditLog, LoginAttempt

@csrf_exempt
@require_http_methods(["POST"])
def api_login(request):
    """API endpoint for user login."""
    try:
        data = json.loads(request.body)
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return JsonResponse({
                'error': 'Email and password are required'
            }, status=400)
        
        user = authenticate(request, email=email, password=password)
        
        if user is None:
            return JsonResponse({
                'error': 'Invalid email or password'
            }, status=401)
        
        if user.approval_status == 'pending':
            return JsonResponse({
                'error': 'Your account is pending approval. Please wait for admin approval.'
            }, status=403)
        
        if user.approval_status == 'rejected':
            return JsonResponse({
                'error': 'Your registration request has been rejected. Please contact the administration.'
            }, status=403)
        
        if not user.is_active:
            return JsonResponse({
                'error': 'Your account is not active. Please contact the administration.'
            }, status=403)
        
        if not user.email_verified and not user.is_superuser:
            return JsonResponse({
                'error': 'Please verify your email address before logging in.'
            }, status=403)
        
        # Check if user has 2FA enabled
        try:
            if hasattr(user, 'twofa_profile') and user.twofa_profile.is_enabled:
                # Store user ID in session for 2FA verification
                request.session['2fa_user_id'] = user.id
                request.session['2fa_verified'] = False
                
                # Log the login attempt
                LoginAttempt.objects.create(
                    user=user,
                    ip_address=request.META.get('REMOTE_ADDR'),
                    user_agent=request.META.get('HTTP_USER_AGENT', ''),
                    success=False,
                    failure_reason='Pending 2FA verification'
                )
                
                return JsonResponse({
                    'error': 'Two-factor authentication required',
                    'requires_2fa': True,
                    'user_id': user.id
                }, status=200)
        except:
            pass
        
        # Proceed with normal login
        login(request, user)
        
        # Create audit log for login
        AuditLog.objects.create(
            user=user,
            action='login',
            entity_type='user',
            entity_id=str(user.id),
            description=f"User login: {user.email}",
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        # Log successful login attempt
        LoginAttempt.objects.create(
            user=user,
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            success=True
        )
        
        # Return user data
        user_data = {
            'id': user.id,
            'email': user.email,
            'full_name': user.get_full_name(),
            'role': user.primary_role.name if user.primary_role else None,
            'is_superuser': user.is_superuser,
            'is_active': user.is_active,
            'email_verified': user.email_verified,
            'approval_status': user.approval_status,
            'date_joined': user.date_joined.isoformat(),
            'last_login': user.last_login.isoformat() if user.last_login else None,
        }
        
        return JsonResponse({
            'success': True,
            'message': f"Welcome {user.get_full_name()}! Login successful.",
            'user': user_data
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'error': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'error': f'Login failed: {str(e)}'
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def api_logout(request):
    """API endpoint for user logout."""
    try:
        from django.contrib.auth import logout
        logout(request)
        
        return JsonResponse({
            'success': True,
            'message': 'Logout successful'
        })
    except Exception as e:
        return JsonResponse({
            'error': f'Logout failed: {str(e)}'
        }, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def api_profile(request):
    """API endpoint to get current user profile."""
    try:
        # Check if user is authenticated
        if not request.user.is_authenticated:
            return JsonResponse({
                'error': 'Authentication required'
            }, status=401)
        
        user = request.user
        user_data = {
            'id': user.id,
            'email': user.email,
            'full_name': user.get_full_name(),
            'role': user.primary_role.name if user.primary_role else None,
            'is_superuser': user.is_superuser,
            'is_active': user.is_active,
            'email_verified': user.email_verified,
            'approval_status': user.approval_status,
            'date_joined': user.date_joined.isoformat(),
            'last_login': user.last_login.isoformat() if user.last_login else None,
        }
        
        return JsonResponse({
            'success': True,
            'user': user_data
        })
    except Exception as e:
        return JsonResponse({
            'error': f'Failed to get profile: {str(e)}'
        }, status=500)
