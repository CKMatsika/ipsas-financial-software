from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import MinLengthValidator
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    """
    Custom user model with IPSAS financial software specific fields.
    """
    ROLE_CHOICES = [
        ('admin', 'Administrator'),
        ('accountant', 'Accountant'),
        ('auditor', 'Auditor'),
        ('viewer', 'Viewer'),
        ('manager', 'Financial Manager'),
    ]
    
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='viewer',
        help_text=_('User role in the system')
    )
    
    employee_id = models.CharField(
        max_length=20,
        unique=True,
        blank=True,
        null=True,
        help_text=_('Employee ID or staff number')
    )
    
    department = models.CharField(
        max_length=100,
        blank=True,
        help_text=_('Department or division')
    )
    
    phone_number = models.CharField(
        max_length=20,
        blank=True,
        help_text=_('Contact phone number')
    )
    
    is_active = models.BooleanField(
        default=True,
        help_text=_('Designates whether this user can log into the system')
    )
    
    last_login_ip = models.GenericIPAddressField(
        blank=True,
        null=True,
        help_text=_('IP address of last login')
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('User')
        verbose_name_plural = _('Users')
        ordering = ['username']
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.username})"
    
    def has_ipsas_permission(self, permission):
        """Check if user has specific IPSAS permission."""
        if self.role == 'admin':
            return True
        elif self.role == 'accountant':
            return permission in ['create', 'edit', 'view', 'delete']
        elif self.role == 'auditor':
            return permission in ['view', 'audit']
        elif self.role == 'manager':
            return permission in ['create', 'edit', 'view', 'approve']
        else:  # viewer
            return permission == 'view'


class UserSession(models.Model):
    """
    Track user sessions for audit purposes.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sessions')
    session_key = models.CharField(max_length=40, unique=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    login_time = models.DateTimeField(auto_now_add=True)
    logout_time = models.DateTimeField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-login_time']
    
    def __str__(self):
        return f"{self.user.username} - {self.login_time}"


class PasswordResetToken(models.Model):
    """
    Secure password reset tokens.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Reset token for {self.user.username}"
    
    def is_expired(self):
        from django.utils import timezone
        return timezone.now() > self.expires_at
