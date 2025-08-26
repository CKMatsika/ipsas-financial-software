from django.db import models
from django.core.validators import MinValueValidator
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from decimal import Decimal
import uuid


class FinancialPeriod(models.Model):
    """
    Financial reporting periods for the organization.
    """
    PERIOD_TYPES = [
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('annual', 'Annual'),
    ]
    
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('closed', 'Closed'),
        ('locked', 'Locked'),
    ]
    
    name = models.CharField(max_length=100)
    fiscal_year = models.IntegerField()
    period_number = models.IntegerField(validators=[MinValueValidator(1), MinValueValidator(12)])
    period_type = models.CharField(max_length=20, choices=PERIOD_TYPES, default='monthly')
    
    start_date = models.DateField()
    end_date = models.DateField()
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    
    # Period control
    is_adjustment_period = models.BooleanField(default=False)
    is_closing_period = models.BooleanField(default=False)
    
    # Metadata
    created_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_periods'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Financial Period')
        verbose_name_plural = _('Financial Periods')
        unique_together = ['fiscal_year', 'period_number']
        ordering = ['-fiscal_year', '-period_number']
    
    def __str__(self):
        return f"{self.fiscal_year} - Period {self.period_number}: {self.name}"
    
    def clean(self):
        """Validate period dates."""
        if self.start_date >= self.end_date:
            raise ValidationError("Start date must be before end date")


class FinancialStatement(models.Model):
    """
    Base model for all financial statements.
    """
    STATEMENT_TYPES = [
        ('sfp', 'Statement of Financial Position'),
        ('sfp_performance', 'Statement of Financial Performance'),
        ('scf', 'Statement of Cash Flows'),
        ('scna', 'Statement of Changes in Net Assets'),
        ('ppes', 'Property, Plant & Equipment Schedule'),
        ('ips', 'Investment Property Schedule'),
        ('notes', 'Notes to Financial Statements'),
        ('budget_vs_actual', 'Budget vs Actual Report'),
        ('segment', 'Segment Financial Position & Performance'),
        ('consolidated', 'Consolidated Accounts'),
    ]
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('review', 'Under Review'),
        ('approved', 'Approved'),
        ('published', 'Published'),
        ('archived', 'Archived'),
    ]
    
    # Statement identification
    statement_type = models.CharField(max_length=50, choices=STATEMENT_TYPES)
    statement_name = models.CharField(max_length=200)
    statement_code = models.CharField(max_length=20, unique=True)
    
    # Period information
    financial_period = models.ForeignKey(
        FinancialPeriod,
        on_delete=models.CASCADE,
        related_name='statements'
    )
    
    # Status and approval
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    version = models.PositiveIntegerField(default=1)
    
    # Generation details
    generated_at = models.DateTimeField(null=True, blank=True)
    generated_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='generated_statements'
    )
    
    # Approval workflow
    reviewed_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_statements'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    
    approved_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_statements'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Financial Statement')
        verbose_name_plural = _('Financial Statements')
        unique_together = ['statement_type', 'financial_period', 'version']
        ordering = ['-financial_period__fiscal_year', '-financial_period__period_number', 'statement_type']
    
    def __str__(self):
        return f"{self.statement_name} - {self.financial_period} (v{self.version})"
    
    def save(self, *args, **kwargs):
        """Auto-generate statement code if not provided."""
        if not self.statement_code:
            self.statement_code = self._generate_statement_code()
        super().save(*args, **kwargs)
    
    def _generate_statement_code(self):
        """Generate unique statement code."""
        prefix = self.statement_type.upper()[:3]
        year = self.financial_period.fiscal_year
        period = self.financial_period.period_number
        return f"{prefix}{year}{period:02d}{self.version:02d}"


