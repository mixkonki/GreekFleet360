"""
Django Admin Configuration for GreekFleet 360
"""
from django.contrib import admin
from unfold.admin import ModelAdmin
from polymorphic.admin import PolymorphicParentModelAdmin, PolymorphicChildModelAdmin
from .models import Company, VehicleAsset, Truck, Bus, Taxi, PassengerCar, Moto, DriverProfile

# Customize Admin Site
# Note: Unfold handles site customization through settings.py


@admin.register(Company)
class CompanyAdmin(ModelAdmin):
    list_display = ['name', 'tax_id', 'business_type', 'is_active', 'created_at']
    list_filter = ['business_type', 'is_active']
    search_fields = ['name', 'tax_id']
    ordering = ['name']


class TruckAdmin(PolymorphicChildModelAdmin):
    base_model = Truck
    list_display = ['plate', 'make', 'model', 'truck_type', 'company', 'status']
    list_filter = ['truck_type', 'status', 'is_adr']
    search_fields = ['plate', 'vin', 'make', 'model']


class BusAdmin(PolymorphicChildModelAdmin):
    base_model = Bus
    list_display = ['plate', 'make', 'model', 'bus_type', 'seat_count', 'company', 'status']
    list_filter = ['bus_type', 'status', 'has_toilet', 'is_tourist_bus']
    search_fields = ['plate', 'vin', 'make', 'model']


class TaxiAdmin(PolymorphicChildModelAdmin):
    base_model = Taxi
    list_display = ['plate', 'make', 'model', 'taximeter_serial', 'license_type_edras', 'company', 'status']
    list_filter = ['license_type_edras', 'status']
    search_fields = ['plate', 'vin', 'make', 'model', 'taximeter_serial']


class PassengerCarAdmin(PolymorphicChildModelAdmin):
    base_model = PassengerCar
    list_display = ['plate', 'make', 'model', 'car_type', 'company', 'status']
    list_filter = ['car_type', 'status']
    search_fields = ['plate', 'vin', 'make', 'model']


class MotoAdmin(PolymorphicChildModelAdmin):
    base_model = Moto
    list_display = ['plate', 'make', 'model', 'moto_type', 'engine_cc', 'company', 'status']
    list_filter = ['moto_type', 'status']
    search_fields = ['plate', 'vin', 'make', 'model']


@admin.register(VehicleAsset)
class VehicleAssetAdmin(PolymorphicParentModelAdmin):
    base_model = VehicleAsset
    child_models = (Truck, Bus, Taxi, PassengerCar, Moto)
    list_display = ['plate', 'make', 'model', 'company', 'status', 'current_odometer']
    list_filter = ['status', 'company']
    search_fields = ['plate', 'vin', 'make', 'model']


@admin.register(DriverProfile)
class DriverProfileAdmin(ModelAdmin):
    list_display = ['user', 'license_number', 'company', 'license_categories', 'is_active']
    list_filter = ['is_active', 'company']
    search_fields = ['user__first_name', 'user__last_name', 'license_number', 'phone']
    ordering = ['user__last_name', 'user__first_name']
    
    fieldsets = (
        ('Βασικές Πληροφορίες', {
            'fields': ('user', 'company', 'phone', 'address', 'date_of_birth')
        }),
        ('Άδεια Οδήγησης', {
            'fields': ('license_categories', 'license_number', 'license_issue_date', 'license_expiry_date', 'license_points')
        }),
        ('ΠΕΙ & Ιατρική', {
            'fields': ('cpc_expiry', 'medical_card_expiry')
        }),
        ('Απασχόληση', {
            'fields': ('hire_date', 'is_active', 'notes')
        }),
    )


