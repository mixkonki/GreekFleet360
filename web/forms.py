"""
Django Forms for GreekFleet 360 Web Interface
Tailwind CSS styled forms
"""
from django import forms
from django.contrib.auth.models import User
from finance.models import RecurringExpense, TransportOrder, ExpenseCategory, CostCenter
from core.models import Employee, Company
from operations.models import FuelEntry, ServiceLog, Vehicle
from accounts.models import UserProfile


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
            self.fields['assigned_vehicle'].queryset = Vehicle.objects.filter(
                company=company,
                status='ACTIVE'
            )
        elif self.instance and self.instance.pk and self.instance.company:
            # If editing existing employee, use its company
            self.fields['assigned_vehicle'].queryset = Vehicle.objects.filter(
                company=self.instance.company,
                status='ACTIVE'
            )


class VehicleForm(TailwindFormMixin, forms.ModelForm):
    """
    Form for creating/editing Fleet Vehicles - Phase 4
    Aligned with Official Registration Certificate (Άδεια Κυκλοφορίας)
    """
    class Meta:
        model = Vehicle
        fields = [
            # Section 1: Identity (Registration Certificate Codes)
            'license_plate', 'vin', 'make', 'model', 'color', 'manufacturing_year',
            'first_registration_date', 'acquisition_date',
            # Section 2: Classification
            'vehicle_class', 'body_type',
            # Section 3: External Dimensions
            'length_total_m', 'width_m', 'height_m',
            # Section 3b: Cargo Dimensions
            'cargo_length_m', 'cargo_width_m', 'cargo_height_m',
            # Section 4: Weights
            'gross_weight_kg', 'unladen_weight_kg',
            # Section 5: Power & Energy
            'horsepower', 'engine_capacity_cc', 'fuel_type', 'emission_class', 'tank_capacity',
            # Section 6: Capacity
            'seats',
            # Section 7: Financials
            'purchase_value', 'available_hours_per_year',
            # Section 8: Status
            'status', 'current_odometer',
            # Notes
            'notes'
        ]
        widgets = {
            'license_plate': forms.TextInput(attrs={'placeholder': 'Κωδικός A'}),
            'vin': forms.TextInput(attrs={'placeholder': 'Κωδικός E - 17 ψηφία'}),
            'make': forms.TextInput(attrs={'placeholder': 'Κωδικός D.1'}),
            'model': forms.TextInput(attrs={'placeholder': 'Κωδικός D.2'}),
            'color': forms.TextInput(attrs={'placeholder': 'Κωδικός R'}),
            'manufacturing_year': forms.NumberInput(attrs={'placeholder': '2020'}),
            'first_registration_date': forms.DateInput(attrs={'type': 'date', 'placeholder': 'Κωδικός B'}),
            'acquisition_date': forms.DateInput(attrs={'type': 'date'}),
            'length_total_m': forms.NumberInput(attrs={'placeholder': 'Κωδικός L', 'step': '0.01'}),
            'width_m': forms.NumberInput(attrs={'placeholder': 'Εξωτερικό πλάτος', 'step': '0.01'}),
            'height_m': forms.NumberInput(attrs={'placeholder': 'Εξωτερικό ύψος', 'step': '0.01'}),
            'cargo_length_m': forms.NumberInput(attrs={'placeholder': 'Εσωτερικό μήκος', 'step': '0.01'}),
            'cargo_width_m': forms.NumberInput(attrs={'placeholder': 'Εσωτερικό πλάτος', 'step': '0.01'}),
            'cargo_height_m': forms.NumberInput(attrs={'placeholder': 'Εσωτερικό ύψος', 'step': '0.01'}),
            'gross_weight_kg': forms.NumberInput(attrs={'placeholder': 'Κωδικός F.1'}),
            'unladen_weight_kg': forms.NumberInput(attrs={'placeholder': 'Κωδικός G'}),
            'horsepower': forms.NumberInput(attrs={'placeholder': 'Κωδικός P.2'}),
            'engine_capacity_cc': forms.NumberInput(attrs={'placeholder': 'Κωδικός P.1'}),
            'tank_capacity': forms.NumberInput(attrs={'placeholder': 'Λίτρα/kWh', 'step': '0.01'}),
            'seats': forms.NumberInput(attrs={'placeholder': 'Κωδικός S.1'}),
            'purchase_value': forms.NumberInput(attrs={'placeholder': 'Αξία αγοράς', 'step': '0.01'}),
            'available_hours_per_year': forms.NumberInput(attrs={'placeholder': '1936'}),
            'current_odometer': forms.NumberInput(attrs={'placeholder': 'Τρέχοντα km'}),
            'notes': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Σημειώσεις'}),
        }
    
    def __init__(self, *args, **kwargs):
        # Extract company from kwargs if provided
        company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)


class CompanyForm(TailwindFormMixin, forms.ModelForm):
    """
    Form for editing Company details
    """
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
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make tax_id readonly if already set
        if self.instance and self.instance.pk and self.instance.tax_id:
            self.fields['tax_id'].widget.attrs['readonly'] = True
            self.fields['tax_id'].widget.attrs['class'] += ' bg-gray-100 cursor-not-allowed'
            self.fields['tax_id'].help_text = 'Κλειδωμένο μετά την αποθήκευση.'

    def clean_tax_id(self):
        import re
        value = (self.cleaned_data.get('tax_id') or '').strip()
        if value and not re.fullmatch(r'\d{9}', value):
            raise forms.ValidationError('Το ΑΦΜ πρέπει να αποτελείται από 9 ψηφία.')
        # Immutability: reject changes once tax_id is set
        if self.instance and self.instance.pk:
            existing = (self.instance.tax_id or '').strip()
            if existing and value != existing:
                raise forms.ValidationError(
                    'Το ΑΦΜ δεν μπορεί να αλλάξει αφού αποθηκευτεί. '
                    'Επικοινωνήστε με τον διαχειριστή.'
                )
        return value


class CompanyUserForm(TailwindFormMixin, forms.ModelForm):
    """
    Form for creating/editing Company Users
    """
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Κωδικός πρόσβασης'}),
        required=False,
        label='Κωδικός Πρόσβασης',
        help_text='Αφήστε κενό για να κρατήσετε τον υπάρχοντα κωδικό'
    )
    role = forms.ChoiceField(
        choices=UserProfile.ROLE_CHOICES,
        label='Ρόλος',
        widget=forms.Select()
    )
    
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'username']
        widgets = {
            'first_name': forms.TextInput(attrs={'placeholder': 'π.χ. Γιώργος'}),
            'last_name': forms.TextInput(attrs={'placeholder': 'π.χ. Παπαδόπουλος'}),
            'email': forms.EmailInput(attrs={'placeholder': 'π.χ. user@company.gr'}),
            'username': forms.TextInput(attrs={'placeholder': 'π.χ. gpapadopoulos'}),
        }
        labels = {
            'first_name': 'Όνομα',
            'last_name': 'Επώνυμο',
            'email': 'Email',
            'username': 'Username',
        }


class ExpenseCategoryForm(TailwindFormMixin, forms.ModelForm):
    """
    Form for creating custom Expense Categories
    """
    class Meta:
        model = ExpenseCategory
        fields = ['family', 'name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'π.χ. Ενοίκιο Γραφείου'}),
            'description': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Περιγραφή κατηγορίας'}),
        }
        labels = {
            'family': 'Οικογένεια Εξόδων',
            'name': 'Όνομα Κατηγορίας',
            'description': 'Περιγραφή',
        }
