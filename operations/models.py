"""
Operations Models for GreekFleet 360
Fuel, Service, and Incident Tracking
"""
from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal
from core.models import Company, VehicleAsset, DriverProfile


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
    vehicle = models.ForeignKey(
        VehicleAsset,
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
    vehicle = models.ForeignKey(
        VehicleAsset,
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
        VehicleAsset,
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
