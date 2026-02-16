"""
Operations Models for GreekFleet 360
Fuel, Service, and Incident Tracking
"""
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
from core.models import Company, DriverProfile
from core.mixins import CompanyScopedManager


class FuelEntry(models.Model):
    """
    Fuel Purchase Entry
    Tracks every fuel transaction for accurate consumption analysis
    """
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='fuel_entries',
        verbose_name="Εταιρεία"
    )
    
    # Tenant Isolation Managers
    objects = CompanyScopedManager()
    all_objects = models.Manager()
    vehicle = models.ForeignKey(
        'Vehicle',
        on_delete=models.CASCADE,
        related_name='fuel_entries',
        verbose_name="Όχημα"
    )
    driver = models.ForeignKey(
        DriverProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='fuel_entries',
        verbose_name="Οδηγός"
    )
    
    # Transaction Details
    date = models.DateField(verbose_name="Ημερομηνία")
    fuel_station_name = models.CharField(max_length=100, blank=True, verbose_name="Πρατήριο")
    
    # Fuel Details
    liters = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name="Λίτρα"
    )
    cost_per_liter = models.DecimalField(
        max_digits=6,
        decimal_places=3,
        validators=[MinValueValidator(Decimal('0.001'))],
        verbose_name="Τιμή/Λίτρο (€)"
    )
    total_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name="Συνολικό Κόστος (€)"
    )
    
    # Consumption Tracking
    is_full_tank = models.BooleanField(
        default=False,
        verbose_name="Γέμισμα Ρεζερβουάρ",
        help_text="Κρίσιμο για ακριβή υπολογισμό κατανάλωσης"
    )
    odometer_reading = models.PositiveIntegerField(verbose_name="Ένδειξη Χιλιομετρητή")
    
    # AdBlue (for Trucks/Buses)
    adblue_liters = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name="AdBlue Λίτρα"
    )
    adblue_cost = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name="AdBlue Κόστος (€)"
    )
    
    # Metadata
    notes = models.TextField(blank=True, verbose_name="Σημειώσεις")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Καταχώρηση Καυσίμου"
        verbose_name_plural = "Καταχωρήσεις Καυσίμων"
        ordering = ['-date', '-created_at']
        indexes = [
            models.Index(fields=['vehicle', '-date']),
            models.Index(fields=['company', '-date']),
        ]
    
    def __str__(self):
        return f"{self.vehicle.plate} - {self.date} - {self.liters}L"
    
    def save(self, *args, **kwargs):
        # Auto-calculate total_cost if not provided
        if not self.total_cost:
            self.total_cost = self.liters * self.cost_per_liter
        super().save(*args, **kwargs)


class ServiceLog(models.Model):
    """
    Service and Maintenance Log
    Tracks all maintenance, repairs, and inspections
    """
    SERVICE_TYPES = [
        ('REGULAR', 'Τακτική Συντήρηση'),
        ('REPAIR', 'Επισκευή'),
        ('TIRE_CHANGE', 'Αλλαγή Ελαστικών'),
        ('KTEO', 'Έλεγχος ΚΤΕΟ'),
        ('TACHOGRAPH', 'Βαθμονόμηση Ταχογράφου'),
    ]
    
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='service_logs',
        verbose_name="Εταιρεία"
    )
    
    # Tenant Isolation Managers
    objects = CompanyScopedManager()
    all_objects = models.Manager()
    vehicle = models.ForeignKey(
        'Vehicle',
        on_delete=models.CASCADE,
        related_name='service_logs',
        verbose_name="Όχημα"
    )
    
    # Service Details
    date = models.DateField(verbose_name="Ημερομηνία")
    service_type = models.CharField(
        max_length=20,
        choices=SERVICE_TYPES,
        verbose_name="Τύπος Εργασίας"
    )
    odometer_reading = models.PositiveIntegerField(verbose_name="Ένδειξη Χιλιομετρητή")
    
    # Cost Breakdown
    cost_parts = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name="Κόστος Ανταλλακτικών (€)"
    )
    cost_labor = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name="Κόστος Εργασίας (€)"
    )
    total_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name="Συνολικό Κόστος (€)"
    )
    
    # Documentation
    description = models.TextField(verbose_name="Περιγραφή Εργασιών")
    invoice_number = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Αριθμός Τιμολογίου"
    )
    invoice_attachment = models.FileField(
        upload_to='service_invoices/%Y/%m/',
        blank=True,
        null=True,
        verbose_name="Συνημμένο Τιμολόγιο"
    )
    
    # Metadata
    notes = models.TextField(blank=True, verbose_name="Σημειώσεις Μηχανικού")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Καταχώρηση Συντήρησης"
        verbose_name_plural = "Καταχωρήσεις Συντήρησης"
        ordering = ['-date', '-created_at']
        indexes = [
            models.Index(fields=['vehicle', '-date']),
            models.Index(fields=['company', '-date']),
            models.Index(fields=['service_type']),
        ]
    
    def __str__(self):
        return f"{self.vehicle.plate} - {self.get_service_type_display()} - {self.date}"
    
    def save(self, *args, **kwargs):
        # Auto-calculate total_cost if not provided
        if not self.total_cost:
            self.total_cost = self.cost_parts + self.cost_labor
        super().save(*args, **kwargs)


