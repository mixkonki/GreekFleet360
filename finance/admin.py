"""
Django Admin Configuration for Finance App
"""
from django.contrib import admin
from unfold.admin import ModelAdmin
from django.utils.html import format_html
from .models import ExpenseFamily, ExpenseCategory, CostCenter, CompanyExpense, TransportOrder
from .services import CostCalculator


@admin.register(ExpenseFamily)
class ExpenseFamilyAdmin(ModelAdmin):
    list_display = ['name', 'icon', 'display_order', 'description']
    list_editable = ['display_order']
    search_fields = ['name', 'description']
    ordering = ['display_order', 'name']


@admin.register(ExpenseCategory)
class ExpenseCategoryAdmin(ModelAdmin):
    list_display = ['name', 'family', 'is_system_default', 'description']
    list_filter = ['family', 'is_system_default']
    search_fields = ['name', 'description']
    ordering = ['family', 'name']


@admin.register(CostCenter)
class CostCenterAdmin(ModelAdmin):
    list_display = ['name', 'company', 'is_active']
    list_filter = ['company', 'is_active']
    search_fields = ['name', 'description']
    ordering = ['company', 'name']


@admin.register(CompanyExpense)
class CompanyExpenseAdmin(ModelAdmin):
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


@admin.register(TransportOrder)
class TransportOrderAdmin(ModelAdmin):
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
