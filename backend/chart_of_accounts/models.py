from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from decimal import Decimal


class AccountCategory(models.Model):
    """
    Main account categories according to IPSAS standards.
    """
    CATEGORY_CHOICES = [
        ('assets', 'Assets'),
        ('liabilities', 'Liabilities'),
        ('equity', 'Equity'),
        ('revenue', 'Revenue'),
        ('expenses', 'Expenses'),
    ]
    
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=10, unique=True)
    category_type = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Account Category')
        verbose_name_plural = _('Account Categories')
        ordering = ['code']
    
    def __str__(self):
        return f"{self.code} - {self.name}"


class AccountGroup(models.Model):
    """
    Account groups within categories (e.g., Current Assets, Non-Current Assets).
    """
    category = models.ForeignKey(AccountCategory, on_delete=models.CASCADE, related_name='groups')
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Account Group')
        verbose_name_plural = _('Account Groups')
        ordering = ['category__code', 'code']
        unique_together = ['category', 'code']
    
    def __str__(self):
        return f"{self.category.code}{self.code} - {self.name}"


class AccountType(models.Model):
    """
    Specific account types (e.g., Cash, Accounts Receivable, Revenue).
    """
    group = models.ForeignKey(AccountGroup, on_delete=models.CASCADE, related_name='types')
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10)
    description = models.TextField(blank=True)
    normal_balance = models.CharField(
        max_length=4,
        choices=[('debit', 'Debit'), ('credit', 'Credit')]
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Account Type')
        verbose_name_plural = _('Account Types')
        ordering = ['group__category__code', 'group__code', 'code']
        unique_together = ['group', 'code']
    
    def __str__(self):
        return f"{self.group.category.code}{self.group.code}{self.code} - {self.name}"


class ChartOfAccount(models.Model):
    """
    Individual chart of accounts with full account codes and details.
    """
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('suspended', 'Suspended'),
    ]
    
    # Account hierarchy
    category = models.ForeignKey(AccountCategory, on_delete=models.CASCADE, related_name='accounts')
    group = models.ForeignKey(AccountGroup, on_delete=models.CASCADE, related_name='accounts')
    type = models.ForeignKey(AccountType, on_delete=models.CASCADE, related_name='accounts')
    
    # Account details
    account_number = models.CharField(max_length=20, unique=True)
    account_name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    # Financial properties
    normal_balance = models.CharField(
        max_length=4,
        choices=[('debit', 'Debit'), ('credit', 'Credit')]
    )
    opening_balance = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00')
    )
    current_balance = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00')
    )
    
    # IPSAS specific fields
    ipsas_category = models.CharField(max_length=100, blank=True)
    zimbabwe_compliance = models.BooleanField(default=True)
    disclosure_required = models.BooleanField(default=False)
    
    # Account status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    is_active = models.BooleanField(default=True)
    
    # Metadata
    created_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_accounts'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Chart of Account')
        verbose_name_plural = _('Chart of Accounts')
        ordering = ['account_number']
        indexes = [
            models.Index(fields=['account_number']),
            models.Index(fields=['category', 'group', 'type']),
            models.Index(fields=['status', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.account_number} - {self.account_name}"
    
    def clean(self):
        """Validate account structure and balances."""
        if self.normal_balance != self.type.normal_balance:
            raise ValidationError(
                f"Account normal balance must match account type normal balance: {self.type.normal_balance}"
            )
        
        if self.opening_balance < 0 and self.normal_balance == 'credit':
            raise ValidationError("Credit accounts cannot have negative opening balances")
        
        if self.opening_balance > 0 and self.normal_balance == 'debit':
            raise ValidationError("Debit accounts cannot have positive opening balances")
    
    def get_full_account_code(self):
        """Get the complete account code combining category, group, and type codes."""
        return f"{self.category.code}{self.group.code}{self.type.code}{self.account_number}"
    
    def get_balance_display(self):
        """Get formatted balance display."""
        if self.normal_balance == 'debit':
            return self.current_balance
        else:
            return -self.current_balance
    
    def is_balance_sheet_account(self):
        """Check if this is a balance sheet account."""
        return self.category.category_type in ['assets', 'liabilities', 'equity']
    
    def is_income_statement_account(self):
        """Check if this is an income statement account."""
        return self.category.category_type in ['revenue', 'expenses']


class AccountBalance(models.Model):
    """
    Track account balances over time for reporting and analysis.
    """
    account = models.ForeignKey(ChartOfAccount, on_delete=models.CASCADE, related_name='balances')
    period_start = models.DateField()
    period_end = models.DateField()
    
    # Balances
    opening_balance = models.DecimalField(max_digits=15, decimal_places=2)
    closing_balance = models.DecimalField(max_digits=15, decimal_places=2)
    
    # Movement
    total_debits = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    total_credits = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Account Balance')
        verbose_name_plural = _('Account Balances')
        ordering = ['account', '-period_end']
        unique_together = ['account', 'period_start', 'period_end']
        indexes = [
            models.Index(fields=['account', 'period_start', 'period_end']),
        ]
    
    def __str__(self):
        return f"{self.account.account_number} - {self.period_start} to {self.period_end}"
    
    def get_net_movement(self):
        """Calculate net movement for the period."""
        return self.total_debits - self.total_credits


class AccountMapping(models.Model):
    """
    Map accounts to external systems (ERP, PROMUN, LADS).
    """
    account = models.ForeignKey(ChartOfAccount, on_delete=models.CASCADE, related_name='mappings')
    external_system = models.CharField(max_length=50)  # PROMUN, LADS, etc.
    external_account_code = models.CharField(max_length=50)
    external_account_name = models.CharField(max_length=200, blank=True)
    mapping_type = models.CharField(
        max_length=20,
        choices=[
            ('one_to_one', 'One to One'),
            ('one_to_many', 'One to Many'),
            ('many_to_one', 'Many to One'),
        ],
        default='one_to_one'
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Account Mapping')
        verbose_name_plural = _('Account Mappings')
        unique_together = ['account', 'external_system', 'external_account_code']
        indexes = [
            models.Index(fields=['external_system', 'external_account_code']),
        ]
    
    def __str__(self):
        return f"{self.account.account_number} -> {self.external_system}:{self.external_account_code}"
