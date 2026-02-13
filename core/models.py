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
    
    is_active = models.BooleanField(default=True, verbose_name="Ενεργή")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Εταιρεία"
        verbose_name_plural = "Εταιρείες"
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.tax_id})"


class VehicleAsset(PolymorphicModel):
    """
    Abstract Base Model for all Vehicle Types
    Uses django-polymorphic for inheritance
    """
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='vehicles',
        verbose_name="Εταιρεία"
    )
    
    # Identity
    plate = models.CharField(max_length=20, unique=True, verbose_name="Πινακίδα")
    vin = models.CharField(max_length=17, unique=True, blank=True, null=True, verbose_name="VIN")
    make = models.CharField(max_length=50, verbose_name="Μάρκα")
    model = models.CharField(max_length=50, verbose_name="Μοντέλο")
    year = models.PositiveIntegerField(
        validators=[MinValueValidator(1900), MaxValueValidator(2100)],
        verbose_name="Έτος Κατασκευής"
    )
    
    # Financial
    purchase_date = models.DateField(verbose_name="Ημ/νία Αγοράς")
    purchase_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name="Τιμή Αγοράς (€)"
    )
    
    # Compliance
    insurance_expiry = models.DateField(verbose_name="Λήξη Ασφάλισης")
    kteo_expiry = models.DateField(verbose_name="Λήξη ΚΤΕΟ")
    circulation_tax_expiry = models.DateField(null=True, blank=True, verbose_name="Λήξη Τελών Κυκλοφορίας")
    
    # Status
    STATUS_CHOICES = [
        ('ACTIVE', 'Ενεργό'),
        ('MAINTENANCE', 'Σε Συντήρηση'),
        ('INACTIVE', 'Ανενεργό'),
        ('SOLD', 'Πωλήθηκε'),
    ]
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='ACTIVE',
        verbose_name="Κατάσταση"
    )
    
    # Odometer
    current_odometer = models.PositiveIntegerField(
        default=0,
        verbose_name="Τρέχον Χιλιόμετρα"
    )
    
    # Metadata
    notes = models.TextField(blank=True, verbose_name="Σημειώσεις")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Όχημα"
        verbose_name_plural = "Οχήματα"
        ordering = ['plate']
    
    def __str__(self):
        return f"{self.plate} - {self.make} {self.model}"


class Truck(VehicleAsset):
    """
    Heavy Transport Vehicle (ΦΔΧ/ΦΙΧ)
    """
    TRUCK_TYPES = [
        ('RIGID', 'Φορτηγό Άκαμπτο'),
        ('ARTICULATED', 'Νταλίκα'),
        ('TANKER', 'Βυτιοφόρο'),
        ('REFRIGERATED', 'Ψυγείο'),
    ]
    truck_type = models.CharField(
        max_length=20,
        choices=TRUCK_TYPES,
        default='RIGID',
        verbose_name="Τύπος Φορτηγού"
    )
    
    # Tachograph
    tachograph_calibration_date = models.DateField(null=True, blank=True, verbose_name="Ημ/νία Βαθμονόμησης Ταχογράφου")
    
    # ADR (Dangerous Goods)
    is_adr = models.BooleanField(default=False, verbose_name="Έχει ADR")
    
    # Axle Configuration
    axles_count = models.PositiveIntegerField(default=2, verbose_name="Αριθμός Αξόνων")
    
    class Meta:
        verbose_name = "Φορτηγό"
        verbose_name_plural = "Φορτηγά"


class Bus(VehicleAsset):
    """
    Passenger Transport Vehicle (Public/Private/Tourism)
    """
    BUS_TYPES = [
        ('URBAN', 'Αστικό'),
        ('INTERCITY', 'Υπεραστικό'),
        ('TOUR', 'Τουριστικό'),
        ('SCHOOL', 'Σχολικό'),
        ('MINIVAN', 'Minivan'),
    ]
    bus_type = models.CharField(
        max_length=20,
        choices=BUS_TYPES,
        default='TOUR',
        verbose_name="Τύπος Λεωφορείου"
    )
    
    # Passenger Capacity
    seat_count = models.PositiveIntegerField(verbose_name="Αριθμός Θέσεων")
    
    # Amenities
    has_toilet = models.BooleanField(default=False, verbose_name="WC")
    is_tourist_bus = models.BooleanField(default=False, verbose_name="Τουριστικό Λεωφορείο")
    
    class Meta:
        verbose_name = "Λεωφορείο"
        verbose_name_plural = "Λεωφορεία"


class Taxi(VehicleAsset):
    """
    Taxi Vehicle
    """
    # Taxi Specific
    taximeter_serial = models.CharField(max_length=50, verbose_name="Σειριακός Ταξιμέτρου")
    
    LICENSE_TYPES = [
        ('EDRAS', 'Έδρας'),
        ('AGORAS', 'Αγοράς'),
    ]
    license_type_edras = models.CharField(
        max_length=10,
        choices=LICENSE_TYPES,
        default='EDRAS',
        verbose_name="Τύπος Άδειας"
    )
    
    class Meta:
        verbose_name = "Ταξί"
        verbose_name_plural = "Ταξί"


class PassengerCar(VehicleAsset):
    """
    Passenger Cars (Sales, Corporate Fleet)
    """
    CAR_TYPES = [
        ('SEDAN', 'Sedan'),
        ('HATCHBACK', 'Hatchback'),
        ('SUV', 'SUV'),
        ('STATION_WAGON', 'Station Wagon'),
    ]
    car_type = models.CharField(
        max_length=20,
        choices=CAR_TYPES,
        default='SEDAN',
        verbose_name="Τύπος Αυτοκινήτου"
    )
    
    # Leasing (for Corporate Fleet)
    leasing_contract_end = models.DateField(null=True, blank=True, verbose_name="Λήξη Σύμβασης Leasing")
    
    # Benefit-in-Kind Tax
    bik_value = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Φορολογητέα Αξία BiK (€)"
    )
    
    class Meta:
        verbose_name = "Επιβατικό Αυτοκίνητο"
        verbose_name_plural = "Επιβατικά Αυτοκίνητα"


class Moto(VehicleAsset):
    """
    Motorcycles/Scooters (Delivery/Courier)
    """
    MOTO_TYPES = [
        ('SCOOTER', 'Scooter'),
        ('MOTORCYCLE', 'Μοτοσυκλέτα'),
        ('DELIVERY', 'Delivery Bike'),
    ]
    moto_type = models.CharField(
        max_length=20,
        choices=MOTO_TYPES,
        default='SCOOTER',
        verbose_name="Τύπος Μοτοσυκλέτας"
    )
    
    engine_cc = models.PositiveIntegerField(verbose_name="Κυβικά (cc)")
    
    # Delivery Specific
    box_capacity_liters = models.PositiveIntegerField(default=0, verbose_name="Χωρητικότητα Box (λίτρα)")
    
    class Meta:
        verbose_name = "Μοτοσυκλέτα"
        verbose_name_plural = "Μοτοσυκλέτες"


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
        'VehicleAsset',
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
