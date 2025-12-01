from django.utils.translation import activate, get_language
from django.utils.deprecation import MiddlewareMixin


class LandingLanguageMiddleware(MiddlewareMixin):
    """
    Middleware to handle language switching for landing pages only.
    Reads the 'landing_language' cookie and activates the language.
    This should be placed AFTER LocaleMiddleware in MIDDLEWARE settings.
    """
    
    def process_request(self, request):
        # Only process for landing pages (home, about, services, contact, etc.)
        path = request.path
        
        # Check if it's a landing page
        is_landing_page = (
            path == '/' or
            path.startswith('/about') or
            path.startswith('/services') or
            path.startswith('/contact') or
            path.startswith('/how-it-works') or
            path.startswith('/faq') or
            path.startswith('/privacy') or
            path.startswith('/terms')
        )
        
        # Also check if it's NOT an admin, users, or dashboard page
        is_not_admin = (
            not path.startswith('/admin') and
            not path.startswith('/users') and
            not path.startswith('/dashboard') and
            not path.startswith('/api') and
            not path.startswith('/static') and
            not path.startswith('/media')
        )
        
        if is_landing_page and is_not_admin:
            # Check for landing_language cookie first
            landing_language = request.COOKIES.get('landing_language')
            
            if landing_language and landing_language in ['en', 'ar']:
                # Activate the language from cookie
                activate(landing_language)
            # If no cookie, check django_language cookie as fallback
            elif not landing_language:
                django_language = request.COOKIES.get('django_language')
                if django_language and django_language in ['en', 'ar']:
                    activate(django_language)
        
        return None

