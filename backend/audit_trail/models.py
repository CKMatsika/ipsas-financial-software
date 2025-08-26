from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
import json


class AuditLog(models.Model):
    """
    Comprehensive audit log for all system changes.
    """
    ACTION_CHOICES = [
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('view', 'View'),
        ('export', 'Export'),
        ('import', 'Import'),
        ('approve', 'Approve'),
        ('reject', 'Reject'),
        ('post', 'Post'),
        ('reverse', 'Reverse'),
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('password_change', 'Password Change'),
        ('permission_change', 'Permission Change'),
    ]
    
    # User and session information
    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='audit_logs'
    )
    session_id = models.CharField(max_length=100, blank=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    
    # Action details
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    timestamp = models.DateTimeField(default=timezone.now)
    
    # Object being acted upon
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # Change details
    object_repr = models.CharField(max_length=200)
    change_message = models.TextField(blank=True)
    
    # Data changes (JSON fields for flexibility)
    old_values = models.JSONField(null=True, blank=True)
    new_values = models.JSONField(null=True, blank=True)
    changed_fields = models.JSONField(null=True, blank=True)
    
    # Additional context
    module = models.CharField(max_length=100, blank=True)
    function = models.CharField(max_length=100, blank=True)
    request_path = models.CharField(max_length=500, blank=True)
    request_method = models.CharField(max_length=10, blank=True)
    
    # Metadata
    is_system_action = models.BooleanField(default=False)
    related_objects = models.JSONField(null=True, blank=True)
    
    class Meta:
        verbose_name = _('Audit Log')
        verbose_name_plural = _('Audit Logs')
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['timestamp', 'user', 'action']),
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['module', 'function']),
        ]
    
    def __str__(self):
        return f"{self.action} by {self.user} on {self.object_repr} at {self.timestamp}"
    
    def get_changes_summary(self):
        """Get a summary of what changed."""
        if not self.changed_fields:
            return "No specific fields changed"
        
        changes = []
        for field in self.changed_fields:
            old_val = self.old_values.get(field, 'N/A') if self.old_values else 'N/A'
            new_val = self.new_values.get(field, 'N/A') if self.new_values else 'N/A'
            changes.append(f"{field}: {old_val} → {new_val}")
        
        return "; ".join(changes)


class DataChangeLog(models.Model):
    """
    Detailed log of data changes for specific models.
    """
    audit_log = models.ForeignKey(
        AuditLog,
        on_delete=models.CASCADE,
        related_name='data_changes'
    )
    
    field_name = models.CharField(max_length=100)
    old_value = models.TextField(blank=True)
    new_value = models.TextField(blank=True)
    
    # Field metadata
    field_type = models.CharField(max_length=50, blank=True)
    is_sensitive = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = _('Data Change Log')
        verbose_name_plural = _('Data Change Logs')
        ordering = ['audit_log__timestamp', 'field_name']
    
    def __str__(self):
        return f"{self.field_name}: {self.old_value} → {self.new_value}"


class SystemEvent(models.Model):
    """
    System-level events and activities.
    """
    EVENT_TYPES = [
        ('system_startup', 'System Startup'),
        ('system_shutdown', 'System Shutdown'),
        ('backup', 'Backup'),
        ('maintenance', 'Maintenance'),
        ('error', 'Error'),
        ('warning', 'Warning'),
        ('info', 'Information'),
        ('security', 'Security Event'),
    ]
    
    SEVERITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    event_type = models.CharField(max_length=50, choices=EVENT_TYPES)
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default='low')
    
    # Event details
    title = models.CharField(max_length=200)
    description = models.TextField()
    details = models.JSONField(null=True, blank=True)
    
    # Timing
    occurred_at = models.DateTimeField(default=timezone.now)
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    # Related information
    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='system_events'
    )
    related_audit_logs = models.ManyToManyField(
        AuditLog,
        blank=True,
        related_name='system_events'
    )
    
    # Status
    is_resolved = models.BooleanField(default=False)
    resolution_notes = models.TextField(blank=True)
    
    class Meta:
        verbose_name = _('System Event')
        verbose_name_plural = _('System Events')
        ordering = ['-occurred_at']
        indexes = [
            models.Index(fields=['event_type', 'severity']),
            models.Index(fields=['occurred_at', 'is_resolved']),
        ]
    
    def __str__(self):
        return f"{self.title} ({self.get_severity_display()}) at {self.occurred_at}"
    
    def resolve(self, notes=""):
        """Mark the event as resolved."""
        self.is_resolved = True
        self.resolved_at = timezone.now()
        self.resolution_notes = notes
        self.save()