class IncidentReport(models.Model):
    """
    Incident and Fine Tracking
    Records accidents, traffic fines, and breakdowns
    """
    INCIDENT_TYPES = [
        ('ACCIDENT', 'Ατύχημα'),
        ('FINE', 'Κλήση Τροχαίας'),
        ('BREAKDOWN', 'Βλάβη'),
    ]
    
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='incidents',
        verbose_name="Εταιρεία"
    )
    vehicle = models.ForeignKey(
        'Vehicle',
        on_delete=models.CASCADE,
        related_name='incidents',
        verbose_name="Όχημα"
    )
    driver = models.ForeignKey(
        DriverProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='incidents',
        verbose_name="Οδηγός"
    )
    
    # Incident Details
    date = models.DateField(verbose_name="Ημερομηνία")
    type = models.CharField(
        max_length=20,
        choices=INCIDENT_TYPES,
        verbose_name="Τύπος Συμβάντος"
    )
    location = models.CharField(max_length=200, verbose_name="Τοποθεσία")
    description = models.TextField(verbose_name="Περιγραφή")
    
    # Cost
    cost_estimate = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name="Εκτίμηση Κόστους (€)"
    )
    
    # Documentation
    police_report_number = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Αριθμός Δελτίου Τροχαίας"
    )
    photos = models.FileField(
        upload_to='incident_photos/%Y/%m/',
        blank=True,
        null=True,
        verbose_name="Φωτογραφίες"
    )
    
    # Status
    is_resolved = models.BooleanField(default=False, verbose_name="Επιλύθηκε")
    resolution_notes = models.TextField(blank=True, verbose_name="Σημειώσεις Επίλυσης")
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Αναφορά Συμβάντος"
        verbose_name_plural = "Αναφορές Συμβάντων"
        ordering = ['-date', '-created_at']
        indexes = [
            models.Index(fields=['vehicle', '-date']),
            models.Index(fields=['company', '-date']),
            models.Index(fields=['type', 'is_resolved']),
        ]
    
    def __str__(self):
        return f"{self.vehicle.plate} - {self.get_type_display()} - {self.date}"


