"""
Django Admin Configuration for Operations App
"""
from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import FuelEntry, ServiceLog, IncidentReport, Vehicle

# Import CompanyRestrictedAdmin from core
from core.admin import CompanyRestrictedAdmin


@admin.register(FuelEntry)
class FuelEntryAdmin(CompanyRestrictedAdmin):
    list_display = [
        'vehicle', 'date', 'liters', 'cost_per_liter', 'total_cost',
        'is_full_tank', 'odometer_reading', 'driver', 'company'
    ]
    list_filter = ['company', 'is_full_tank', 'date', 'vehicle']
    search_fields = ['vehicle__plate', 'driver__user__first_name', 'driver__user__last_name', 'fuel_station_name']
    date_hierarchy = 'date'
    ordering = ['-date', '-created_at']
    
    fieldsets = (
        ('Βασικές Πληροφορίες', {
            'fields': ('company', 'vehicle', 'driver', 'date', 'fuel_station_name')
        }),
        ('Καύσιμο', {
            'fields': ('liters', 'cost_per_liter', 'total_cost', 'is_full_tank', 'odometer_reading')
        }),
        ('AdBlue', {
            'fields': ('adblue_liters', 'adblue_cost'),
            'classes': ('collapse',)
        }),
        ('Σημειώσεις', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    def get_queryset(self, request):
        """Override to use all_objects for superusers"""
        if request.user.is_superuser:
            return self.model.all_objects.all()
        return self.model.objects.all()
    
    def has_change_permission(self, request, obj=None):
        """Verify user can only change their company's records"""
        if request.user.is_superuser:
            return True
        if obj and hasattr(request, 'company') and obj.company != request.company:
            return False
        return super().has_change_permission(request, obj)
    
    def has_delete_permission(self, request, obj=None):
        """Verify user can only delete their company's records"""
        if request.user.is_superuser:
            return True
        if obj and hasattr(request, 'company') and obj.company != request.company:
            return False
        return super().has_delete_permission(request, obj)
    
    def save_model(self, request, obj, form, change):
        """Auto-set company for new records"""
        if not obj.pk and hasattr(request, 'company'):
            obj.company = request.company
        super().save_model(request, obj, form, change)


@admin.register(ServiceLog)
class ServiceLogAdmin(CompanyRestrictedAdmin):
    list_display = [
        'vehicle', 'date', 'service_type', 'odometer_reading',
        'total_cost', 'invoice_number', 'company'
    ]
    list_filter = ['company', 'service_type', 'date', 'vehicle']
    search_fields = ['vehicle__plate', 'invoice_number', 'description']
    date_hierarchy = 'date'
    ordering = ['-date', '-created_at']
    
    fieldsets = (
        ('Βασικές Πληροφορίες', {
            'fields': ('company', 'vehicle', 'date', 'service_type', 'odometer_reading')
        }),
        ('Κόστος', {
            'fields': ('cost_parts', 'cost_labor', 'total_cost')
        }),
        ('Τεκμηρίωση', {
            'fields': ('description', 'invoice_number', 'invoice_attachment')
        }),
        ('Σημειώσεις', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    def get_queryset(self, request):
        """Override to use all_objects for superusers"""
        if request.user.is_superuser:
            return self.model.all_objects.all()
        return self.model.objects.all()
    
    def has_change_permission(self, request, obj=None):
        """Verify user can only change their company's records"""
        if request.user.is_superuser:
            return True
        if obj and hasattr(request, 'company') and obj.company != request.company:
            return False
        return super().has_change_permission(request, obj)
    
    def has_delete_permission(self, request, obj=None):
        """Verify user can only delete their company's records"""
        if request.user.is_superuser:
            return True
        if obj and hasattr(request, 'company') and obj.company != request.company:
            return False
        return super().has_delete_permission(request, obj)
    
    def save_model(self, request, obj, form, change):
        """Auto-set company for new records"""
        if not obj.pk and hasattr(request, 'company'):
            obj.company = request.company
        super().save_model(request, obj, form, change)


@admin.register(IncidentReport)
class IncidentReportAdmin(CompanyRestrictedAdmin):
    list_display = [
        'vehicle', 'date', 'type', 'location', 'driver',
        'cost_estimate', 'is_resolved', 'company'
    ]
    list_filter = ['company', 'type', 'is_resolved', 'date', 'vehicle']
    search_fields = ['vehicle__plate', 'driver__user__first_name', 'driver__user__last_name', 'location', 'description']
    date_hierarchy = 'date'
    ordering = ['-date', '-created_at']
    
    fieldsets = (
        ('Βασικές Πληροφορίες', {
            'fields': ('company', 'vehicle', 'driver', 'date', 'type')
        }),
        ('Λεπτομέρειες Συμβάντος', {
            'fields': ('location', 'description', 'cost_estimate')
        }),
        ('Τεκμηρίωση', {
            'fields': ('police_report_number', 'photos')
        }),
        ('Κατάσταση', {
            'fields': ('is_resolved', 'resolution_notes')
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    actions = ['mark_as_resolved']
    
    def mark_as_resolved(self, request, queryset):
        """
        Admin action to mark selected incidents as resolved
        """
        updated = queryset.update(is_resolved=True)
        self.message_user(request, f'{updated} συμβάντα επισημάνθηκαν ως επιλυμένα.')
    mark_as_resolved.short_description = "Επισήμανση ως επιλυμένα"


@admin.register(Vehicle)
class VehicleAdmin(CompanyRestrictedAdmin):
    list_display = [
        'license_plate', 'make', 'model', 'vehicle_class', 'body_type', 'fuel_type',
        'status', 'company', 'get_current_value', 'get_annual_depreciation', 'get_hourly_rate'
    ]
    list_filter = ['company', 'vehicle_class', 'body_type', 'status', 'fuel_type', 'emission_class']
    search_fields = ['license_plate', 'vin', 'make', 'model']
    ordering = ['license_plate']
    
    fieldsets = (
        ('Ταυτότητα (Από Άδεια Κυκλοφορίας)', {
            'fields': ('company', 'license_plate', 'vin', 'make', 'model', 'color', 'manufacturing_year', 'first_registration_date', 'acquisition_date'),
            'description': 'Στοιχεία από την επίσημη άδεια κυκλοφορίας με κωδικούς A, B, D.1, D.2, E, R'
        }),
        ('Κατηγοριοποίηση', {
            'fields': ('vehicle_class', 'body_type')
        }),
        ('Εξωτερικές Διαστάσεις (Routing)', {
            'fields': ('length_total_m', 'width_m', 'height_m'),
            'classes': ('collapse',)
        }),
        ('Εσωτερικές Διαστάσεις Φορτίου', {
            'fields': ('cargo_length_m', 'cargo_width_m', 'cargo_height_m'),
            'classes': ('collapse',),
            'description': 'Εσωτερικός χώρος φορτίου για υπολογισμό όγκου'
        }),
        ('Βάρη (F.1, G)', {
            'fields': ('gross_weight_kg', 'unladen_weight_kg'),
            'classes': ('collapse',),
            'description': 'Κωδικοί F.1 (Μικτό) και G (Απόβαρο) από άδεια'
        }),
        ('Ισχύς & Ενέργεια (P.1, P.2, P.3)', {
            'fields': ('horsepower', 'engine_capacity_cc', 'fuel_type', 'emission_class', 'tank_capacity'),
            'classes': ('collapse',),
            'description': 'Κωδικοί P.1 (Κυβισμός), P.2 (HP), P.3 (Καύσιμο)'
        }),
        ('Χωρητικότητα (S.1)', {
            'fields': ('seats',),
            'classes': ('collapse',),
            'description': 'Κωδικός S.1 - Θέσεις επιβατών'
        }),
        ('Οικονομικά (Αυτόματη Απόσβεση 16%)', {
            'fields': ('purchase_value', 'available_hours_per_year'),
            'description': 'Απόσβεση υπολογίζεται αυτόματα με 16% ετησίως από acquisition_date'
        }),
        ('Κατάσταση & Χρήση', {
            'fields': ('status', 'current_odometer', 'last_service_km')
        }),
        ('Σημειώσεις', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    def get_current_value(self, obj):
        """Display current accounting value"""
        return f"€{obj.current_accounting_value:,.2f}"
    get_current_value.short_description = "Τρέχουσα Αξία"
    
    def get_annual_depreciation(self, obj):
        return f"€{obj.annual_depreciation:,.2f}"
    get_annual_depreciation.short_description = "Ετήσια Απόσβεση (16%)"
    
    def get_hourly_rate(self, obj):
        return f"€{obj.fixed_cost_per_hour:,.2f}/ώρα"
    get_hourly_rate.short_description = "Ωριαίο Κόστος"
