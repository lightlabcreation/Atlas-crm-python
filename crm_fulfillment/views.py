from django.shortcuts import render
from django.http import Http404

def custom_404(request, exception):
    """Custom 404 page handler."""
    return render(request, '404.html', status=404)

def custom_500(request):
    """Custom 500 page handler."""
    return render(request, '500.html', status=500)


def test_simple_permission_denied(request):
    """
    Simple test view to verify the permission denied system is working.
    """
    context = {
        'custom_message': 'This is a test message from the simple permission denied view.',
        'error_type': 'permission_denied',
        'page_title': 'Test Permission Denied'
    }
    
    return render(request, 'simple_permission_denied.html', context, status=403) 