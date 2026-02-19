"""
Finance Models for GreekFleet 360
Financial Core & Cost Engine - Refactored with Hierarchical Expense Structure
"""
from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal
from datetime import timedelta
from core.models import Company, DriverProfile
from core.mixins import CompanyScopedManager


class ExpenseFamily(models.Model):
    """
    Top-level grouping for expense categories
    E.g., Buildings, Communication, HR, Taxes
    """
    name = models.CharField(max_length=100, unique=True, verbose_name="Οικογένεια Εξόδων")
    icon = models.CharField(
        max_length=50,
        default='folder',
        verbose_name="Font Awesome Icon",
        help_text="e.g., 'building', 'wifi', 'users', 'file-invoice'"
    )
    description = models.TextField(blank=True, verbose_name="Περιγραφή")
    display_order = models.IntegerField(default=0, verbose_name="Σειρά Εμφάνισης")
    
    class Meta:
        verbose_name = "Οικογένεια Εξόδων"
        verbose_name_plural = "Οικογένειες Εξόδων"
        ordering = ['display_order', 'name']
    
    def __str__(self):
        return self.name


class ExpenseCategory(models.Model):
    """
    Master Data: Expense Categories
    Supports both system-wide defaults and tenant-specific custom categories
    """
    family = models.ForeignKey(
        ExpenseFamily,
        on_delete=models.PROTECT,
        related_name='categories',
        verbose_name="Οικογένεια"
    )
    name = models.CharField(max_length=100, verbose_name="Κατηγορία")
    description = models.TextField(blank=True, verbose_name="Περιγραφή")
    is_system_default = models.BooleanField(
        default=False,
        verbose_name="Προεπιλεγμένη Κατηγορία",
        help_text="Κατηγορίες που δημιουργούνται αυτόματα από το σύστημα"
    )
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='custom_categories',
        verbose_name="Εταιρεία",
        help_text="Αν NULL, είναι προεπιλεγμένη κατηγορία. Αν έχει εταιρεία, είναι προσαρμοσμένη."
    )
    
    class Meta:
        verbose_name = "Κατηγορία Εξόδου"
        verbose_name_plural = "Κατηγορίες Εξόδων"
        ordering = ['family', 'name']
        unique_together = [['company', 'name']]
    
    def __str__(self):
        if self.company:
            return f"{self.family.name} - {self.name} ({self.company.name})"
        return f"{self.family.name} - {self.name} [System]"


class CostCenter(models.Model):
    """
    Cost Centers for expense allocation
    Enhanced for Cost Engine with type classification and entity linking
    """
    TYPE_CHOICES = [
        ('VEHICLE', 'Όχημα'),
        ('DRIVER', 'Οδηγός'),
        ('OVERHEAD', 'Γενικά Έξοδα'),
        ('ROUTE', 'Διαδρομή'),
        ('OTHER', 'Άλλο'),
    ]
    
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='cost_centers',
        verbose_name="Εταιρεία"
    )
    
    # Tenant Isolation Managers
    objects = CompanyScopedManager()
    all_objects = models.Manager()
    
    name = models.CharField(max_length=100, verbose_name="Όνομα Κέντρου Κόστους")
    description = models.TextField(blank=True, verbose_name="Περιγραφή")
    type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        default='OTHER',
        verbose_name="Τύπος Κέντρου"
    )
    
    # Entity Linking for automated mapping
    vehicle = models.ForeignKey(
        'operations.Vehicle',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cost_center',
        verbose_name="Όχημα",
        help_text="Σύνδεση με όχημα για αυτόματη κατανομή"
    )
    driver = models.ForeignKey(
        DriverProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cost_center',
        verbose_name="Οδηγός",
        help_text="Σύνδεση με οδηγό για αυτόματη κατανομή"
    )
    
    is_active = models.BooleanField(default=True, verbose_name="Ενεργό")
    
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    
    class Meta:
        verbose_name = "Κέντρο Κόστους"
        verbose_name_plural = "Κέντρα Κόστους"
        unique_together = ['company', 'name']
        ordering = ['company', 'name']
    
    def __str__(self):
        return f"{self.company.name} - {self.name}"


