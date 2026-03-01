"""
Core Models for GreekFleet 360
Polymorphic Vehicle Asset Management System
"""
from django.db import models
from django.contrib.auth.models import User
from polymorphic.models import PolymorphicModel
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal

# Import driver compliance models
from .driver_compliance_models import DrivingLicenseCategory, AdrCategory, DriverCompliance


class Company(models.Model):
    """
    Multi-Tenant Company Model
    Each company has isolated data access
    """
    name = models.CharField(max_length=200, verbose_name="Επωνυμία Εταιρείας")
    tax_id = models.CharField(max_length=20, unique=True, verbose_name="ΑΦΜ")
    doy = models.CharField(max_length=100, blank=True, verbose_name="ΔΟΥ")
    address = models.TextField(blank=True, verbose_name="Διεύθυνση")
    phone = models.CharField(max_length=20, blank=True, verbose_name="Τηλέφωνο")
    email = models.EmailField(blank=True, verbose_name="Email")
    
    # Business Type
    BUSINESS_TYPES = [
        ('TRANSPORT', 'Μεταφορές Εμπορευμάτων'),
        ('PASSENGER', 'Μεταφορές Επιβατών'),
        ('TAXI', 'Ταξί'),
        ('TOUR', 'Τουριστικά'),
        ('CORPORATE', 'Εταιρικός Στόλος'),
        ('MIXED', 'Μικτός Στόλος'),
    ]
    business_type = models.CharField(
        max_length=20,
        choices=BUSINESS_TYPES,
        default='MIXED',
        verbose_name="Τύπος Επιχείρησης"
    )
    
    # Transport Type (for accounting purposes)
    TRANSPORT_TYPES = [
        ('FREIGHT', 'Εμπορευματικές Μεταφορές'),
        ('PASSENGER', 'Επιβατικές Μεταφορές'),
    ]
    transport_type = models.CharField(
        max_length=20,
        choices=TRANSPORT_TYPES,
        default='FREIGHT',
        verbose_name="Τύπος Μεταφορών"
    )
    
    # ========== FREIGHT COST INTELLIGENCE SETTINGS ==========
    utilization_rate = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        default=Decimal('0.85'),
        validators=[MinValueValidator(Decimal('0.01')), MaxValueValidator(Decimal('1.00'))],
        verbose_name="Ποσοστό Αξιοποίησης Στόλου",
        help_text="Π.χ. 0.85 για 85% - Μέσος όρος χρήσης οχημάτων"
    )
    working_days_per_year = models.IntegerField(
        default=252,
        validators=[MinValueValidator(1), MaxValueValidator(365)],
        verbose_name="Εργάσιμες Ημέρες/Έτος",
        help_text="Τυπικά 252 ημέρες (365 - 52 Σαββατοκύριακα - αργίες)"
    )
    working_hours_per_day = models.IntegerField(
        default=8,
        validators=[MinValueValidator(1), MaxValueValidator(24)],
        verbose_name="Ώρες Εργασίας/Ημέρα",
        help_text="Τυπικά 8 ώρες"
    )
    
    is_active = models.BooleanField(default=True, verbose_name="Ενεργή")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # ========== SUBSCRIPTION MANAGEMENT ==========
    SUBSCRIPTION_STATUS_CHOICES = [
        ('TRIAL', 'Δοκιμαστική Περίοδος'),
        ('ACTIVE', 'Ενεργή'),
        ('EXPIRED', 'Ληγμένη'),
    ]
    subscription_status = models.CharField(
        max_length=20,
        choices=SUBSCRIPTION_STATUS_CHOICES,
        default='ACTIVE',
        verbose_name="Κατάσταση Συνδρομής"
    )
    subscription_expires_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Λήξη Συνδρομής",
        help_text="Αν κενό, δεν υπάρχει όριο λήξης"
    )
    vehicle_limit = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Όριο Οχημάτων",
        help_text="Μέγιστος αριθμός οχημάτων (null = απεριόριστο)"
    )
    
    class Meta:
        verbose_name = "Εταιρεία"
        verbose_name_plural = "Εταιρείες"
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.tax_id})"




class EmployeePosition(models.Model):
    """
    Employee Position/Role
    """
    title = models.CharField(max_length=100, unique=True, verbose_name="Τίτλος Θέσης")
    is_driver_role = models.BooleanField(default=False, verbose_name="Θέση Οδηγού")
    
    class Meta:
        verbose_name = "Θέση Εργασίας"
        verbose_name_plural = "Θέσεις Εργασίας"
        ordering = ['title']
    
    def __str__(self):
        return self.title


