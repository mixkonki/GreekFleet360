"""
Django Admin Configuration for Finance App
"""
from django.contrib import admin
from unfold.admin import ModelAdmin
from django.utils.html import format_html
from .models import (
    ExpenseFamily, ExpenseCategory, CostCenter, CompanyExpense, 
    TransportOrder, CostItem, CostPosting, CostRateSnapshot, OrderCostBreakdown
)
from .legacy_services import CostCalculator

# Import CompanyRestrictedAdmin from core
from core.admin import CompanyRestrictedAdmin


@admin.register(ExpenseFamily)
class ExpenseFamilyAdmin(ModelAdmin):
    list_display = ['name', 'icon', 'display_order', 'description']
    list_editable = ['display_order']
    search_fields = ['name', 'description']
    ordering = ['display_order', 'name']
    
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        # Add helpful text for icon field
        form.base_fields['icon'].help_text = format_html(
            'Εισάγετε το όνομα του εικονιδίου από το Font Awesome (π.χ. truck, building). '
            'Βρείτε τη λίστα εδώ: <a href="https://fontawesome.com/search?o=r&m=free" target="_blank" '
            'style="color: #0066cc; text-decoration: underline;">Font Awesome Icons</a>'
        )
        return form


@admin.register(ExpenseCategory)
class ExpenseCategoryAdmin(ModelAdmin):
    list_display = ['name', 'family', 'is_system_default', 'description']
    list_filter = ['family', 'is_system_default']
    search_fields = ['name', 'description']
    ordering = ['family', 'name']


@admin.register(CostCenter)
class CostCenterAdmin(CompanyRestrictedAdmin):
    list_display = ['name', 'type', 'company', 'vehicle', 'driver', 'is_active']
    list_filter = ['company', 'type', 'is_active']
    search_fields = ['name', 'description']
    ordering = ['company', 'name']
    
    fieldsets = (
        ('Βασικές Πληροφορίες', {
            'fields': ('company', 'name', 'type', 'description')
        }),
        ('Σύνδεση Οντοτήτων', {
            'fields': ('vehicle', 'driver'),
            'description': 'Αυτόματη κατανομή κόστους σε όχημα ή οδηγό'
        }),
        ('Κατάσταση', {
            'fields': ('is_active',)
        }),
    )
    
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


@admin.register(CostRateSnapshot)
class CostRateSnapshotAdmin(CompanyRestrictedAdmin):
    list_display = ['cost_center', 'basis_unit', 'rate', 'total_cost', 'total_units', 'period_start', 'period_end', 'status', 'company']
    list_filter = ['company', 'cost_center', 'basis_unit', 'status', 'period_start']
    search_fields = ['cost_center__name']
    date_hierarchy = 'period_start'
    ordering = ['-period_start', 'cost_center', 'basis_unit']
    
    fieldsets = (
        ('Περίοδος', {
            'fields': ('company', 'period_start', 'period_end')
        }),
        ('Κέντρο Κόστους', {
            'fields': ('cost_center', 'basis_unit')
        }),
        ('Υπολογισμοί', {
            'fields': ('total_cost', 'total_units', 'rate', 'status')
        }),
    )
    
    readonly_fields = ['created_at']
    
    def get_queryset(self, request):
        """Override to use all_objects for superusers"""
        if request.user.is_superuser:
            return self.model.all_objects.all()
        return self.model.objects.all()
    
    def has_add_permission(self, request):
        """Snapshots are created by management command, not manually"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Snapshots are read-only"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Allow deletion for cleanup"""
        if request.user.is_superuser:
            return True
        if obj and hasattr(request, 'company') and obj.company != request.company:
            return False
        return super().has_delete_permission(request, obj)


@admin.register(OrderCostBreakdown)
class OrderCostBreakdownAdmin(CompanyRestrictedAdmin):
    list_display = [
        'transport_order', 'total_cost', 'revenue', 'profit', 'margin',
        'period_start', 'period_end', 'status', 'company'
    ]
    list_filter = ['company', 'status', 'period_start', 'transport_order__assigned_vehicle']
    search_fields = ['transport_order__customer_name', 'transport_order__origin', 'transport_order__destination']
    date_hierarchy = 'period_start'
    ordering = ['-period_start', '-profit']
    
    fieldsets = (
        ('Περίοδος', {
            'fields': ('company', 'period_start', 'period_end')
        }),
        ('Εντολή Μεταφοράς', {
            'fields': ('transport_order',)
        }),
        ('Κατανομή Κόστους', {
            'fields': ('vehicle_alloc', 'overhead_alloc', 'direct_cost', 'total_cost')
        }),
        ('Κερδοφορία', {
            'fields': ('revenue', 'profit', 'margin', 'status')
        }),
    )
    
    readonly_fields = ['created_at']
    
    def get_queryset(self, request):
        """Override to use all_objects for superusers"""
        if request.user.is_superuser:
            return self.model.all_objects.all()
        return self.model.objects.all()
    
    def has_add_permission(self, request):
        """Breakdowns are created by management command, not manually"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Breakdowns are read-only"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Allow deletion for cleanup"""
        if request.user.is_superuser:
            return True
        if obj and hasattr(request, 'company') and obj.company != request.company:
            return False
        return super().has_delete_permission(request, obj)