class CompanyExpense(models.Model):
    """
    Company Expenses - Supports both recurring and one-off amortized expenses
    """
    EXPENSE_TYPE_CHOICES = [
        ('RECURRING', 'Τακτικό'),
        ('ONE_OFF', 'Έκτακτο'),
    ]
    
    PERIODICITY_CHOICES = [
        ('MONTHLY', 'Μηνιαίο'),
        ('QUARTERLY', 'Τριμηνιαίο'),
        ('BIANNUAL', 'Εξαμηνιαίο'),
        ('YEARLY', 'Ετήσιο'),
        ('NONE', 'Εφάπαξ'),
    ]
    
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='company_expenses',
        verbose_name="Εταιρεία"
    )
    
    # Tenant Isolation Managers
    objects = CompanyScopedManager()
    all_objects = models.Manager()
    
    category = models.ForeignKey(
        ExpenseCategory,
        on_delete=models.PROTECT,
        related_name='company_expenses',
        verbose_name="Κατηγορία"
    )
    cost_center = models.ForeignKey(
        CostCenter,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='company_expenses',
        verbose_name="Κέντρο Κόστους"
    )
    
    # Cost Allocation
    distribute_to_all_centers = models.BooleanField(
        default=False,
        verbose_name="Επιμερισμός σε όλα τα κέντρα",
        help_text="Αν επιλεγεί, το κόστος θα μοιραστεί ισόποσα σε όλα τα ενεργά κέντρα κόστους"
    )
    
    # Employee Link
    employee = models.ForeignKey(
        'core.Employee',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='expenses',
        verbose_name="Υπάλληλος"
    )
    
    # Expense Type & Periodicity
    expense_type = models.CharField(
        max_length=20,
        choices=EXPENSE_TYPE_CHOICES,
        default='RECURRING',
        verbose_name="Τύπος Εξόδου"
    )
    periodicity = models.CharField(
        max_length=20,
        choices=PERIODICITY_CHOICES,
        default='MONTHLY',
        verbose_name="Περιοδικότητα"
    )
    
    # Financial Details
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name="Ποσό (€)"
    )
    
    # Date Range
    start_date = models.DateField(verbose_name="Ημ/νία Έναρξης")
    end_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="Ημ/νία Λήξης",
        help_text="Αν κενό, το έξοδο είναι ανοιχτό (recurring)"
    )
    
    # Amortization
    is_amortized = models.BooleanField(
        default=False,
        verbose_name="Κατανομή σε μήνες",
        help_text="π.χ. Ένα ετήσιο έξοδο 120€ θα υπολογίζεται ως 10€/μήνα"
    )
    
    # Invoice
    invoice_number = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Αριθμός Τιμολογίου"
    )
    
    # Metadata
    description = models.TextField(blank=True, verbose_name="Περιγραφή")
    is_active = models.BooleanField(default=True, verbose_name="Ενεργό")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Έξοδο Εταιρείας"
        verbose_name_plural = "Έξοδα Εταιρείας"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['company', 'is_active']),
            models.Index(fields=['category']),
            models.Index(fields=['start_date', 'end_date']),
        ]
    
    def __str__(self):
        return f"{self.category.name} - €{self.amount} ({self.start_date})"
    
    @property
    def monthly_impact(self):
        """
        Calculate monthly impact of this expense
        
        Returns:
            Decimal: Monthly cost impact
        """
        if self.expense_type == 'ONE_OFF':
            return Decimal('0.00')
        
        if self.periodicity == 'MONTHLY':
            return self.amount
        elif self.periodicity == 'QUARTERLY':
            return self.amount / Decimal('3.0')
        elif self.periodicity == 'BIANNUAL':
            return self.amount / Decimal('6.0')
        elif self.periodicity == 'YEARLY':
            return self.amount / Decimal('12.0')
        
        return Decimal('0.00')
    
    @property
    def annual_impact(self):
        """
        Calculate annual impact of this expense
        
        Returns:
            Decimal: Annual cost impact
        """
        if self.expense_type == 'ONE_OFF':
            return self.amount
        
        if self.periodicity == 'MONTHLY':
            return self.amount * 12
        elif self.periodicity == 'QUARTERLY':
            return self.amount * 4
        elif self.periodicity == 'BIANNUAL':
            return self.amount * 2
        elif self.periodicity == 'YEARLY':
            return self.amount
        
        return Decimal('0.00')
    
    def get_daily_cost(self):
        """
        Calculate daily cost for amortized expenses
        
        Returns:
            Decimal: Daily cost
        """
        if not self.is_amortized or not self.end_date:
            return Decimal('0.00')
        
        days = (self.end_date - self.start_date).days + 1
        if days <= 0:
            return Decimal('0.00')
        
        return self.amount / Decimal(str(days))
    
    def get_period_cost(self, period_start, period_end):
        """
        Calculate allocated cost for a specific period
        
        Args:
            period_start: datetime.date
            period_end: datetime.date
        
        Returns:
            Decimal: Allocated cost for the period
        """
        if not self.is_active:
            return Decimal('0.00')
        
        overlap_start = max(self.start_date, period_start)
        overlap_end = min(self.end_date or period_end, period_end)
        
        if overlap_start > overlap_end:
            return Decimal('0.00')
        
        if self.is_amortized and self.end_date:
            daily_rate = self.get_daily_cost()
            days_in_period = (overlap_end - overlap_start).days + 1
            return daily_rate * Decimal(str(days_in_period))
        else:
            return self.amount


