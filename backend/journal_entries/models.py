from django.db import models
from django.core.validators import MinValueValidator
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.db import transaction
from decimal import Decimal
import uuid
from django.utils import timezone


class JournalEntry(models.Model):
    """
    Main journal entry model representing a complete financial transaction.
    """
    ENTRY_TYPES = [
        ('regular', 'Regular Entry'),
        ('adjusting', 'Adjusting Entry'),
        ('closing', 'Closing Entry'),
        ('reversing', 'Reversing Entry'),
        ('opening', 'Opening Entry'),
        ('import', 'Imported Entry'),
    ]
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('posted', 'Posted'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    ]
    
    # Basic information
    entry_number = models.CharField(max_length=20, unique=True)
    entry_date = models.DateField()
    reference_number = models.CharField(max_length=50, blank=True)
    description = models.TextField()
    
    # Entry classification
    entry_type = models.CharField(max_length=20, choices=ENTRY_TYPES, default='regular')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Financial period
    fiscal_year = models.IntegerField()
    fiscal_period = models.IntegerField(validators=[MinValueValidator(1), MinValueValidator(12)])
    
    # Amounts
    total_debits = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    total_credits = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    
    # Audit fields
    created_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.PROTECT,
        related_name='created_entries'
    )
    approved_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_entries'
    )
    posted_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='posted_entries'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    posted_at = models.DateTimeField(null=True, blank=True)
    
    # Additional metadata
    source_system = models.CharField(max_length=50, blank=True)  # PROMUN, LADS, manual
    batch_id = models.CharField(max_length=50, blank=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        verbose_name = _('Journal Entry')
        verbose_name_plural = _('Journal Entries')
        ordering = ['-entry_date', '-created_at']
        indexes = [
            models.Index(fields=['entry_date', 'fiscal_year', 'fiscal_period']),
            models.Index(fields=['status', 'entry_type']),
            models.Index(fields=['created_by', 'status']),
        ]
    
    def __str__(self):
        return f"{self.entry_number} - {self.description[:50]}"
    
    def clean(self):
        """Validate journal entry."""
        if self.total_debits != self.total_credits:
            raise ValidationError("Total debits must equal total credits")
        
        if self.fiscal_period < 1 or self.fiscal_period > 12:
            raise ValidationError("Fiscal period must be between 1 and 12")
    
    def save(self, *args, **kwargs):
        """Override save to auto-generate entry number if not provided."""
        if not self.entry_number:
            self.entry_number = self._generate_entry_number()
        super().save(*args, **kwargs)
    
    def _generate_entry_number(self):
        """Generate unique entry number."""
        import datetime
        today = datetime.date.today()
        prefix = f"JE{today.year}{today.month:02d}"
        
        # Get the last entry number for today
        last_entry = JournalEntry.objects.filter(
            entry_number__startswith=prefix
        ).order_by('-entry_number').first()
        
        if last_entry:
            try:
                last_number = int(last_entry.entry_number[-4:])
                new_number = last_number + 1
            except ValueError:
                new_number = 1
        else:
            new_number = 1
        
        return f"{prefix}{new_number:04d}"
    
    def get_balance(self):
        """Get the balance (should always be zero for valid entries)."""
        return self.total_debits - self.total_credits
    
    def can_approve(self, user):
        """Check if user can approve this entry."""
        if self.status != 'pending':
            return False
        
        if user.role in ['admin', 'manager']:
            return True
        
        return False
    
    def can_post(self, user):
        """Check if user can post this entry."""
        if self.status != 'approved':
            return False
        
        if user.role in ['admin', 'accountant']:
            return True
        
        return False
    
    def approve(self, user):
        """Approve the journal entry."""
        if not self.can_approve(user):
            raise ValidationError("User cannot approve this entry")
        
        self.status = 'approved'
        self.approved_by = user
        self.approved_at = timezone.now()
        self.save()
    
    def post(self, user):
        """Post the journal entry to accounts."""
        if not self.can_post(user):
            raise ValidationError("User cannot post this entry")
        
        with transaction.atomic():
            # Update account balances
            for line in self.lines.all():
                line.account.current_balance += line.debit_amount - line.credit_amount
                line.account.save()
            
            self.status = 'posted'
            self.posted_by = user
            self.posted_at = timezone.now()
            self.save()
    
    def reverse(self, user):
        """Create a reversing entry."""
        if self.status != 'posted':
            raise ValidationError("Only posted entries can be reversed")
        
        # Create reversing entry logic here
        pass


class JournalEntryLine(models.Model):
    """
    Individual line items within a journal entry.
    """
    journal_entry = models.ForeignKey(
        JournalEntry,
        on_delete=models.CASCADE,
        related_name='lines'
    )
    account = models.ForeignKey(
        'chart_of_accounts.ChartOfAccount',
        on_delete=models.PROTECT,
        related_name='journal_lines'
    )
    
    # Line details
    line_number = models.PositiveIntegerField()
    description = models.CharField(max_length=200)
    
    # Amounts
    debit_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00')
    )
    credit_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00')
    )
    
    # Additional fields
    project_code = models.CharField(max_length=50, blank=True)
    cost_center = models.CharField(max_length=50, blank=True)
    fund_code = models.CharField(max_length=50, blank=True)
    
    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Journal Entry Line')
        verbose_name_plural = _('Journal Entry Lines')
        ordering = ['journal_entry', 'line_number']
        unique_together = ['journal_entry', 'line_number']
        indexes = [
            models.Index(fields=['account', 'journal_entry']),
        ]
    
    def __str__(self):
        return f"{self.journal_entry.entry_number} - Line {self.line_number}: {self.account.account_name}"
    
    def clean(self):
        """Validate line item."""
        if self.debit_amount < 0 or self.credit_amount < 0:
            raise ValidationError("Amounts cannot be negative")
        
        if self.debit_amount > 0 and self.credit_amount > 0:
            raise ValidationError("Line cannot have both debit and credit amounts")
        
        if self.debit_amount == 0 and self.credit_amount == 0:
            raise ValidationError("Line must have either debit or credit amount")
    
    def get_amount(self):
        """Get the amount for this line (positive for debit, negative for credit)."""
        if self.debit_amount > 0:
            return self.debit_amount
        else:
            return -self.credit_amount


