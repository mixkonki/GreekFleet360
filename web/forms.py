"""
Django Forms for GreekFleet 360 Web Interface
Tailwind CSS styled forms
"""
from django import forms
from finance.models import RecurringExpense, TransportOrder, ExpenseCategory, CostCenter
from core.models import Employee
from operations.models import FuelEntry, ServiceLog, Vehicle
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
            'category', 'cost_center', 'employee', 'expense_type', 'periodicity',
            'amount', 'start_date', 'end_date',
            'is_amortized', 'distribute_to_all_centers', 'invoice_number', 'description'
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
            self.fields['employee'].queryset = Employee.objects.filter(
                company=company,
                is_active=True
            )
        elif self.instance and self.instance.pk and self.instance.company:
            # If editing existing expense, use its company
            self.fields['cost_center'].queryset = CostCenter.objects.filter(
                company=self.instance.company,
                is_active=True
            )
            self.fields['employee'].queryset = Employee.objects.filter(
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


class EmployeeForm(TailwindFormMixin, forms.ModelForm):
    """
    Form for Employee (Frontend - no company field)
    """
    class Meta:
        model = Employee
        fields = ['first_name', 'last_name', 'position', 'assigned_vehicle']
    
    def __init__(self, *args, **kwargs):
        # Extract company from kwargs if provided
        company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)
        
        # Filter assigned_vehicle queryset by company
        if company:
            self.fields['assigned_vehicle'].queryset = VehicleAsset.objects.filter(
                company=company,
                status='ACTIVE'
            )
        elif self.instance and self.instance.pk and self.instance.company:
            # If editing existing employee, use its company
            self.fields['assigned_vehicle'].queryset = VehicleAsset.objects.filter(
                company=self.instance.company,
                status='ACTIVE'
            )


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


class VehicleForm(TailwindFormMixin, forms.ModelForm):
    """
    Form for creating/editing Fleet Vehicles
    Includes all fields: Basic Info, Capacity, and Financials
    """
    class Meta:
        model = Vehicle
        fields = [
            'license_plate', 'make', 'model', 'vehicle_type',
            'gross_weight_kg', 'payload_capacity_kg', 'seats',
            'purchase_value', 'residual_value', 'depreciation_years',
            'annual_insurance', 'annual_road_tax', 'available_hours_per_year'
        ]
        widgets = {
            'license_plate': forms.TextInput(attrs={'placeholder': 'π.χ. ΑΒΓ-1234'}),
            'make': forms.TextInput(attrs={'placeholder': 'π.χ. Mercedes-Benz'}),
            'model': forms.TextInput(attrs={'placeholder': 'π.χ. Actros 1845'}),
            'gross_weight_kg': forms.NumberInput(attrs={'placeholder': 'π.χ. 18000'}),
            'payload_capacity_kg': forms.NumberInput(attrs={'placeholder': 'π.χ. 12000'}),
            'seats': forms.NumberInput(attrs={'placeholder': 'π.χ. 2'}),
            'purchase_value': forms.NumberInput(attrs={'placeholder': 'π.χ. 50000.00', 'step': '0.01'}),
            'residual_value': forms.NumberInput(attrs={'placeholder': 'π.χ. 10000.00', 'step': '0.01'}),
            'depreciation_years': forms.NumberInput(attrs={'placeholder': 'π.χ. 5'}),
            'annual_insurance': forms.NumberInput(attrs={'placeholder': 'π.χ. 2000.00', 'step': '0.01'}),
            'annual_road_tax': forms.NumberInput(attrs={'placeholder': 'π.χ. 500.00', 'step': '0.01'}),
            'available_hours_per_year': forms.NumberInput(attrs={'placeholder': '1936'}),
        }
        labels = {
            'license_plate': 'Πινακίδα',
            'make': 'Μάρκα',
            'model': 'Μοντέλο',
            'vehicle_type': 'Τύπος Οχήματος',
            'gross_weight_kg': 'Μικτό Βάρος (kg)',
            'payload_capacity_kg': 'Ωφέλιμο Φορτίο (kg)',
            'seats': 'Θέσεις Επιβατών',
            'purchase_value': 'Αξία Αγοράς (€)',
            'residual_value': 'Υπολειμματική Αξία (€)',
            'depreciation_years': 'Έτη Απόσβεσης',
            'annual_insurance': 'Ετήσια Ασφάλιση (€)',
            'annual_road_tax': 'Ετήσια Τέλη Κυκλοφορίας (€)',
            'available_hours_per_year': 'Διαθέσιμες Ώρες/Έτος',
        }
        help_texts = {
            'available_hours_per_year': '1936 ώρες = 11 μήνες × 22 ημέρες × 8 ώρες',
            'purchase_value': 'Αξία αγοράς του οχήματος σε ευρώ',
            'residual_value': 'Υπολειμματική αξία μετά την απόσβεση',
            'depreciation_years': 'Αριθμός ετών για την απόσβεση',
        }
    
    def __init__(self, *args, **kwargs):
        # Extract company from kwargs if provided
        company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)
        
        # Add Euro symbol (€) to monetary field labels
        monetary_fields = ['purchase_value', 'residual_value', 'annual_insurance', 'annual_road_tax']
        for field_name in monetary_fields:
            if field_name in self.fields:
                current_label = self.fields[field_name].label
                if '€' not in current_label:
                    self.fields[field_name].label = f"{current_label}"


class CompanyForm(TailwindFormMixin, forms.ModelForm):
    """
    Form for editing Company details
    """
    from core.models import Company
    
    class Meta:
        model = Company
        fields = ['name', 'transport_type', 'tax_id', 'address', 'phone', 'email']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'π.χ. GreekFleet Transport'}),
            'tax_id': forms.TextInput(attrs={'placeholder': 'π.χ. 123456789'}),
            'address': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Διεύθυνση εταιρείας'}),
            'phone': forms.TextInput(attrs={'placeholder': 'π.χ. 2101234567'}),
            'email': forms.EmailInput(attrs={'placeholder': 'π.χ. info@company.gr'}),
        }
        labels = {
            'name': 'Επωνυμία Εταιρείας',
            'transport_type': 'Τύπος Μεταφορών',
            'tax_id': 'ΑΦΜ',
            'address': 'Διεύθυνση',
            'phone': 'Τηλέφωνο',
            'email': 'Email',
        }
