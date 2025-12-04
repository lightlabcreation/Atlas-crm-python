from django.apps import AppConfig


class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'users'

    def ready(self):
        """Initialize audit logging when app is ready."""
        super().ready()
        try:
            from utils.audit_config import register_audit_models
            register_audit_models()
        except Exception as e:
            pass  # Migrations may not be complete yet
