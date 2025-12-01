from django.shortcuts import redirect
from django.urls import reverse
from django.contrib.auth import logout
from django.contrib import messages
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class TwoFactorAuthMiddleware(MiddlewareMixin):
    """
    Middleware to enforce 2FA verification for authenticated users
    """
    
    def process_request(self, request):
        # Skip 2FA check for certain paths
        skip_paths = [
            '/users/logout/',
            '/users/2fa/verify-login/',
            '/admin/logout/',
            '/static/',
            '/media/',
        ]
        
        # Skip if path should be ignored
        if any(request.path.startswith(path) for path in skip_paths):
            return None
        
        # Skip for anonymous users
        if not request.user.is_authenticated:
            return None
        
        # Skip if user doesn't have 2FA enabled
        try:
            if not hasattr(request.user, 'twofa_profile') or not request.user.twofa_profile.is_enabled:
                return None
        except:
            return None
        
        # Skip if 2FA is already verified in this session
        if request.session.get('2fa_verified', False):
            return None
        
        # Skip for API endpoints (if needed)
        if request.path.startswith('/api/'):
            return None
        
        # Redirect to 2FA verification page
        if request.path != '/users/2fa/verify-login/':
            # Store the original URL to redirect back after 2FA verification
            request.session['2fa_redirect_url'] = request.get_full_path()
            return redirect('/users/2fa/verify-login/')
        
        return None


class LoginAttemptMiddleware(MiddlewareMixin):
    """
    Middleware to track login attempts
    """
    
    def process_request(self, request):
        # Only track login attempts
        if request.path == '/users/login/' and request.method == 'POST':
            # This will be handled in the login view
            pass
        return None
    
    def process_response(self, request, response):
        # Log successful logins
        if (request.path == '/users/login/' and 
            request.method == 'POST' and 
            response.status_code == 302 and
            request.user.is_authenticated):
            
            try:
                from .models import LoginAttempt
                LoginAttempt.objects.create(
                    user=request.user,
                    ip_address=request.META.get('REMOTE_ADDR'),
                    user_agent=request.META.get('HTTP_USER_AGENT', ''),
                    success=True
                )
            except Exception as e:
                logger.error(f"Failed to log successful login: {e}")
        
        return response




