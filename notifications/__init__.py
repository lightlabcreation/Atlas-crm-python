"""
Notifications Django App

A comprehensive notification system for all user roles in the CRM system.
Provides universal notification management with advanced features like
archiving, filtering, and real-time updates.
"""

default_app_config = 'notifications.apps.NotificationsConfig'

# Version information
__version__ = '1.0.0'
__author__ = 'CRM System Development Team'
__email__ = 'dev@crm-system.com'

# App metadata
APP_NAME = 'notifications'
APP_DESCRIPTION = 'Universal notification system for CRM'
APP_VERSION = __version__

# Export key components for easy access
__all__ = [
    'APP_NAME',
    'APP_DESCRIPTION',
    'APP_VERSION',
]
