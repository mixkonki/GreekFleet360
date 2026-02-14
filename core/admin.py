"""
Django Admin Configuration for GreekFleet 360
"""
from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from unfold.admin import ModelAdmin
from unfold.contrib.forms.widgets import WysiwygWidget
from polymorphic.admin import PolymorphicParentModelAdmin, PolymorphicChildModelAdmin
from .models import Company, VehicleAsset, Truck, Bus, Taxi, PassengerCar, Moto, DriverProfile, EmployeePosition, Employee

# Customize Admin Site
# Note: Unfold handles site customization through settings.py


# ============================================================================
# MULTI-TENANCY MIXIN
# ============================================================================

class CompanyRestrictedAdmin(ModelAdmin):
    """
    Base admin class for tenant-isolated models.
    Automatically filters queryset by company and hides company field for non-superusers.
    """
    
    def get_queryset(self, request):
        """
        Filter queryset by company for non-superusers
        """
        qs = super().get_queryset(request)
        
        # Superusers see everything
        if request.user.is_superuser:
            return qs
        
        # Regular users only see their company's data
        try:
            user_company = request.user.userprofile.company
            if user_company:
                return qs.filter(company=user_company)
        except:
            pass
        
        # If no company assigned, return empty queryset
        return qs.none()
    
    def save_model(self, request, obj, form, change):
        """
        Automatically set company for new objects
        """
        if not change and not request.user.is_superuser:
            # Only set company for new objects (not editing)
            try:
                if not obj.company:
                    obj.company = request.user.userprofile.company
            except:
                pass
        
        super().save_model(request, obj, form, change)
    
    def get_form(self, request, obj=None, **kwargs):
        """
        Hide company field for non-superusers
        """
        form = super().get_form(request, obj, **kwargs)
        
        if not request.user.is_superuser:
            # Remove company field from form for non-superusers
            if 'company' in form.base_fields:
                form.base_fields['company'].widget = admin.widgets.AdminTextInputWidget(attrs={'readonly': 'readonly'})
                form.base_fields['company'].disabled = True
        
        return form


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


@admin.register(EmployeePosition)
class EmployeePositionAdmin(ModelAdmin):
    list_display = ['title', 'is_driver_role']
    list_filter = ['is_driver_role']
    search_fields = ['title']
    ordering = ['title']


@admin.register(Employee)
class EmployeeAdmin(CompanyRestrictedAdmin):
    list_display = ['full_name', 'position', 'assigned_vehicle', 'company', 'is_active']
    list_filter = ['company', 'position', 'is_active']
    search_fields = ['first_name', 'last_name']
    ordering = ['last_name', 'first_name']
    
    fieldsets = (
        ('Βασικές Πληροφορίες', {
            'fields': ('first_name', 'last_name', 'position', 'company')
        }),
        ('Μισθοδοσία', {
            'fields': ('monthly_gross_salary', 'employer_contributions_rate', 'available_hours_per_year')
        }),
        ('Ανάθεση', {
            'fields': ('assigned_vehicle', 'is_active')
        }),
    )


@admin.register(DriverProfile)
class DriverProfileAdmin(CompanyRestrictedAdmin):
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


# ============================================================================
# USER ADMIN WITH USERPROFILE INLINE
# ============================================================================

# Unregister default User admin
admin.site.unregister(User)

# Import UserProfile
from accounts.models import UserProfile

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'
    fk_name = 'user'
    fields = ('company', 'role')

@admin.register(User)
class CustomUserAdmin(BaseUserAdmin):
    """
    Custom User Admin with UserProfile inline and tenant isolation
    """
    inlines = (UserProfileInline,)
    
    list_display = ['username', 'email', 'first_name', 'last_name', 'get_company', 'is_staff', 'is_active']
    list_filter = ['is_staff', 'is_superuser', 'is_active', 'groups']
    
    def get_queryset(self, request):
        """
        Filter users by company for non-superusers
        """
        qs = super().get_queryset(request)
        
        # Superusers see all users
        if request.user.is_superuser:
            return qs
        
        # Staff users only see users from their company
        try:
            user_company = request.user.userprofile.company
            if user_company:
                # Filter users who have a profile with the same company
                return qs.filter(userprofile__company=user_company)
        except:
            pass
        
        # If no company assigned, return empty queryset
        return qs.none()
    
    def get_company(self, obj):
        """Display user's company"""
        try:
            return obj.userprofile.company.name if obj.userprofile.company else '-'
        except:
            return '-'
    get_company.short_description = 'Company'
