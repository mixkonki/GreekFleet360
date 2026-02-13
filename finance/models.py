"""
Finance Models for GreekFleet 360
Financial Core & Cost Engine - Refactored with Hierarchical Expense Structure
"""
from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal
from datetime import timedelta
from core.models import Company, VehicleAsset, DriverProfile


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
    System-wide categories for recurring expenses
    """
    family = models.ForeignKey(
        ExpenseFamily,
        on_delete=models.PROTECT,
        related_name='categories',
        verbose_name="Οικογένεια"
    )
    name = models.CharField(max_length=100, unique=True, verbose_name="Κατηγορία")
    description = models.TextField(blank=True, verbose_name="Περιγραφή")
    is_system_default = models.BooleanField(
        default=False,
        verbose_name="Προεπιλεγμένη Κατηγορία",
        help_text="Κατηγορίες που δημιουργούνται αυτόματα από το σύστημα"
    )
    
    class Meta:
        verbose_name = "Κατηγορία Εξόδου"
        verbose_name_plural = "Κατηγορίες Εξόδων"
        ordering = ['family', 'name']
    
    def __str__(self):
        return f"{self.family.name} - {self.name}"


class CostCenter(models.Model):
    """
    Cost Centers for expense allocation
    """
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='cost_centers',
        verbose_name="Εταιρεία"
    )
    name = models.CharField(max_length=100, verbose_name="Όνομα Κέντρου Κόστους")
    description = models.TextField(blank=True, verbose_name="Περιγραφή")
    is_active = models.BooleanField(default=True, verbose_name="Ενεργό")
    
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
        ('YEARLY', 'Ετήσιο'),
        ('NONE', 'Εφάπαξ'),
    ]
    
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='company_expenses',
        verbose_name="Εταιρεία"
    )
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
    
    # Date Range (replaces frequency)
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
        verbose_name="Αποσβέσιμο",
        help_text="Αν True, το κόστος κατανέμεται ημερησίως στο διάστημα start_date - end_date"
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
        
        # Determine overlap between expense range and query period
        overlap_start = max(self.start_date, period_start)
        overlap_end = min(self.end_date or period_end, period_end)
        
        if overlap_start > overlap_end:
            return Decimal('0.00')
        
        if self.is_amortized and self.end_date:
            # Amortized: Calculate daily rate and multiply by days in period
            daily_rate = self.get_daily_cost()
            days_in_period = (overlap_end - overlap_start).days + 1
            return daily_rate * Decimal(str(days_in_period))
        else:
            # Non-amortized: Full amount if period overlaps
            return self.amount


# Backward compatibility alias
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
    
    # Customer & Route
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
    
    # Revenue
    agreed_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name="Συμφωνημένη Τιμή (€)"
    )
    
    # Assignment
    assigned_vehicle = models.ForeignKey(
        VehicleAsset,
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
    
    # Trip Details
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
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING',
        verbose_name="Κατάσταση"
    )
    
    # Metadata
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