class ComplianceCheck(models.Model):
    """
    Track compliance checks and validations.
    """
    CHECK_TYPES = [
        ('ipsas', 'IPSAS Compliance'),
        ('zimbabwe', 'Zimbabwe Compliance'),
        ('data_integrity', 'Data Integrity'),
        ('audit_trail', 'Audit Trail'),
        ('user_access', 'User Access'),
        ('financial_controls', 'Financial Controls'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('passed', 'Passed'),
        ('failed', 'Failed'),
        ('warning', 'Warning'),
    ]
    
    check_type = models.CharField(max_length=50, choices=CHECK_TYPES)
    check_name = models.CharField(max_length=200)
    description = models.TextField()
    
    # Check details
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    started_at = models.DateTimeField(default=timezone.now)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Results
    result_details = models.JSONField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    warnings = models.JSONField(null=True, blank=True)
    
    # Compliance metadata
    compliance_standard = models.CharField(max_length=100, blank=True)
    compliance_version = models.CharField(max_length=20, blank=True)
    required_frequency = models.CharField(max_length=50, blank=True)
    
    # Related audit logs
    related_audit_logs = models.ManyToManyField(
        AuditLog,
        blank=True,
        related_name='compliance_checks'
    )
    
    class Meta:
        verbose_name = _('Compliance Check')
        verbose_name_plural = _('Compliance Checks')
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['check_type', 'status']),
            models.Index(fields=['started_at', 'completed_at']),
        ]
    
    def __str__(self):
        return f"{self.check_name} - {self.get_status_display()}"
    
    def complete_check(self, status, result_details=None, error_message=None, warnings=None):
        """Complete the compliance check."""
        self.status = status
        self.completed_at = timezone.now()
        self.result_details = result_details
        self.error_message = error_message or ""
        self.warnings = warnings or []
        self.save()


class AuditReport(models.Model):
    """
    Generated audit reports for compliance and review.
    """
    REPORT_TYPES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('annual', 'Annual'),
        ('on_demand', 'On Demand'),
    ]
    
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES)
    report_name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    # Report period
    period_start = models.DateField()
    period_end = models.DateField()
    
    # Generation details
    generated_at = models.DateTimeField(default=timezone.now)
    generated_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='generated_audit_reports'
    )
    
    # Report content
    report_data = models.JSONField()
    summary = models.TextField(blank=True)
    
    # File attachments
    report_file = models.FileField(upload_to='audit_reports/', null=True, blank=True)
    file_format = models.CharField(max_length=20, blank=True)
    
    # Status
    is_approved = models.BooleanField(default=False)
    approved_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_audit_reports'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = _('Audit Report')
        verbose_name_plural = _('Audit Reports')
        ordering = ['-generated_at']
        indexes = [
            models.Index(fields=['report_type', 'period_start', 'period_end']),
            models.Index(fields=['generated_at', 'is_approved']),
        ]
    
    def __str__(self):
        return f"{self.report_name} - {self.period_start} to {self.period_end}"
    
    def approve(self, user):
        """Approve the audit report."""
        self.is_approved = True
        self.approved_by = user
        self.approved_at = timezone.now()
        self.save()