class StatementLine(models.Model):
    """
    Individual line items in financial statements.
    """
    LINE_TYPES = [
        ('header', 'Header'),
        ('subtotal', 'Subtotal'),
        ('total', 'Total'),
        ('detail', 'Detail'),
        ('calculation', 'Calculation'),
    ]
    
    statement = models.ForeignKey(
        FinancialStatement,
        on_delete=models.CASCADE,
        related_name='lines'
    )
    
    # Line structure
    line_number = models.PositiveIntegerField()
    parent_line = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='child_lines'
    )
    
    # Line content
    line_type = models.CharField(max_length=20, choices=LINE_TYPES, default='detail')
    description = models.CharField(max_length=500)
    account_codes = models.TextField(blank=True)  # Comma-separated account codes
    
    # Financial amounts
    current_period_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00')
    )
    previous_period_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00')
    )
    budget_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00')
    )
    
    # Display properties
    is_bold = models.BooleanField(default=False)
    is_italic = models.BooleanField(default=False)
    indent_level = models.PositiveIntegerField(default=0)
    sort_order = models.PositiveIntegerField(default=0)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Statement Line')
        verbose_name_plural = _('Statement Lines')
        ordering = ['statement', 'sort_order', 'line_number']
        unique_together = ['statement', 'line_number']
    
    def __str__(self):
        return f"{self.statement.statement_code} - Line {self.line_number}: {self.description}"


class StatementOfFinancialPosition(models.Model):
    """
    Statement of Financial Position (Balance Sheet) specific model.
    """
    statement = models.OneToOneField(
        FinancialStatement,
        on_delete=models.CASCADE,
        related_name='sfp_details'
    )
    
    # Statement-specific fields
    reporting_date = models.DateField()
    comparative_date = models.DateField()
    
    # Key metrics
    total_assets = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    total_liabilities = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    total_equity = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    
    # Working capital
    current_assets = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    current_liabilities = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    working_capital = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Statement of Financial Position')
        verbose_name_plural = _('Statements of Financial Position')
    
    def __str__(self):
        return f"Statement of Financial Position - {self.reporting_date}"
    
    def calculate_working_capital(self):
        """Calculate working capital."""
        self.working_capital = self.current_assets - self.current_liabilities
        return self.working_capital


class StatementOfFinancialPerformance(models.Model):
    """
    Statement of Financial Performance (Income Statement) specific model.
    """
    statement = models.OneToOneField(
        FinancialStatement,
        on_delete=models.CASCADE,
        related_name='sfp_performance_details'
    )
    
    # Statement-specific fields
    reporting_period_start = models.DateField()
    reporting_period_end = models.DateField()
    comparative_period_start = models.DateField()
    comparative_period_end = models.DateField()
    
    # Key metrics
    total_revenue = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    total_expenses = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    net_surplus_deficit = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    
    # Budget comparison
    budgeted_revenue = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    budgeted_expenses = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    budgeted_surplus_deficit = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    
    # Variances
    revenue_variance = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    expense_variance = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Statement of Financial Performance')
        verbose_name_plural = _('Statements of Financial Performance')
    
    def __str__(self):
        return f"Statement of Financial Performance - {self.reporting_period_start} to {self.reporting_period_end}"
    
    def calculate_net_surplus_deficit(self):
        """Calculate net surplus/deficit."""
        self.net_surplus_deficit = self.total_revenue - self.total_expenses
        return self.net_surplus_deficit
    
    def calculate_variances(self):
        """Calculate budget variances."""
        self.revenue_variance = self.total_revenue - self.budgeted_revenue
        self.expense_variance = self.total_expenses - self.budgeted_expenses
        return self.revenue_variance, self.expense_variance