RecurringExpense = CompanyExpense


class TransportOrder(models.Model):
    """
    Transport Order - The Revenue Side
    Links revenue to specific vehicles and calculates profitability
    """
    STATUS_CHOICES = [
        ('PENDING', 'Εκκρεμεί'),
        ('IN_PROGRESS', 'Σε Εξέλιξη'),
        ('COMPLETED', 'Ολοκληρώθηκε'),
        ('INVOICED', 'Τιμολογήθηκε'),
    ]
    
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='transport_orders',
        verbose_name="Εταιρεία"
    )
    
    # Tenant Isolation Managers
    objects = CompanyScopedManager()
    all_objects = models.Manager()
    
    customer_name = models.CharField(max_length=200, verbose_name="Όνομα Πελάτη")
    date = models.DateField(verbose_name="Ημερομηνία")
    origin = models.CharField(max_length=200, verbose_name="Αφετηρία")
    destination = models.CharField(max_length=200, verbose_name="Προορισμός")
    distance_km = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name="Απόσταση (km)"
    )
    
    agreed_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name="Συμφωνημένη Τιμή (€)"
    )
    
    assigned_vehicle = models.ForeignKey(
        'operations.Vehicle',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transport_orders',
        verbose_name="Όχημα"
    )
    assigned_driver = models.ForeignKey(
        DriverProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transport_orders',
        verbose_name="Οδηγός"
    )
    
    duration_hours = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name="Διάρκεια (ώρες)"
    )
    tolls_cost = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name="Διόδια (€)"
    )
    ferry_cost = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name="Πορθμείο (€)"
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING',
        verbose_name="Κατάσταση"
    )
    
    notes = models.TextField(blank=True, verbose_name="Σημειώσεις")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Εντολή Μεταφοράς"
        verbose_name_plural = "Εντολές Μεταφοράς"
        ordering = ['-date', '-created_at']
        indexes = [
            models.Index(fields=['company', '-date']),
            models.Index(fields=['assigned_vehicle', '-date']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.customer_name} - {self.origin} → {self.destination} - {self.date}"


class CostItem(models.Model):
    """
    Cost Item - Defines types of costs for financial intelligence
    E.g., Insurance, Fuel, Driver Social Security, Maintenance
    """
    CATEGORY_CHOICES = [
        ('FIXED', 'Σταθερό'),
        ('VARIABLE', 'Μεταβλητό'),
        ('INDIRECT', 'Έμμεσο'),
    ]
    
    UNIT_CHOICES = [
        ('MONTH', 'Μήνας'),
        ('KM', 'Χιλιόμετρο'),
        ('HOUR', 'Ώρα'),
        ('TRIP', 'Δρομολόγιο'),
    ]
    
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='cost_items',
        verbose_name="Εταιρεία"
    )
    
    # Tenant Isolation Managers
    objects = CompanyScopedManager()
    all_objects = models.Manager()
    
    name = models.CharField(max_length=100, verbose_name="Όνομα Κόστους")
    description = models.TextField(blank=True, verbose_name="Περιγραφή")
    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        verbose_name="Κατηγορία Κόστους"
    )
    unit = models.CharField(
        max_length=20,
        choices=UNIT_CHOICES,
        verbose_name="Μονάδα Μέτρησης"
    )
    
    is_active = models.BooleanField(default=True, verbose_name="Ενεργό")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Στοιχείο Κόστους"
        verbose_name_plural = "Στοιχεία Κόστους"
        unique_together = ['company', 'name']
        ordering = ['company', 'category', 'name']
        indexes = [
            models.Index(fields=['company', 'category']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.get_category_display()}) - {self.get_unit_display()}"


