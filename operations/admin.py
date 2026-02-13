"""
Django Admin Configuration for Operations App
"""
from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import FuelEntry, ServiceLog, IncidentReport


@admin.register(FuelEntry)
class FuelEntryAdmin(ModelAdmin):
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


@admin.register(ServiceLog)
class ServiceLogAdmin(ModelAdmin):
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


@admin.register(IncidentReport)
class IncidentReportAdmin(ModelAdmin):
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