class StatementOfCashFlows(models.Model):
    """
    Statement of Cash Flows specific model.
    """
    statement = models.OneToOneField(
        FinancialStatement,
        on_delete=models.CASCADE,
        related_name='scf_details'
    )
    
    # Statement-specific fields
    reporting_period_start = models.DateField()
    reporting_period_end = models.DateField()
    
    # Operating activities
    cash_from_operations = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    cash_used_in_operations = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    net_cash_from_operations = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    
    # Investing activities
    cash_from_investing = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    cash_used_in_investing = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    net_cash_from_investing = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    
    # Financing activities
    cash_from_financing = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    cash_used_in_financing = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    net_cash_from_financing = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    
    # Net change and ending balance
    net_change_in_cash = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    cash_at_beginning = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    cash_at_end = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Statement of Cash Flows')
        verbose_name_plural = _('Statements of Cash Flows')
    
    def __str__(self):
        return f"Statement of Cash Flows - {self.reporting_period_start} to {self.reporting_period_end}"
    
    def calculate_net_cash_flows(self):
        """Calculate net cash flows for each category."""
        self.net_cash_from_operations = self.cash_from_operations - self.cash_used_in_operations
        self.net_cash_from_investing = self.cash_from_investing - self.cash_used_in_investing
        self.net_cash_from_financing = self.cash_from_financing - self.cash_used_in_financing
        
        self.net_change_in_cash = (
            self.net_cash_from_operations +
            self.net_cash_from_investing +
            self.net_cash_from_financing
        )
        
        self.cash_at_end = self.cash_at_beginning + self.net_change_in_cash
        
        return self.net_change_in_cash


class PropertyPlantEquipment(models.Model):
    """
    Property, Plant & Equipment Schedule for IPSAS compliance.
    """
    statement = models.ForeignKey(
        FinancialStatement,
        on_delete=models.CASCADE,
        related_name='ppes_details'
    )
    
    # Asset classification
    asset_category = models.CharField(max_length=100)
    asset_subcategory = models.CharField(max_length=100, blank=True)
    
    # Cost information
    cost_at_beginning = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    additions = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    disposals = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    revaluations = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    transfers = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    cost_at_end = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    
    # Accumulated depreciation
    accumulated_depreciation_beginning = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00')
    )
    depreciation_expense = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00')
    )
    accumulated_depreciation_disposals = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00')
    )
    accumulated_depreciation_revaluations = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00')
    )
    accumulated_depreciation_end = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00')
    )
    
    # Carrying amounts
    carrying_amount_beginning = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00')
    )
    carrying_amount_end = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00')
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Property, Plant & Equipment')
        verbose_name_plural = _('Property, Plant & Equipment')
        ordering = ['asset_category', 'asset_subcategory']
    
    def __str__(self):
        return f"{self.asset_category} - {self.asset_subcategory or 'General'}"
    
    def calculate_carrying_amounts(self):
        """Calculate carrying amounts."""
        self.cost_at_end = (
            self.cost_at_beginning +
            self.additions -
            self.disposals +
            self.revaluations +
            self.transfers
        )
        
        self.accumulated_depreciation_end = (
            self.accumulated_depreciation_beginning +
            self.depreciation_expense -
            self.accumulated_depreciation_disposals +
            self.accumulated_depreciation_revaluations
        )
        
        self.carrying_amount_beginning = self.cost_at_beginning - self.accumulated_depreciation_beginning
        self.carrying_amount_end = self.cost_at_end - self.accumulated_depreciation_end
        
        return self.carrying_amount_end


class FinancialStatementTemplate(models.Model):
    """
    Templates for generating financial statements.
    """
    template_name = models.CharField(max_length=200)
    statement_type = models.CharField(max_length=50, choices=FinancialStatement.STATEMENT_TYPES)
    description = models.TextField(blank=True)
    
    # Template structure (JSON field for flexibility)
    template_structure = models.JSONField()
    
    # Template metadata
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)
    
    # IPSAS compliance
    ipsas_version = models.CharField(max_length=10, default='2022')
    zimbabwe_compliance = models.BooleanField(default=True)
    
    # Metadata
    created_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_templates'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Financial Statement Template')
        verbose_name_plural = _('Financial Statement Templates')
        ordering = ['statement_type', 'template_name']
    
    def __str__(self):
        return f"{self.template_name} - {self.get_statement_type_display()}"