class Vehicle(models.Model):
    """
    Unified Vehicle Model - Single Source of Truth
    Phase 4: Aligned with Official Registration Certificate (Άδεια Κυκλοφορίας)
    Automated 16% annual depreciation based on acquisition date
    """
    
    # Depreciation Constant (16% annual rate)
    ANNUAL_DEPRECIATION_RATE = Decimal('0.16')
    
    # ========== ENUMS / CHOICES ==========
    
    class VehicleClass(models.TextChoices):
        """Vehicle Classification - Defines operational capabilities"""
        TRACTOR = 'TRACTOR', 'Ελκυστήρας (Tractor)'
        TRUCK = 'TRUCK', 'Φορτηγό (Rigid Truck)'
        SEMI_TRAILER = 'SEMI_TRAILER', 'Ημιρυμουλκούμενο (Semi-Trailer)'
        TRAILER = 'TRAILER', 'Ρυμουλκούμενο (Trailer)'
        BUS = 'BUS', 'Λεωφορείο (Bus)'
        VAN = 'VAN', 'Βαν / Ελαφρύ Φορτηγό (Van)'
        CAR = 'CAR', 'Επιβατικό (Passenger Car)'
    
    class BodyType(models.TextChoices):
        """Body Type - Physical cargo area configuration"""
        TRACTOR_UNIT = 'TRACTOR_UNIT', 'Μονάδα Ελκυστήρα (Tractor Unit)'
        CURTAIN = 'CURTAIN', 'Κουρτίνα (Curtain Sider)'
        BOX = 'BOX', 'Κόφα (Box/Van Body)'
        FLATBED = 'FLATBED', 'Πλατφόρμα/Ανοιχτό (Flatbed)'
        REFRIGERATOR = 'REFRIGERATOR', 'Ψυγείο (Refrigerated)'
        TANKER = 'TANKER', 'Βυτίο (Tanker)'
        TIPPER = 'TIPPER', 'Ανατρεπόμενο (Tipper/Dump)'
        CONTAINER_CHASSIS = 'CONTAINER_CHASSIS', 'Βάση Κοντέινερ (Container Chassis)'
        CAR_CARRIER = 'CAR_CARRIER', 'Αυτοκινητάμαξα (Car Carrier)'
        BUS_BODY = 'BUS_BODY', 'Αμάξωμα Λεωφορείου (Bus Body)'
        OTHER = 'OTHER', 'Άλλο / Ειδικό (Other/Special)'
    
    class FuelType(models.TextChoices):
        """Fuel/Energy Type"""
        DIESEL = 'DIESEL', 'Πετρέλαιο (Diesel)'
        PETROL = 'PETROL', 'Βενζίνη (Petrol/Gasoline)'
        ELECTRIC = 'ELECTRIC', 'Ηλεκτρικό (Electric)'
        GAS = 'GAS', 'Φυσικό Αέριο (CNG/LNG)'
        HYBRID = 'HYBRID', 'Υβριδικό (Hybrid)'
    
    class EmissionClass(models.TextChoices):
        """Euro Emission Standards - Critical for international tolls"""
        EURO_3 = 'EURO_3', 'Euro 3'
        EURO_4 = 'EURO_4', 'Euro 4'
        EURO_5 = 'EURO_5', 'Euro 5'
        EURO_6 = 'EURO_6', 'Euro 6'
        EURO_6C = 'EURO_6C', 'Euro 6c'
        EURO_6D = 'EURO_6D', 'Euro 6d'
        ELECTRIC_ZERO = 'ELECTRIC_ZERO', 'Μηδενικές Εκπομπές (Electric/Zero)'
    
    class Status(models.TextChoices):
        """Operational Status"""
        ACTIVE = 'ACTIVE', 'Ενεργό'
        INACTIVE = 'INACTIVE', 'Ανενεργό'
        SOLD = 'SOLD', 'Πωλήθηκε'
    
    # ========== SECTION 1: IDENTITY (From Registration Certificate) ==========
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='fleet_vehicles',
        verbose_name="Εταιρεία"
    )
    license_plate = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="Αριθμός Κυκλοφορίας (A)",
        help_text="Κωδικός A από την άδεια κυκλοφορίας"
    )
    vin = models.CharField(
        max_length=17,
        unique=True,
        blank=True,
        null=True,
        verbose_name="Αριθμός Πλαισίου (E)",
        help_text="Κωδικός E - 17-ψήφιος αριθμός πλαισίου"
    )
    make = models.CharField(
        max_length=50,
        verbose_name="Μάρκα (D.1)",
        help_text="Κωδικός D.1 από την άδεια"
    )
    model = models.CharField(
        max_length=50,
        verbose_name="Τύπος/Μοντέλο (D.2)",
        help_text="Κωδικός D.2 από την άδεια"
    )
    color = models.CharField(
        max_length=30,
        blank=True,
        verbose_name="Χρώμα (R)",
        help_text="Κωδικός R από την άδεια"
    )
    manufacturing_year = models.PositiveIntegerField(
        default=2020,
        validators=[MinValueValidator(1900), MaxValueValidator(2100)],
        verbose_name="Έτος Κατασκευής"
    )
    first_registration_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="Ημερομηνία Πρώτης Άδειας (B)",
        help_text="Κωδικός B - Ημερομηνία πρώτης άδειας κυκλοφορίας"
    )
    acquisition_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="Ημερομηνία Απόκτησης από Εταιρεία",
        help_text="Ημερομηνία που η εταιρεία αγόρασε το όχημα"
    )
    
    # ========== SECTION 2: CLASSIFICATION ==========
    vehicle_class = models.CharField(
        max_length=20,
        choices=VehicleClass.choices,
        verbose_name="Κλάση Οχήματος",
        help_text="Καθορίζει τις λειτουργικές δυνατότητες"
    )
    body_type = models.CharField(
        max_length=30,
        choices=BodyType.choices,
        verbose_name="Τύπος Αμαξώματος",
        help_text="Φυσική διαμόρφωση χώρου φορτίου"
    )
    
    # ========== SECTION 3: DIMENSIONS (Critical for Routing) ==========
    # External Dimensions
    length_total_m = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name="Συνολικό Μήκος (L)",
        help_text="Κωδικός L - Συμπεριλαμβανομένων προεξοχών"
    )
    width_m = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name="Πλάτος",
        help_text="Εξωτερικό πλάτος οχήματος"
    )
    height_m = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name="Ύψος",
        help_text="Κρίσιμο για γέφυρες και σήραγγες"
    )
    
    # Internal Cargo Dimensions
    cargo_length_m = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name="Μήκος Χώρου Φορτίου (m)",
        help_text="Εσωτερικό μήκος χώρου φορτίου"
    )
    cargo_width_m = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name="Πλάτος Χώρου Φορτίου (m)",
        help_text="Εσωτερικό πλάτος χώρου φορτίου"
    )
    cargo_height_m = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name="Ύψος Χώρου Φορτίου (m)",
        help_text="Εσωτερικό ύψος χώρου φορτίου"
    )
    
    # ========== SECTION 4: WEIGHTS (From Registration Certificate) ==========
    gross_weight_kg = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        verbose_name="Μικτό Βάρος (F.1)",
        help_text="Κωδικός F.1 - Μέγιστο επιτρεπόμενο βάρος"
    )
    unladen_weight_kg = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        verbose_name="Απόβαρο (G)",
        help_text="Κωδικός G - Βάρος κενού οχήματος"
    )
    
    # ========== SECTION 5: POWER & ENERGY ==========
    horsepower = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1)],
        verbose_name="Ιπποδύναμη (P.2)",
        help_text="Κωδικός P.2 - Ισχύς κινητήρα σε HP"
    )
    engine_capacity_cc = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1)],
        verbose_name="Κυβισμός Κινητήρα (P.1)",
        help_text="Κωδικός P.1 - Κυβισμός σε cm³"
    )
    fuel_type = models.CharField(
        max_length=20,
        choices=FuelType.choices,
        default=FuelType.DIESEL,
        verbose_name="Τύπος Καυσίμου (P.3)",
        help_text="Κωδικός P.3 από την άδεια"
    )
    emission_class = models.CharField(
        max_length=20,
        choices=EmissionClass.choices,
        null=True,
        blank=True,
        verbose_name="Κατηγορία Εκπομπών",
        help_text="Κρίσιμο για διεθνή διόδια και περιβαλλοντικές ζώνες"
    )
    tank_capacity = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name="Χωρητικότητα Ρεζερβουάρ (L/kWh)"
    )
    
    # ========== SECTION 6: CAPACITY ==========
    seats = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        verbose_name="Θέσεις Επιβατών (S.1)",
        help_text="Κωδικός S.1 - Για λεωφορεία και επιβατικά"
    )
    
    # ========== SECTION 7: FINANCIALS (Automated Depreciation) ==========
    purchase_value = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name="Αξία Αγοράς (€)",
        help_text="Αξία κατά την απόκτηση από την εταιρεία"
    )
    available_hours_per_year = models.IntegerField(
        default=1936,
        validators=[MinValueValidator(1)],
        verbose_name="Διαθέσιμες Ώρες/Έτος",
        help_text="1936 ώρες = 11 μήνες × 22 ημέρες × 8 ώρες"
    )
    
    # ========== SECTION 8: STATUS & USAGE ==========
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
        verbose_name="Κατάσταση"
    )
    current_odometer = models.PositiveIntegerField(
        default=0,
        verbose_name="Τρέχοντα Χιλιόμετρα"
    )
    last_service_km = models.PositiveIntegerField(
        default=0,
        verbose_name="Χιλιόμετρα Τελευταίας Συντήρησης"
    )
    
    # ========== FREIGHT COST INTELLIGENCE ==========
    average_fuel_consumption = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name="Μέση Κατανάλωση Καυσίμου (L/100km)",
        help_text="Υπολογίζεται από ιστορικό ή εισάγεται χειροκίνητα"
    )
    average_tire_cost_per_km = models.DecimalField(
        max_digits=6,
        decimal_places=4,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.0001'))],
        verbose_name="Μέσο Κόστος Ελαστικών ανά km (€/km)",
        help_text="Π.χ. 0.05 για 5 λεπτά ανά χιλιόμετρο"
    )
    
    
    # Metadata
    notes = models.TextField(blank=True, verbose_name="Σημειώσεις")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Όχημα"
        verbose_name_plural = "Οχήματα"
        ordering = ['license_plate']
        indexes = [
            models.Index(fields=['company', 'status']),
            models.Index(fields=['vehicle_class']),
            models.Index(fields=['license_plate']),
        ]
    
    def __str__(self):
        return f"{self.license_plate} - {self.make} {self.model}"
    
    @property
    def payload_capacity_kg(self):
        """
        Calculate payload capacity (Gross - Unladen)
        
        Returns:
            int: Payload capacity in kg, or None if data missing
        """
        if self.gross_weight_kg and self.unladen_weight_kg:
            return self.gross_weight_kg - self.unladen_weight_kg
        return None
    
    @property
    def current_accounting_value(self):
        """
        Calculate current accounting value using 16% annual depreciation
        Based on acquisition_date and purchase_value
        
        Returns:
            Decimal: Current accounting value
        """
        from datetime import date
        from dateutil.relativedelta import relativedelta
        
        if not self.acquisition_date or not self.purchase_value:
            return self.purchase_value
        
        # Calculate years since acquisition
        today = date.today()
        years_owned = relativedelta(today, self.acquisition_date).years
        months_owned = relativedelta(today, self.acquisition_date).months
        
        # Convert to decimal years (including months)
        total_years = Decimal(str(years_owned)) + (Decimal(str(months_owned)) / Decimal('12'))
        
        # Calculate depreciation: value * (1 - rate)^years
        depreciation_factor = (Decimal('1') - self.ANNUAL_DEPRECIATION_RATE) ** total_years
        current_value = self.purchase_value * depreciation_factor
        
        # Ensure value doesn't go below zero
        return max(current_value, Decimal('0.00'))
    
    @property
    def annual_depreciation(self):
        """
        Calculate annual depreciation at 16% rate
        
        Returns:
            Decimal: Annual depreciation amount
        """
        return self.purchase_value * self.ANNUAL_DEPRECIATION_RATE
    
    @property
    def fixed_cost_per_hour(self):
        """
        Calculate fixed cost per hour (Depreciation only - other costs in Expense system)
        
        Returns:
            Decimal: Fixed cost per available hour
        """
        if self.available_hours_per_year <= 0:
            return Decimal('0.00')
        
        return self.annual_depreciation / Decimal(str(self.available_hours_per_year))
    
    @property
    def cargo_volume_m3(self):
        """
        Calculate internal cargo volume in cubic meters
        
        Returns:
            Decimal: Cargo volume in m³, or None if dimensions missing
        """
        if self.cargo_length_m and self.cargo_width_m and self.cargo_height_m:
            return self.cargo_length_m * self.cargo_width_m * self.cargo_height_m
        return None
