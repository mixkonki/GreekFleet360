"""
Django Forms for GreekFleet 360 Web Interface
Tailwind CSS styled forms
"""
from django import forms
from finance.models import RecurringExpense, TransportOrder, ExpenseCategory, CostCenter
from operations.models import FuelEntry, ServiceLog
from core.models import VehicleAsset


class TailwindFormMixin:
    """
    Mixin to apply Tailwind CSS classes to form fields
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            # Base input classes
            base_classes = 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent'
            
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = 'w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500'
            elif isinstance(field.widget, forms.Select):
                field.widget.attrs['class'] = base_classes + ' bg-white'
            elif isinstance(field.widget, forms.Textarea):
                field.widget.attrs['class'] = base_classes
                field.widget.attrs['rows'] = 4
            elif isinstance(field.widget, forms.FileInput):
                field.widget.attrs['class'] = 'block w-full text-sm text-gray-900 border border-gray-300 rounded-lg cursor-pointer bg-gray-50 focus:outline-none'
            else:
                field.widget.attrs['class'] = base_classes


class CompanyExpenseForm(TailwindFormMixin, forms.ModelForm):
    """
    Form for Company Expense (Frontend - no company field)
    """
    class Meta:
        model = RecurringExpense  # Using alias for backward compatibility
        fields = [
            'category', 'cost_center', 'expense_type', 'periodicity',
            'amount', 'start_date', 'end_date',
            'is_amortized', 'invoice_number', 'description'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 2}),
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
        }
    
    def __init__(self, *args, **kwargs):
        # Extract company from kwargs if provided
        company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)
        
        # Filter cost_center queryset by company
        if company:
            self.fields['cost_center'].queryset = CostCenter.objects.filter(
                company=company,
                is_active=True
            )
        elif self.instance and self.instance.pk and self.instance.company:
            # If editing existing expense, use its company
            self.fields['cost_center'].queryset = CostCenter.objects.filter(
                company=self.instance.company,
                is_active=True
            )
        
        # Group categories by family using optgroup
        from finance.models import ExpenseFamily
        families = ExpenseFamily.objects.prefetch_related('categories').order_by('display_order')
        
        grouped_choices = [('', '---------')]  # Empty choice
        for family in families:
            family_categories = [(cat.id, cat.name) for cat in family.categories.all()]
            if family_categories:
                grouped_choices.append((family.name, family_categories))
        
        self.fields['category'].choices = grouped_choices


# Backward compatibility alias
RecurringExpenseForm = CompanyExpenseForm


class CostCenterForm(TailwindFormMixin, forms.ModelForm):
    """
    Form for Cost Center (Frontend - no company field)
    """
    class Meta:
        model = CostCenter
        fields = ['name', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 2}),
        }


class TransportOrderForm(TailwindFormMixin, forms.ModelForm):
    """
    Form for creating/editing Transport Orders
    """
    class Meta:
        model = TransportOrder
        fields = [
            'company', 'customer_name', 'date',
            'origin', 'destination', 'distance_km',
            'agreed_price', 'assigned_vehicle', 'assigned_driver',
            'duration_hours', 'tolls_cost', 'ferry_cost',
            'status', 'notes'
        ]
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }


class FuelEntryForm(TailwindFormMixin, forms.ModelForm):
    """
    Form for Fuel Entry
    """
    class Meta:
        model = FuelEntry
        fields = [
            'company', 'vehicle', 'driver', 'date',
            'fuel_station_name', 'liters', 'cost_per_liter', 'total_cost',
            'is_full_tank', 'odometer_reading',
            'adblue_liters', 'adblue_cost', 'notes'
        ]
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 2}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Auto-calculate total_cost using JavaScript
        self.fields['total_cost'].required = False


class ServiceLogForm(TailwindFormMixin, forms.ModelForm):
    """
    Form for Service Log Entry
    """
    class Meta:
        model = ServiceLog
        fields = [
            'company', 'vehicle', 'date', 'service_type',
            'odometer_reading', 'cost_parts', 'cost_labor', 'total_cost',
            'description', 'invoice_number', 'invoice_attachment', 'notes'
        ]
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 3}),
            'notes': forms.Textarea(attrs={'rows': 2}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Auto-calculate total_cost using JavaScript
        self.fields['total_cost'].required = False


class VehicleFinancialForm(TailwindFormMixin, forms.ModelForm):
    """
    Form for editing Vehicle Financial Profile
    (Only financial fields, not the full vehicle)
    """
    # Custom fields for cost configuration
    driver_monthly_salary = forms.DecimalField(
        max_digits=8,
        decimal_places=2,
        required=False,
        label="Μηνιαίος Μισθός Οδηγού (€)",
        help_text="Μικτός μισθός οδηγού"
    )
    
    annual_insurance_cost = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        label="Ετήσιο Κόστος Ασφάλισης (€)"
    )
    
    tire_set_price = forms.DecimalField(
        max_digits=8,
        decimal_places=2,
        required=False,
        label="Τιμή Σετ Ελαστικών (€)"
    )
    
    tire_lifespan_km = forms.IntegerField(
        required=False,
        label="Διάρκεια Ζωής Ελαστικών (km)",
        initial=50000
    )
    
    maintenance_accrual_per_km = forms.DecimalField(
        max_digits=6,
        decimal_places=3,
        required=False,
        label="Πρόβλεψη Συντήρησης (€/km)",
        initial=0.05
    )
    
    class Meta:
        model = VehicleAsset
        fields = ['purchase_price']
