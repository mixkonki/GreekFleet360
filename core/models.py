"""
Core Models for GreekFleet 360
Polymorphic Vehicle Asset Management System
"""
from django.db import models
from django.contrib.auth.models import User
from polymorphic.models import PolymorphicModel
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal


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
    Employee Model - Minimalist personnel tracking
    """
    first_name = models.CharField(max_length=100, verbose_name="Όνομα")
    last_name = models.CharField(max_length=100, verbose_name="Επώνυμο")
    position = models.ForeignKey(
        EmployeePosition,
        on_delete=models.PROTECT,
        related_name='employees',
        verbose_name="Θέση"
    )
    assigned_vehicle = models.ForeignKey(
        'operations.Vehicle',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_employees',
        verbose_name="Συνδεδεμένο Όχημα"
    )
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='employees',
        verbose_name="Εταιρεία"
    )
    is_active = models.BooleanField(default=True, verbose_name="Ενεργός")
    
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


class DriverProfile(models.Model):
    """
    Driver Profile linked to Django User
    Handles License Types, Medical Exams, CPC
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='driver_profile',
        verbose_name="Χρήστης"
    )
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='drivers',
        verbose_name="Εταιρεία"
    )
    
    # Personal Info
    phone = models.CharField(max_length=20, verbose_name="Τηλέφωνο")
    address = models.TextField(blank=True, verbose_name="Διεύθυνση")
    date_of_birth = models.DateField(verbose_name="Ημ/νία Γέννησης")
    
    # License Categories (stored as comma-separated string)
    license_categories = models.CharField(
        max_length=50,
        verbose_name="Κατηγορίες Άδειας (π.χ. B,C,E)",
        help_text="Διαχωρισμένες με κόμμα (π.χ. B,C,E)"
    )
    license_number = models.CharField(max_length=20, unique=True, verbose_name="Αριθμός Άδειας")
    license_issue_date = models.DateField(verbose_name="Ημ/νία Έκδοσης Άδειας")
    license_expiry_date = models.DateField(verbose_name="Λήξη Άδειας")
    
    # CPC (Certificate of Professional Competence - ΠΕΙ)
    cpc_expiry = models.DateField(null=True, blank=True, verbose_name="Λήξη ΠΕΙ")
    
    # Medical Exam
    medical_card_expiry = models.DateField(null=True, blank=True, verbose_name="Λήξη Ιατρικής Κάρτας")
    
    # Point System (Sesame - Σύστημα Βαθμών)
    license_points = models.PositiveIntegerField(
        default=12,
        validators=[MaxValueValidator(12)],
        verbose_name="Βαθμοί Άδειας (Σύστημα Σησάμι)"
    )
    
    # Employment
    hire_date = models.DateField(verbose_name="Ημ/νία Πρόσληψης")
    is_active = models.BooleanField(default=True, verbose_name="Ενεργός")
    
    # Metadata
    notes = models.TextField(blank=True, verbose_name="Σημειώσεις")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Προφίλ Οδηγού"
        verbose_name_plural = "Προφίλ Οδηγών"
        ordering = ['user__last_name', 'user__first_name']
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.license_number}"
