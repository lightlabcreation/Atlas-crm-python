from django.db import models
from django.contrib.auth import get_user_model
from django_otp.models import Device

User = get_user_model()


class User2FAProfile(models.Model):
    """User 2FA Profile to store 2FA settings and backup codes"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='twofa_profile')
    is_enabled = models.BooleanField(default=False)
    backup_codes = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.email} - 2FA: {'Enabled' if self.is_enabled else 'Disabled'}"
    
    def generate_backup_codes(self, count=10):
        """Generate backup codes for the user"""
        import secrets
        import string
        
        codes = []
        for _ in range(count):
            code = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))
            codes.append(code)
        
        self.backup_codes = codes
        self.save()
        return codes
    
    def verify_backup_code(self, code):
        """Verify if a backup code is valid"""
        if code in self.backup_codes:
            self.backup_codes.remove(code)
            self.save()
            return True
        return False
    
    def has_backup_codes(self):
        """Check if user has any backup codes left"""
        return len(self.backup_codes) > 0


class LoginAttempt(models.Model):
    """Track login attempts for security monitoring"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='login_attempts')
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    success = models.BooleanField(default=False)
    failure_reason = models.CharField(max_length=100, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.user.email} - {self.ip_address} - {'Success' if self.success else 'Failed'}"