class JournalEntryAttachment(models.Model):
    """
    Attachments for journal entries (receipts, invoices, etc.).
    """
    journal_entry = models.ForeignKey(
        JournalEntry,
        on_delete=models.CASCADE,
        related_name='attachments'
    )
    file_name = models.CharField(max_length=255)
    file_path = models.FileField(upload_to='journal_attachments/')
    file_type = models.CharField(max_length=100)
    file_size = models.PositiveIntegerField()
    description = models.CharField(max_length=200, blank=True)
    
    uploaded_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='uploaded_attachments'
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('Journal Entry Attachment')
        verbose_name_plural = _('Journal Entry Attachments')
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return f"{self.journal_entry.entry_number} - {self.file_name}"


class JournalEntryApproval(models.Model):
    """
    Track approval workflow for journal entries.
    """
    journal_entry = models.ForeignKey(
        JournalEntry,
        on_delete=models.CASCADE,
        related_name='approvals'
    )
    approver = models.ForeignKey(
        'accounts.User',
        on_delete=models.PROTECT,
        related_name='entry_approvals'
    )
    
    action = models.CharField(
        max_length=20,
        choices=[
            ('approved', 'Approved'),
            ('rejected', 'Rejected'),
            ('returned', 'Returned for Revision'),
        ]
    )
    
    comments = models.TextField(blank=True)
    action_date = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('Journal Entry Approval')
        verbose_name_plural = _('Journal Entry Approvals')
        ordering = ['-action_date']
    
    def __str__(self):
        return f"{self.journal_entry.entry_number} - {self.action} by {self.approver.username}"


class TrialBalance(models.Model):
    """
    Trial balance for a specific period.
    """
    fiscal_year = models.IntegerField()
    fiscal_period = models.IntegerField(validators=[MinValueValidator(1), MinValueValidator(12)])
    as_of_date = models.DateField()
    
    # Balances
    total_debits = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    total_credits = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    
    # Status
    is_balanced = models.BooleanField(default=False)
    is_closed = models.BooleanField(default=False)
    
    # Metadata
    created_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_trial_balances'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Trial Balance')
        verbose_name_plural = _('Trial Balances')
        unique_together = ['fiscal_year', 'fiscal_period']
        ordering = ['-fiscal_year', '-fiscal_period']
    
    def __str__(self):
        return f"Trial Balance - {self.fiscal_year} Period {self.fiscal_period}"
    
    def get_balance(self):
        """Get the balance (should be zero if balanced)."""
        return self.total_debits - self.total_credits


class TrialBalanceLine(models.Model):
    """
    Individual line items in trial balance.
    """
    trial_balance = models.ForeignKey(
        TrialBalance,
        on_delete=models.CASCADE,
        related_name='lines'
    )
    account = models.ForeignKey(
        'chart_of_accounts.ChartOfAccount',
        on_delete=models.PROTECT,
        related_name='trial_balance_lines'
    )
    
    # Balances
    opening_debit = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    opening_credit = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    period_debit = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    period_credit = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    closing_debit = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    closing_credit = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    
    class Meta:
        verbose_name = _('Trial Balance Line')
        verbose_name_plural = _('Trial Balance Lines')
        unique_together = ['trial_balance', 'account']
        ordering = ['account__account_number']
    
    def __str__(self):
        return f"{self.account.account_number} - {self.account.account_name}"
    
    def get_opening_balance(self):
        """Get opening balance."""
        if self.opening_debit > 0:
            return self.opening_debit
        else:
            return -self.opening_credit
    
    def get_closing_balance(self):
        """Get closing balance."""
        if self.closing_debit > 0:
            return self.closing_debit
        else:
            return -self.closing_credit