class CostPosting(models.Model):
    """
    Cost Posting - Actual transaction/allocation records
    Links cost items to cost centers for a specific period
    """
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='cost_postings',
        verbose_name="Εταιρεία"
    )
    
    # Tenant Isolation Managers
    objects = CompanyScopedManager()
    all_objects = models.Manager()
    
    cost_center = models.ForeignKey(
        CostCenter,
        on_delete=models.CASCADE,
        related_name='cost_postings',
        verbose_name="Κέντρο Κόστους"
    )
    cost_item = models.ForeignKey(
        CostItem,
        on_delete=models.PROTECT,
        related_name='cost_postings',
        verbose_name="Στοιχείο Κόστους"
    )
    
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name="Ποσό (€)"
    )
    
    period_start = models.DateField(verbose_name="Έναρξη Περιόδου")
    period_end = models.DateField(verbose_name="Λήξη Περιόδου")
    
    notes = models.TextField(blank=True, verbose_name="Σημειώσεις")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Καταχώρηση Κόστους"
        verbose_name_plural = "Καταχωρήσεις Κόστους"
        ordering = ['-period_start', '-created_at']
        indexes = [
            models.Index(fields=['company', '-period_start']),
            models.Index(fields=['cost_center', '-period_start']),
            models.Index(fields=['cost_item']),
        ]
    
    def __str__(self):
        return f"{self.cost_item.name} → {self.cost_center.name}: €{self.amount} ({self.period_start})"


