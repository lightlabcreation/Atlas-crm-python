"""
Middleware for enforcing password change requirements.
"""
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.deprecation import MiddlewareMixin


class PasswordChangeRequiredMiddleware(MiddlewareMixin):
    """
    Middleware to enforce password change for users with password_change_required=True.

    This middleware intercepts all requests from authenticated users and checks if they
    have password_change_required set to True. If so, they are redirected to the password
    change page unless they are already on that page or logging out.

    Exempted URLs:
    - /users/force-password-change/ (the password change page itself)
    - /logout/ (allow users to logout)
    - /static/ (static assets)
    - /media/ (media files)
    """

    def process_request(self, request):
        """
        Process each request to check if password change is required.
        """
        # Skip if user is not authenticated
        if not request.user.is_authenticated:
            return None

        # Skip if user doesn't have password_change_required attribute
        if not hasattr(request.user, 'password_change_required'):
            return None

        # Skip if password change is not required
        if not request.user.password_change_required:
            return None

        # Allow access to the password change page itself
        force_password_change_url = reverse('users:force_password_change')
        if request.path == force_password_change_url:
            return None

        # Allow logout
        if request.path.startswith('/logout/') or request.path == reverse('users:logout'):
            return None

        # Allow static and media files
        if request.path.startswith('/static/') or request.path.startswith('/media/'):
            return None

        # Redirect to password change page
        return redirect('users:force_password_change')