@admin.register(CompanyExpense)
class CompanyExpenseAdmin(CompanyRestrictedAdmin):
    list_display = ['category', 'company', 'amount', 'start_date', 'end_date', 'is_amortized', 'is_active']
    list_filter = ['company', 'category', 'is_amortized', 'is_active']
    search_fields = ['category__name', 'description', 'invoice_number']
    ordering = ['-created_at']
    date_hierarchy = 'start_date'
    
    fieldsets = (
        ('Βασικές Πληροφορίες', {
            'fields': ('company', 'category', 'cost_center')
        }),
        ('Οικονομικά', {
            'fields': ('amount', 'start_date', 'end_date', 'is_amortized')
        }),
        ('Τιμολόγηση', {
            'fields': ('invoice_number',)
        }),
        ('Λεπτομέρειες', {
            'fields': ('description', 'is_active')
        }),
    )
    
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


@admin.register(TransportOrder)
class TransportOrderAdmin(CompanyRestrictedAdmin):
    list_display = [
        'customer_name', 'date', 'origin', 'destination',
        'distance_km', 'agreed_price', 'assigned_vehicle',
        'status', 'get_projected_profit'
    ]
    list_filter = ['company', 'status', 'date', 'assigned_vehicle']
    search_fields = ['customer_name', 'origin', 'destination', 'assigned_vehicle__plate']
    date_hierarchy = 'date'
    ordering = ['-date', '-created_at']
    
    fieldsets = (
        ('Βασικές Πληροφορίες', {
            'fields': ('company', 'customer_name', 'date', 'status')
        }),
        ('Διαδρομή', {
            'fields': ('origin', 'destination', 'distance_km')
        }),
        ('Οικονομικά', {
            'fields': ('agreed_price', 'tolls_cost', 'ferry_cost')
        }),
        ('Ανάθεση', {
            'fields': ('assigned_vehicle', 'assigned_driver', 'duration_hours')
        }),
        ('Σημειώσεις', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at', 'get_profitability_breakdown']
    
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
    
    def get_projected_profit(self, obj):
        """
        Calculate and display projected profit using CostCalculator
        """
        if not obj.assigned_vehicle or not obj.duration_hours:
            return format_html('<span style="color: gray;">N/A</span>')
        
        try:
            calculator = CostCalculator(
                vehicle=obj.assigned_vehicle,
                distance_km=obj.distance_km,
                duration_hours=obj.duration_hours,
                tolls_cost=obj.tolls_cost,
                ferry_cost=obj.ferry_cost
            )
            
            result = calculator.calculate_trip_profitability(obj.agreed_price)
            profit = result['profit']
            profit_margin = result['profit_margin']
            
            if profit >= 0:
                color = 'green' if profit_margin > 15 else 'orange'
                return format_html(
                    '<span style="color: {}; font-weight: bold;">€{:,.2f} ({}%)</span>',
                    color, profit, profit_margin
                )
            else:
                return format_html(
                    '<span style="color: red; font-weight: bold;">-€{:,.2f} ({}%)</span>',
                    abs(profit), profit_margin
                )
        except Exception as e:
            return format_html('<span style="color: red;">Error: {}</span>', str(e))
    
    get_projected_profit.short_description = "Προβλεπόμενο Κέρδος"
    
    def get_profitability_breakdown(self, obj):
        """
        Display detailed cost breakdown in admin
        """
        if not obj.assigned_vehicle or not obj.duration_hours:
            return "Δεν υπάρχουν αρκετά δεδομένα για υπολογισμό"
        
        try:
            calculator = CostCalculator(
                vehicle=obj.assigned_vehicle,
                distance_km=obj.distance_km,
                duration_hours=obj.duration_hours,
                tolls_cost=obj.tolls_cost,
                ferry_cost=obj.ferry_cost
            )
            
            result = calculator.calculate_trip_profitability(obj.agreed_price)
            
            html = f"""
            <table style="border-collapse: collapse; width: 100%;">
                <tr style="background-color: #f0f0f0;">
                    <th style="padding: 8px; text-align: left; border: 1px solid #ddd;">Κατηγορία</th>
                    <th style="padding: 8px; text-align: right; border: 1px solid #ddd;">Ποσό (€)</th>
                </tr>
                <tr>
                    <td style="padding: 8px; border: 1px solid #ddd;">Σταθερά Κόστη</td>
                    <td style="padding: 8px; text-align: right; border: 1px solid #ddd;">€{result['fixed_cost']:,.2f}</td>
                </tr>
                <tr>
                    <td style="padding: 8px; border: 1px solid #ddd;">Γενικά Έξοδα</td>
                    <td style="padding: 8px; text-align: right; border: 1px solid #ddd;">€{result['overhead_cost']:,.2f}</td>
                </tr>
                <tr>
                    <td style="padding: 8px; border: 1px solid #ddd;">Μεταβλητά Κόστη</td>
                    <td style="padding: 8px; text-align: right; border: 1px solid #ddd;">€{result['variable_cost']:,.2f}</td>
                </tr>
                <tr>
                    <td style="padding: 8px; border: 1px solid #ddd;">Διόδια</td>
                    <td style="padding: 8px; text-align: right; border: 1px solid #ddd;">€{result['tolls_cost']:,.2f}</td>
                </tr>
                <tr>
                    <td style="padding: 8px; border: 1px solid #ddd;">Πορθμείο</td>
                    <td style="padding: 8px; text-align: right; border: 1px solid #ddd;">€{result['ferry_cost']:,.2f}</td>
                </tr>
                <tr style="background-color: #f9f9f9; font-weight: bold;">
                    <td style="padding: 8px; border: 1px solid #ddd;">Συνολικό Κόστος</td>
                    <td style="padding: 8px; text-align: right; border: 1px solid #ddd;">€{result['total_cost']:,.2f}</td>
                </tr>
                <tr style="background-color: #e8f5e9;">
                    <td style="padding: 8px; border: 1px solid #ddd;">Έσοδα</td>
                    <td style="padding: 8px; text-align: right; border: 1px solid #ddd;">€{result['revenue']:,.2f}</td>
                </tr>
                <tr style="background-color: {'#c8e6c9' if result['profit'] >= 0 else '#ffcdd2'}; font-weight: bold; font-size: 1.1em;">
                    <td style="padding: 8px; border: 1px solid #ddd;">Κέρδος</td>
                    <td style="padding: 8px; text-align: right; border: 1px solid #ddd;">€{result['profit']:,.2f} ({result['profit_margin']}%)</td>
                </tr>
            </table>
            """
            return format_html(html)
        except Exception as e:
            return format_html('<span style="color: red;">Σφάλμα: {}</span>', str(e))
    
    get_profitability_breakdown.short_description = "Ανάλυση Κερδοφορίας"
    
    # Add profitability breakdown to the detail view
    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        obj = self.get_object(request, object_id)
        if obj:
            extra_context['profitability_breakdown'] = self.get_profitability_breakdown(obj)
        return super().change_view(request, object_id, form_url, extra_context)


@admin.register(CostItem)
class CostItemAdmin(CompanyRestrictedAdmin):
    list_display = ['name', 'category', 'unit', 'company', 'is_active']
    list_filter = ['company', 'category', 'unit', 'is_active']
    search_fields = ['name', 'description']
    ordering = ['company', 'category', 'name']
    
    fieldsets = (
        ('Βασικές Πληροφορίες', {
            'fields': ('company', 'name', 'description')
        }),
        ('Κατηγοριοποίηση', {
            'fields': ('category', 'unit')
        }),
        ('Κατάσταση', {
            'fields': ('is_active',)
        }),
    )
    
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


@admin.register(CostPosting)
class CostPostingAdmin(CompanyRestrictedAdmin):
    list_display = ['cost_item', 'cost_center', 'amount', 'period_start', 'period_end', 'company']
    list_filter = ['company', 'cost_center', 'cost_item', 'period_start']
    search_fields = ['cost_item__name', 'cost_center__name', 'notes']
    date_hierarchy = 'period_start'
    ordering = ['-period_start', '-created_at']
    
    fieldsets = (
        ('Βασικές Πληροφορίες', {
            'fields': ('company', 'cost_center', 'cost_item')
        }),
        ('Οικονομικά', {
            'fields': ('amount', 'period_start', 'period_end')
        }),
        ('Σημειώσεις', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
    )
    
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
