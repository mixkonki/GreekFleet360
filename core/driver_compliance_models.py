"""
Driver Compliance Models for GreekFleet 360
Tracks driver credentials, licenses, and certifications
"""
from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal


class DrivingLicenseCategory(models.Model):
    """
    Driving License Categories (A, B, C, CE, D, DE, etc.)
    Bilingual lookup table
    """
    code = models.CharField(
        max_length=10,
        unique=True,
        verbose_name="Κωδικός Κατηγορίας",
        help_text="π.χ. B, C, CE, D, DE"
    )
    label_el = models.CharField(
        max_length=100,
        verbose_name="Ελληνική Ονομασία"
    )
    label_en = models.CharField(
        max_length=100,
        verbose_name="Αγγλική Ονομασία"
    )
    display_order = models.IntegerField(
        default=0,
        verbose_name="Σειρά Εμφάνισης"
    )
    
    class Meta:
        verbose_name = "Κατηγορία Άδειας Οδήγησης"
        verbose_name_plural = "Κατηγορίες Αδειών Οδήγησης"
        ordering = ['display_order', 'code']
    
    def __str__(self):
        return f"{self.code} - {self.label_el}"


class AdrCategory(models.Model):
    """
    ADR Categories for Dangerous Goods (Π1-Π9)
    Bilingual lookup table
    """
    code = models.CharField(
        max_length=10,
        unique=True,
        verbose_name="Κωδικός ADR",
        help_text="π.χ. Π1, Π2, Π3, Π4, Π5, Π6, Π7, Π8, Π9"
    )
    label_el = models.CharField(
        max_length=200,
        verbose_name="Ελληνική Περιγραφή"
    )
    label_en = models.CharField(
        max_length=200,
        verbose_name="Αγγλική Περιγραφή"
    )
    display_order = models.IntegerField(
        default=0,
        verbose_name="Σειρά Εμφάνισης"
    )
    
    class Meta:
        verbose_name = "Κατηγορία ADR"
        verbose_name_plural = "Κατηγορίες ADR"
        ordering = ['display_order', 'code']
    
    def __str__(self):
        return f"{self.code} - {self.label_el}"


class DriverCompliance(models.Model):
    """
    Driver Compliance & Credentials
    Tracks all required documents and certifications for professional drivers
    
    OneToOne with Employee (only for drivers)
    Tenant-scoped via Employee.company relationship
    """
    employee = models.OneToOneField(
        'core.Employee',
        on_delete=models.CASCADE,
        related_name='driver_compliance',
        verbose_name="Υπάλληλος",
        limit_choices_to={'position__is_driver_role': True}
    )
    
    # ========== DRIVING LICENSE ==========
    license_number = models.CharField(
        max_length=20,
        verbose_name="Αριθμός Άδειας Οδήγησης"
    )
    license_issue_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="Ημερομηνία Έκδοσης Άδειας"
    )
    license_expiry_date = models.DateField(
        verbose_name="Ημερομηνία Λήξης Άδειας"
    )
    license_categories = models.ManyToManyField(
        DrivingLicenseCategory,
        related_name='drivers',
        verbose_name="Κατηγορίες Άδειας",
        help_text="π.χ. B, C, CE, D, DE"
    )
    
    # ========== ΠΕΙ (Professional Competence Certificate) ==========
    pei_truck_expiry = models.DateField(
        null=True,
        blank=True,
        verbose_name="Λήξη ΠΕΙ Φορτηγών",
        help_text="Πιστοποιητικό Επαγγελματικής Ικανότητας για φορτηγά"
    )
    pei_bus_expiry = models.DateField(
        null=True,
        blank=True,
        verbose_name="Λήξη ΠΕΙ Λεωφορείων",
        help_text="Πιστοποιητικό Επαγγελματικής Ικανότητας για λεωφορεία"
    )
    
    # ========== TACHOGRAPH (Digital Driver Card) ==========
    tachograph_card_number = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="Αριθμός Κάρτας Ψηφιακού Ταχογράφου"
    )
    tachograph_card_expiry = models.DateField(
        null=True,
        blank=True,
        verbose_name="Λήξη Κάρτας Ταχογράφου"
    )
    
    # ========== ADR (Dangerous Goods) ==========
    adr_categories = models.ManyToManyField(
        AdrCategory,
        blank=True,
        related_name='drivers',
        verbose_name="Κατηγορίες ADR",
        help_text="Πιστοποίηση μεταφοράς επικίνδυνων εμπορευμάτων"
    )
    adr_expiry = models.DateField(
        null=True,
        blank=True,
        verbose_name="Λήξη ADR"
    )
    
    # ========== METADATA ==========
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Συμμόρφωση Οδηγού"
        verbose_name_plural = "Συμμορφώσεις Οδηγών"
        ordering = ['employee__last_name', 'employee__first_name']
    
    def __str__(self):
        return f"{self.employee.full_name} - Άδεια: {self.license_number}"
    
    def is_license_valid(self, check_date=None):
        """
        Check if driving license is valid on a specific date
        
        Args:
            check_date: Date to check (default: today)
        
        Returns:
            bool: True if license is valid
        """
        from django.utils import timezone
        if check_date is None:
            check_date = timezone.now().date()
        
        return self.license_expiry_date >= check_date
    
    def is_pei_truck_valid(self, check_date=None):
        """
        Check if PEI for trucks is valid
        
        Args:
            check_date: Date to check (default: today)
        
        Returns:
            bool: True if PEI is valid, False if missing or expired
        """
        from django.utils import timezone
        if not self.pei_truck_expiry:
            return False
        
        if check_date is None:
            check_date = timezone.now().date()
        
        return self.pei_truck_expiry >= check_date
    
    def is_pei_bus_valid(self, check_date=None):
        """
        Check if PEI for buses is valid
        
        Args:
            check_date: Date to check (default: today)
        
        Returns:
            bool: True if PEI is valid, False if missing or expired
        """
        from django.utils import timezone
        if not self.pei_bus_expiry:
            return False
        
        if check_date is None:
            check_date = timezone.now().date()
        
        return self.pei_bus_expiry >= check_date
    
    def is_tachograph_valid(self, check_date=None):
        """
        Check if tachograph card is valid
        
        Args:
            check_date: Date to check (default: today)
        
        Returns:
            bool: True if tachograph is valid, False if missing or expired
        """
        from django.utils import timezone
        if not self.tachograph_card_expiry:
            return False
        
        if check_date is None:
            check_date = timezone.now().date()
        
        return self.tachograph_card_expiry >= check_date
    
    def is_adr_valid(self, check_date=None):
        """
        Check if ADR certification is valid
        
        Args:
            check_date: Date to check (default: today)
        
        Returns:
            bool: True if ADR is valid, False if missing or expired
        """
        from django.utils import timezone
        if not self.adr_expiry:
            return False
        
        if check_date is None:
            check_date = timezone.now().date()
        
        return self.adr_expiry >= check_date
    
    def has_license_category(self, category_code):
        """
        Check if driver has a specific license category
        
        Args:
            category_code: License category code (e.g., 'C', 'CE', 'D')
        
        Returns:
            bool: True if driver has the category
        """
        return self.license_categories.filter(code=category_code).exists()
    
    def has_any_adr_category(self):
        """
        Check if driver has any ADR certification
        
        Returns:
            bool: True if driver has at least one ADR category
        """
        return self.adr_categories.exists()