class Employee(models.Model):
    """
    Employee Model - Personnel tracking with driver credentials
    """
    # Basic Info
    first_name = models.CharField(max_length=100, verbose_name="Όνομα")
    last_name = models.CharField(max_length=100, verbose_name="Επώνυμο")
    position = models.ForeignKey(
        EmployeePosition,
        on_delete=models.PROTECT,
        related_name='employees',
        verbose_name="Θέση"
    )
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='employees',
        verbose_name="Εταιρεία"
    )
    is_active = models.BooleanField(default=True, verbose_name="Ενεργός")
    
    # Personnel Data
    photo = models.ImageField(
        upload_to='employees/photos/',
        null=True,
        blank=True,
        verbose_name="Φωτογραφία"
    )
    email = models.EmailField(blank=True, verbose_name="Email")
    phone = models.CharField(max_length=20, blank=True, verbose_name="Τηλέφωνο")
    date_of_birth = models.DateField(null=True, blank=True, verbose_name="Ημ/νία Γέννησης")
    
    # Driver Credentials (nullable - only for drivers)
    driver_license_number = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="Αριθμός Άδειας Οδήγησης"
    )
    driver_license_categories = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Κατηγορίες Άδειας",
        help_text="π.χ. B,C,CE,D,DE"
    )
    driver_license_expiry = models.DateField(
        null=True,
        blank=True,
        verbose_name="Λήξη Άδειας Οδήγησης"
    )
    tachograph_card_number = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="Αριθμός Ψηφιακού Ταχογράφου"
    )
    tachograph_card_expiry = models.DateField(
        null=True,
        blank=True,
        verbose_name="Λήξη Κάρτας Ταχογράφου"
    )
    adr_category = models.CharField(
        max_length=10,
        blank=True,
        verbose_name="Κατηγορία ADR",
        help_text="Π1-Π9 για επικίνδυνα εμπορεύματα"
    )
    adr_expiry = models.DateField(
        null=True,
        blank=True,
        verbose_name="Λήξη ADR"
    )
    
    # Salary & Cost Data
    monthly_gross_salary = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name="Μικτός Μηνιαίος Μισθός (€)"
    )
    employer_contributions_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.22'),
        validators=[MinValueValidator(Decimal('0.00')), MaxValueValidator(Decimal('1.00'))],
        verbose_name="Ποσοστό Εργοδοτικών Εισφορών",
        help_text="Π.χ. 0.22 για 22%"
    )
    available_hours_per_year = models.IntegerField(
        default=1936,
        validators=[MinValueValidator(1)],
        verbose_name="Διαθέσιμες Ώρες/Έτος",
        help_text="1936 ώρες = 11 μήνες × 22 ημέρες × 8 ώρες"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Υπάλληλος"
        verbose_name_plural = "Υπάλληλοι"
        ordering = ['last_name', 'first_name']
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.position.title}"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def total_annual_cost(self):
        """
        Calculate total annual cost including 14 salaries and employer contributions
        
        Returns:
            Decimal: Total annual cost
        """
        # 14 salaries (12 months + 2 bonuses in Greece)
        annual_gross = self.monthly_gross_salary * 14
        # Add employer contributions (e.g., 22%)
        total_cost = annual_gross * (Decimal('1.00') + self.employer_contributions_rate)
        return total_cost


class EmployeeLeaveBalance(models.Model):
    """
    Employee Leave Balance per Year
    Tracks annual, sick, and other leave
    """
    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='leave_balances',
        verbose_name="Υπάλληλος"
    )
    year = models.IntegerField(verbose_name="Έτος")
    
    # Leave tracking
    annual_entitled = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        default=Decimal('20.0'),
        verbose_name="Δικαίωμα Ετήσιας Άδειας (ημέρες)"
    )
    annual_taken = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        default=Decimal('0.0'),
        verbose_name="Ληφθείσα Ετήσια Άδεια (ημέρες)"
    )
    sick_taken = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        default=Decimal('0.0'),
        verbose_name="Ληφθείσα Αναρρωτική (ημέρες)"
    )
    other_taken = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        default=Decimal('0.0'),
        verbose_name="Άλλες Άδειες (ημέρες)"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Υπόλοιπο Αδειών Υπαλλήλου"
        verbose_name_plural = "Υπόλοιπα Αδειών Υπαλλήλων"
        unique_together = [['employee', 'year']]
        ordering = ['-year', 'employee__last_name']
    
    def __str__(self):
        return f"{self.employee.full_name} - {self.year}"
    
    @property
    def annual_remaining(self):
        """Calculate remaining annual leave"""
        return self.annual_entitled - self.annual_taken