class CostRateSnapshot(models.Model):
    """
    Cost Rate Snapshot - Calculated rates per CostCenter for a period
    Stores the result of cost engine calculations for historical tracking
    """
    STATUS_CHOICES = [
        ('OK', 'OK'),
        ('MISSING_ACTIVITY', 'Χωρίς Δραστηριότητα'),
    ]
    
    BASIS_UNIT_CHOICES = [
        ('KM', 'Χιλιόμετρο'),
        ('HOUR', 'Ώρα'),
        ('TRIP', 'Δρομολόγιο'),
        ('REVENUE', 'Έσοδα'),
    ]
    
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='cost_rate_snapshots',
        verbose_name="Εταιρεία"
    )
    
    # Tenant Isolation Managers
    objects = CompanyScopedManager()
    all_objects = models.Manager()
    
    period_start = models.DateField(verbose_name="Έναρξη Περιόδου")
    period_end = models.DateField(verbose_name="Λήξη Περιόδου")
    
    cost_center = models.ForeignKey(
        CostCenter,
        on_delete=models.CASCADE,
        related_name='rate_snapshots',
        verbose_name="Κέντρο Κόστους"
    )
    
    basis_unit = models.CharField(
        max_length=20,
        choices=BASIS_UNIT_CHOICES,
        verbose_name="Μονάδα Βάσης"
    )
    
    total_cost = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Συνολικό Κόστος (€)"
    )
    
    total_units = models.DecimalField(
        max_digits=12,
        decimal_places=3,
        default=Decimal('0.000'),
        verbose_name="Συνολικές Μονάδες"
    )
    
    rate = models.DecimalField(
        max_digits=12,
        decimal_places=6,
        default=Decimal('0.000000'),
        verbose_name="Τιμή ανά Μονάδα (€)"
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='OK',
        verbose_name="Κατάσταση"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Στιγμιότυπο Τιμής Κόστους"
        verbose_name_plural = "Στιγμιότυπα Τιμών Κόστους"
        ordering = ['-period_start', '-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['company', 'period_start', 'period_end', 'cost_center', 'basis_unit'],
                name='unique_cost_rate_snapshot'
            )
        ]
        indexes = [
            models.Index(fields=['company', '-period_start']),
            models.Index(fields=['cost_center', '-period_start']),
        ]
    
    def __str__(self):
        return f"{self.cost_center.name} - {self.basis_unit}: €{self.rate}/unit ({self.period_start})"


class OrderCostBreakdown(models.Model):
    """
    Order Cost Breakdown - Detailed cost analysis per TransportOrder
    Links calculated costs to specific orders for profitability tracking
    """
    STATUS_CHOICES = [
        ('OK', 'OK'),
        ('MISSING_RATE', 'Λείπει Τιμή'),
    ]
    
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='order_cost_breakdowns',
        verbose_name="Εταιρεία"
    )
    
    # Tenant Isolation Managers
    objects = CompanyScopedManager()
    all_objects = models.Manager()
    
    transport_order = models.ForeignKey(
        TransportOrder,
        on_delete=models.CASCADE,
        related_name='cost_breakdown',
        verbose_name="Εντολή Μεταφοράς"
    )
    
    period_start = models.DateField(verbose_name="Έναρξη Περιόδου")
    period_end = models.DateField(verbose_name="Λήξη Περιόδου")
    
    # Cost Allocations
    vehicle_alloc = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Κατανομή Οχήματος (€)"
    )
    
    overhead_alloc = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Κατανομή Γενικών Εξόδων (€)"
    )
    
    direct_cost = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Άμεσο Κόστος (€)"
    )
    
    total_cost = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Συνολικό Κόστος (€)"
    )
    
    # Revenue & Profitability
    revenue = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Έσοδα (€)"
    )
    
    profit = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Κέρδος (€)"
    )
    
    margin = models.DecimalField(
        max_digits=7,
        decimal_places=4,
        default=Decimal('0.0000'),
        verbose_name="Περιθώριο (%)"
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='OK',
        verbose_name="Κατάσταση"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Ανάλυση Κόστους Εντολής"
        verbose_name_plural = "Αναλύσεις Κόστους Εντολών"
        ordering = ['-period_start', '-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['company', 'transport_order', 'period_start', 'period_end'],
                name='unique_order_cost_breakdown'
            )
        ]
        indexes = [
            models.Index(fields=['company', '-period_start']),
            models.Index(fields=['transport_order']),
        ]
    
    def __str__(self):
        return f"{self.transport_order} - Κόστος: €{self.total_cost}, Κέρδος: €{self.profit}"
