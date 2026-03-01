"""
Django Forms for GreekFleet 360 Web Interface
Tailwind CSS styled forms
"""
import re
from django import forms
from django.contrib.auth.models import User

from accounts.models import UserProfile
from core.models import Employee, Company
from core.driver_compliance_models import DriverCompliance
from finance.models import RecurringExpense, TransportOrder, ExpenseCategory, CostCenter
from operations.models import FuelEntry, ServiceLog, Vehicle


class TailwindFormMixin:
    """
    Mixin to apply Tailwind CSS classes to form fields
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            base_classes = (
                "w-full px-4 py-2 border border-gray-300 rounded-lg "
                "focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            )

            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs["class"] = (
                    "w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500"
                )
            elif isinstance(field.widget, forms.Select):
                field.widget.attrs["class"] = base_classes + " bg-white"
            elif isinstance(field.widget, forms.Textarea):
                field.widget.attrs["class"] = base_classes
                field.widget.attrs["rows"] = 4
            elif isinstance(field.widget, forms.FileInput):
                field.widget.attrs["class"] = (
                    "block w-full text-sm text-gray-900 border border-gray-300 rounded-lg "
                    "cursor-pointer bg-gray-50 focus:outline-none"
                )
            else:
                field.widget.attrs["class"] = base_classes


class CompanyExpenseForm(TailwindFormMixin, forms.ModelForm):
    """
    Form for Company Expense (Frontend - company is NOT editable; scoped server-side)
    """
    class Meta:
        model = RecurringExpense  # Using alias for backward compatibility
        fields = [
            "category", "cost_center", "employee", "expense_type", "periodicity",
            "amount", "start_date", "end_date",
            "is_amortized", "distribute_to_all_centers", "invoice_number", "description"
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 2}),
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "end_date": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        company = kwargs.pop("company", None)
        super().__init__(*args, **kwargs)

        # Tenant-scoped querysets
        if company:
            self.fields["cost_center"].queryset = CostCenter.objects.filter(company=company, is_active=True)
            self.fields["employee"].queryset = Employee.objects.filter(company=company, is_active=True)
        elif self.instance and self.instance.pk and getattr(self.instance, "company", None):
            self.fields["cost_center"].queryset = CostCenter.objects.filter(company=self.instance.company, is_active=True)
            self.fields["employee"].queryset = Employee.objects.filter(company=self.instance.company, is_active=True)

        # Group categories by family using optgroup
        from finance.models import ExpenseFamily
        families = ExpenseFamily.objects.prefetch_related("categories").order_by("display_order")

        grouped_choices = [("", "---------")]
        for family in families:
            family_categories = [(cat.id, cat.name) for cat in family.categories.all()]
            if family_categories:
                grouped_choices.append((family.name, family_categories))

        self.fields["category"].choices = grouped_choices


# Backward compatibility alias
RecurringExpenseForm = CompanyExpenseForm


class CostCenterForm(TailwindFormMixin, forms.ModelForm):
    """
    Form for Cost Center (Frontend - company is NOT editable; scoped server-side)
    """
    class Meta:
        model = CostCenter
        fields = ["name", "description", "type", "vehicle", "driver"]
        widgets = {"description": forms.Textarea(attrs={"rows": 2})}

    def __init__(self, *args, **kwargs):
        company = kwargs.pop("company", None)
        super().__init__(*args, **kwargs)

        if company:
            self.fields["driver"].queryset = Employee.objects.filter(
                company=company,
                position__is_driver_role=True,
                is_active=True
            )
            self.fields["vehicle"].queryset = Vehicle.objects.filter(company=company, status="ACTIVE")
        elif self.instance and self.instance.pk and getattr(self.instance, "company", None):
            self.fields["driver"].queryset = Employee.objects.filter(
                company=self.instance.company,
                position__is_driver_role=True,
                is_active=True
            )
            self.fields["vehicle"].queryset = Vehicle.objects.filter(company=self.instance.company, status="ACTIVE")

    def clean_driver(self):
        driver = self.cleaned_data.get("driver")
        if driver:
            if not driver.is_active:
                raise forms.ValidationError("Ο επιλεγμένος οδηγός δεν είναι ενεργός.")
            if not driver.position.is_driver_role:
                raise forms.ValidationError("Ο επιλεγμένος υπάλληλος δεν έχει θέση οδηγού.")
        return driver


class TransportOrderForm(TailwindFormMixin, forms.ModelForm):
    """
    Form for creating/editing Transport Orders (Frontend - company is NOT editable)
    """
    class Meta:
        model = TransportOrder
        # Important: company is set server-side; do NOT expose it in the form
        exclude = ["company"]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        self.company = kwargs.pop("company", None)
        super().__init__(*args, **kwargs)

        # Tenant-scoped driver dropdown
        if self.company and "assigned_driver" in self.fields:
            self.fields["assigned_driver"].queryset = Employee.objects.filter(
                company=self.company,
                position__is_driver_role=True,
                is_active=True
            )
        elif self.instance and self.instance.pk and getattr(self.instance, "company", None) and "assigned_driver" in self.fields:
            self.fields["assigned_driver"].queryset = Employee.objects.filter(
                company=self.instance.company,
                position__is_driver_role=True,
                is_active=True
            )
        
        # Tenant-scoped vehicle dropdown
        if self.company and "assigned_vehicle" in self.fields:
            self.fields["assigned_vehicle"].queryset = Vehicle.objects.filter(
                company=self.company,
                status='ACTIVE'
            )
        elif self.instance and self.instance.pk and getattr(self.instance, "company", None) and "assigned_vehicle" in self.fields:
            self.fields["assigned_vehicle"].queryset = Vehicle.objects.filter(
                company=self.instance.company,
                status='ACTIVE'
            )

    def clean(self):
        """
        HARD BLOCK: Validate driver compliance before allowing order assignment
        """
        cleaned_data = super().clean()
        driver = cleaned_data.get("assigned_driver")
        assigned_vehicle = cleaned_data.get("assigned_vehicle")
        requires_adr = cleaned_data.get("requires_adr", False)
        
        # If no driver assigned, allow (draft order)
        if not driver:
            return cleaned_data
        
        # Driver must be active and have driver role
        if not driver.is_active:
            raise forms.ValidationError("Ο επιλεγμένος οδηγός δεν είναι ενεργός. (Driver is inactive)")
        
        if not driver.position.is_driver_role:
            raise forms.ValidationError("Ο επιλεγμένος υπάλληλος δεν έχει θέση οδηγού. (Employee is not a driver)")
        
        # Check if driver has compliance record
        try:
            compliance = driver.driver_compliance
        except Exception:
            raise forms.ValidationError(
                f"Ο οδηγός {driver.full_name} δεν έχει καταχωρημένα στοιχεία συμμόρφωσης (άδεια, ΠΕΙ, ταχογράφος). "
                f"(Driver {driver.full_name} has no compliance record)"
            )
        
        # Get today's date for validation
        from django.utils import timezone
        today = timezone.now().date()
        
        # Check license validity
        if not compliance.is_license_valid(today):
            raise forms.ValidationError(
                f"Η άδεια οδήγησης του {driver.full_name} έχει λήξει ({compliance.license_expiry_date}). "
                f"(Driver license expired on {compliance.license_expiry_date})"
            )
        
        # Vehicle-class specific validation
        if assigned_vehicle:
            vehicle_class = assigned_vehicle.vehicle_class
            
            # BUS: requires D/DE license, PEI bus, tachograph
            if vehicle_class == 'BUS':
                if not (compliance.has_license_category('D') or compliance.has_license_category('DE')):
                    raise forms.ValidationError(
                        f"Ο οδηγός {driver.full_name} δεν έχει άδεια κατηγορίας D/DE για λεωφορεία. "
                        f"(Driver does not have D/DE license for buses)"
                    )
                
                if not compliance.is_pei_bus_valid(today):
                    raise forms.ValidationError(
                        f"Το ΠΕΙ λεωφορείων του {driver.full_name} λείπει ή έχει λήξει. "
                        f"(Bus PEI missing or expired)"
                    )
                
                if not compliance.is_tachograph_valid(today):
                    raise forms.ValidationError(
                        f"Η κάρτα ψηφιακού ταχογράφου του {driver.full_name} λείπει ή έχει λήξει. "
                        f"(Tachograph card missing or expired)"
                    )
            
            # TRUCK: requires C/CE license, PEI truck, tachograph
            elif vehicle_class == 'TRUCK':
                if not (compliance.has_license_category('C') or compliance.has_license_category('CE')):
                    raise forms.ValidationError(
                        f"Ο οδηγός {driver.full_name} δεν έχει άδεια κατηγορίας C/CE για φορτηγά. "
                        f"(Driver does not have C/CE license for trucks)"
                    )
                
                if not compliance.is_pei_truck_valid(today):
                    raise forms.ValidationError(
                        f"Το ΠΕΙ φορτηγών του {driver.full_name} λείπει ή έχει λήξει. "
                        f"(Truck PEI missing or expired)"
                    )
                
                if not compliance.is_tachograph_valid(today):
                    raise forms.ValidationError(
                        f"Η κάρτα ψηφιακού ταχογράφου του {driver.full_name} λείπει ή έχει λήξει. "
                        f"(Tachograph card missing or expired)"
                    )
            
            # VAN: requires B license minimum
            elif vehicle_class == 'VAN':
                if not compliance.has_license_category('B'):
                    raise forms.ValidationError(
                        f"Ο οδηγός {driver.full_name} δεν έχει άδεια κατηγορίας B για βαν. "
                        f"(Driver does not have B license for van)"
                    )
        
        # ADR validation
        if requires_adr:
            if not compliance.is_adr_valid(today):
                raise forms.ValidationError(
                    f"Η εντολή απαιτεί ADR αλλά το ADR του {driver.full_name} λείπει ή έχει λήξει. "
                    f"(Order requires ADR but driver's ADR is missing or expired)"
                )
            
            if not compliance.has_any_adr_category():
                raise forms.ValidationError(
                    f"Η εντολή απαιτεί ADR αλλά ο {driver.full_name} δεν έχει καμία κατηγορία ADR. "
                    f"(Order requires ADR but driver has no ADR categories)"
                )
        
        return cleaned_data


class FuelEntryForm(TailwindFormMixin, forms.ModelForm):
    """
    Form for Fuel Entry (Frontend - company is NOT editable)
    """
    class Meta:
        model = FuelEntry
        exclude = ["company"]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}),
            "notes": forms.Textarea(attrs={"rows": 2}),
        }

    def __init__(self, *args, **kwargs):
        company = kwargs.pop("company", None)
        super().__init__(*args, **kwargs)

        # Auto-calc total_cost
        if "total_cost" in self.fields:
            self.fields["total_cost"].required = False

        # Scope dropdowns if present
        if company:
            if "vehicle" in self.fields:
                self.fields["vehicle"].queryset = Vehicle.objects.filter(company=company, status="ACTIVE")
            if "driver" in self.fields:
                self.fields["driver"].queryset = Employee.objects.filter(
                    company=company, position__is_driver_role=True, is_active=True
                )


class ServiceLogForm(TailwindFormMixin, forms.ModelForm):
    """
    Form for Service Log Entry (Frontend - company is NOT editable)
    """
    class Meta:
        model = ServiceLog
        exclude = ["company"]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}),
            "description": forms.Textarea(attrs={"rows": 3}),
            "notes": forms.Textarea(attrs={"rows": 2}),
        }

    def __init__(self, *args, **kwargs):
        company = kwargs.pop("company", None)
        super().__init__(*args, **kwargs)

        # Auto-calc total_cost
        if "total_cost" in self.fields:
            self.fields["total_cost"].required = False

        if company and "vehicle" in self.fields:
            self.fields["vehicle"].queryset = Vehicle.objects.filter(company=company, status="ACTIVE")


class EmployeeForm(TailwindFormMixin, forms.ModelForm):
    """
    Form for Employee (Frontend - company is set server-side)
    """
    class Meta:
        model = Employee
        exclude = ["company"]  # All fields except company
        widgets = {
            "date_of_birth": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        self.company = kwargs.pop("company", None)
        super().__init__(*args, **kwargs)
        
        # Make salary fields optional (they have defaults in model)
        if "monthly_gross_salary" in self.fields:
            self.fields["monthly_gross_salary"].required = False
        if "employer_contributions_rate" in self.fields:
            self.fields["employer_contributions_rate"].required = False
        if "available_hours_per_year" in self.fields:
            self.fields["available_hours_per_year"].required = False


class DriverComplianceForm(TailwindFormMixin, forms.ModelForm):
    """
    Form for Driver Compliance (Frontend - employee/company scoped server-side)
    """

    # ADR: single-select UX (χωρίς να αλλάξουμε το model)
    adr_category = forms.ModelChoiceField(
        queryset=None,
        required=False,
        empty_label="— Χωρίς ADR —",
        label="Κατηγορία ADR (Single)",
        widget=forms.Select(),
    )

    class Meta:
        model = DriverCompliance
        fields = [
            "license_number",
            "license_expiry_date",
            "license_categories",
            "pei_truck_expiry",
            "pei_bus_expiry",
            "tachograph_card_number",
            "tachograph_card_expiry",
            # κρατάμε το adr_categories στο model (ManyToMany) αλλά ΔΕΝ θα το δείχνουμε στο UI
            "adr_categories",
            "adr_expiry",
        ]
        widgets = {
            "license_categories": forms.CheckboxSelectMultiple(),
            # adr_categories ΔΕΝ θα εμφανίζεται (θα γίνεται set μέσω adr_category)
        }
        labels = {
            "license_number": "Αριθμός Άδειας (Πεδίο 5 / 5β)",
            "license_expiry_date": "Λήξη Άδειας Οδήγησης",
            "tachograph_card_number": "Αριθμός Κάρτας Ταχογράφου (Πεδίο 5α)",
            "tachograph_card_expiry": "Λήξη Κάρτας Ταχογράφου (Πεδίο 4β)",
            "pei_truck_expiry": "Λήξη ΠΕΙ Φορτηγού",
            "pei_bus_expiry": "Λήξη ΠΕΙ Λεωφορείου",
            "adr_expiry": "Λήξη ADR",
        }

    def __init__(self, *args, **kwargs):
        # Get instance BEFORE calling super
        instance = kwargs.get('instance', None)
        
        # Call parent to initialize form
        super().__init__(*args, **kwargs)

        # 1) FORCE date widgets with format attribute (like license_expiry_date in Meta)
        for f in [
            "license_expiry_date",
            "pei_truck_expiry",
            "pei_bus_expiry",
            "tachograph_card_expiry",
            "adr_expiry",
        ]:
            if f in self.fields:
                self.fields[f].widget = forms.DateInput(
                    attrs={"type": "date"},
                    format='%Y-%m-%d'
                )

        # 2) Mην αφήνεις το Tailwind mixin να "σπάει" τα checkbox widgets
        if "license_categories" in self.fields:
            self.fields["license_categories"].widget.attrs.pop("class", None)

        # 3) Κρύψε το adr_categories (το model field), θα το χειριζόμαστε μέσω adr_category
        if "adr_categories" in self.fields:
            self.fields["adr_categories"].required = False
            self.fields["adr_categories"].widget = forms.MultipleHiddenInput()

        # 4) Φέρε queryset για adr_category από το ίδιο relation του model
        try:
            from core.driver_compliance_models import AdrCategory
            self.fields["adr_category"].queryset = AdrCategory.objects.all().order_by('display_order')
        except Exception:
            self.fields["adr_category"].queryset = None

        # 5) Αν υπάρχει ήδη ADR επιλογή, κάνε prefill το single-select
        # FIX: Set initial value from existing instance
        # CRITICAL: Must reload from DB to get M2M data
        if instance and instance.pk:
            try:
                # Reload instance from DB to ensure M2M is loaded
                from core.driver_compliance_models import DriverCompliance
                fresh_instance = DriverCompliance.objects.prefetch_related('adr_categories').get(pk=instance.pk)
                
                # Get first ADR category if exists
                first_adr = fresh_instance.adr_categories.first()
                if first_adr:
                    # Set initial to the pk
                    self.fields["adr_category"].initial = first_adr.pk
                    # ALSO set in self.initial dict
                    self.initial["adr_category"] = first_adr.pk
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Failed to load ADR category initial: {e}")

    # -------------------------
    # HARD VALIDATIONS
    # -------------------------
    def clean_license_number(self):
        v = (self.cleaned_data.get("license_number") or "").strip()
        if not re.fullmatch(r"\d{9}", v):
            raise forms.ValidationError("Ο αριθμός άδειας πρέπει να είναι ΑΚΡΙΒΩΣ 9 ψηφία.")
        return v

    def clean_tachograph_card_number(self):
        v = (self.cleaned_data.get("tachograph_card_number") or "").strip().replace(" ", "").upper()
        # Allow empty (optional field)
        if not v:
            return ""
        # 16 αλφαριθμητικοί (14 driver id + 1 replace + 1 renewal)
        if not re.fullmatch(r"[A-Z0-9]{16}", v):
            raise forms.ValidationError(
                "Ο αριθμός κάρτας ταχογράφου (5α) πρέπει να είναι ΑΚΡΙΒΩΣ 16 αλφαριθμητικοί χαρακτήρες."
            )
        return v

    def clean(self):
        cleaned = super().clean()

        adr_expiry = cleaned.get("adr_expiry")
        adr_category = cleaned.get("adr_category")
        adr_categories = cleaned.get("adr_categories")  # μπορεί να έρθει από tests

        # Backward compatibility: check both adr_category (UI) and adr_categories (tests/API)
        has_adr_selection = False
        if adr_category:
            has_adr_selection = True
        elif adr_categories is not None:
            # όταν έρχεται από POST ως M2M
            try:
                has_adr_selection = adr_categories.exists()
            except Exception:
                has_adr_selection = bool(adr_categories)

        # ADR rule: selection + expiry consistency
        if has_adr_selection and not adr_expiry:
            raise forms.ValidationError(
                "Αν επιλέξετε ADR, πρέπει να ορίσετε ημερομηνία λήξης ADR."
            )
        if adr_expiry and not has_adr_selection:
            raise forms.ValidationError(
                "Αν ορίσετε ημερομηνία λήξης ADR, πρέπει να επιλέξετε ADR."
            )

        return cleaned


    def save(self, commit=True):
        """
        Σώζει το instance.
        CRITICAL: Do NOT call _apply_adr_single_select here!
        It will be called by save_m2m() which is the proper place for M2M operations.
        """
        instance = super().save(commit=commit)
        return instance

    def save_m2m(self):
        """
        Override save_m2m to ensure ADR single-select is applied
        """
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info(f"[SAVE_M2M] Called. Instance pk: {self.instance.pk}")
        logger.info(f"[SAVE_M2M] Before super().save_m2m()")
        
        super().save_m2m()
        
        logger.info(f"[SAVE_M2M] After super().save_m2m()")
        logger.info(f"[SAVE_M2M] ADR count before _apply_adr_single_select: {self.instance.adr_categories.count()}")
        
        # Apply ADR single-select after all M2M are saved
        if self.instance.pk:
            self._apply_adr_single_select(self.instance)
            
        logger.info(f"[SAVE_M2M] ADR count after _apply_adr_single_select: {self.instance.adr_categories.count()}")

    def _apply_adr_single_select(self, instance):
        """
        Apply single-select ADR category to M2M field
        """
        import logging
        logger = logging.getLogger(__name__)
        
        adr_category = self.cleaned_data.get("adr_category")
        adr_categories = self.cleaned_data.get("adr_categories")

        logger.info(f"[ADR_SAVE] adr_category from form: {adr_category}")
        logger.info(f"[ADR_SAVE] adr_categories from form: {adr_categories}")

        if adr_category:
            logger.info(f"[ADR_SAVE] Setting adr_categories to [{adr_category}]")
            instance.adr_categories.set([adr_category])
            logger.info(f"[ADR_SAVE] After set, count: {instance.adr_categories.count()}")
            return

        # Αν δεν υπάρχει adr_category, αλλά το form πήρε adr_categories (tests / legacy)
        if adr_categories is not None:
            logger.info(f"[ADR_SAVE] Setting adr_categories from legacy field")
            instance.adr_categories.set(list(adr_categories))
            return

        logger.info(f"[ADR_SAVE] Clearing adr_categories (no selection)")
        instance.adr_categories.clear()


class VehicleForm(TailwindFormMixin, forms.ModelForm):
    """
    Form for creating/editing Fleet Vehicles
    """
    class Meta:
        model = Vehicle
        fields = [
            "license_plate", "vin", "make", "model", "color", "manufacturing_year",
            "first_registration_date", "acquisition_date",
            "vehicle_class", "body_type",
            "length_total_m", "width_m", "height_m",
            "cargo_length_m", "cargo_width_m", "cargo_height_m",
            "gross_weight_kg", "unladen_weight_kg",
            "horsepower", "engine_capacity_cc", "fuel_type", "emission_class", "tank_capacity",
            "seats",
            "purchase_value", "available_hours_per_year",
            "status", "current_odometer",
            "notes",
        ]
        widgets = {
            "license_plate": forms.TextInput(attrs={"placeholder": "Κωδικός A"}),
            "vin": forms.TextInput(attrs={"placeholder": "Κωδικός E - 17 ψηφία"}),
            "make": forms.TextInput(attrs={"placeholder": "Κωδικός D.1"}),
            "model": forms.TextInput(attrs={"placeholder": "Κωδικός D.2"}),
            "color": forms.TextInput(attrs={"placeholder": "Κωδικός R"}),
            "manufacturing_year": forms.NumberInput(attrs={"placeholder": "2020"}),
            "first_registration_date": forms.DateInput(attrs={"type": "date", "placeholder": "Κωδικός B"}),
            "acquisition_date": forms.DateInput(attrs={"type": "date"}),
            "length_total_m": forms.NumberInput(attrs={"placeholder": "Κωδικός L", "step": "0.01"}),
            "width_m": forms.NumberInput(attrs={"placeholder": "Εξωτερικό πλάτος", "step": "0.01"}),
            "height_m": forms.NumberInput(attrs={"placeholder": "Εξωτερικό ύψος", "step": "0.01"}),
            "cargo_length_m": forms.NumberInput(attrs={"placeholder": "Εσωτερικό μήκος", "step": "0.01"}),
            "cargo_width_m": forms.NumberInput(attrs={"placeholder": "Εσωτερικό πλάτος", "step": "0.01"}),
            "cargo_height_m": forms.NumberInput(attrs={"placeholder": "Εσωτερικό ύψος", "step": "0.01"}),
            "gross_weight_kg": forms.NumberInput(attrs={"placeholder": "Κωδικός F.1"}),
            "unladen_weight_kg": forms.NumberInput(attrs={"placeholder": "Κωδικός G"}),
            "horsepower": forms.NumberInput(attrs={"placeholder": "Κωδικός P.2"}),
            "engine_capacity_cc": forms.NumberInput(attrs={"placeholder": "Κωδικός P.1"}),
            "tank_capacity": forms.NumberInput(attrs={"placeholder": "Λίτρα/kWh", "step": "0.01"}),
            "seats": forms.NumberInput(attrs={"placeholder": "Κωδικός S.1"}),
            "purchase_value": forms.NumberInput(attrs={"placeholder": "Αξία αγοράς", "step": "0.01"}),
            "available_hours_per_year": forms.NumberInput(attrs={"placeholder": "1936"}),
            "current_odometer": forms.NumberInput(attrs={"placeholder": "Τρέχοντα km"}),
            "notes": forms.Textarea(attrs={"rows": 3, "placeholder": "Σημειώσεις"}),
        }

    def __init__(self, *args, **kwargs):
        kwargs.pop("company", None)  # accept but ignore; company is server-side
        super().__init__(*args, **kwargs)


class CompanyForm(TailwindFormMixin, forms.ModelForm):
    """
    Form for editing Company details
    """
    class Meta:
        model = Company
        fields = ["name", "transport_type", "tax_id", "address", "phone", "email"]
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "π.χ. GreekFleet Transport"}),
            "tax_id": forms.TextInput(attrs={"placeholder": "π.χ. 123456789"}),
            "address": forms.Textarea(attrs={"rows": 3, "placeholder": "Διεύθυνση εταιρείας"}),
            "phone": forms.TextInput(attrs={"placeholder": "π.χ. 2101234567"}),
            "email": forms.EmailInput(attrs={"placeholder": "π.χ. info@company.gr"}),
        }
        labels = {
            "name": "Επωνυμία Εταιρείας",
            "transport_type": "Τύπος Μεταφορών",
            "tax_id": "ΑΦΜ",
            "address": "Διεύθυνση",
            "phone": "Τηλέφωνο",
            "email": "Email",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk and self.instance.tax_id:
            self.fields["tax_id"].widget.attrs["readonly"] = True
            self.fields["tax_id"].widget.attrs["class"] += " bg-gray-100 cursor-not-allowed"
            self.fields["tax_id"].help_text = "Κλειδωμένο μετά την αποθήκευση."

    def clean_tax_id(self):
        import re
        value = (self.cleaned_data.get("tax_id") or "").strip()
        if value and not re.fullmatch(r"\d{9}", value):
            raise forms.ValidationError("Το ΑΦΜ πρέπει να αποτελείται από 9 ψηφία.")
        if self.instance and self.instance.pk:
            existing = (self.instance.tax_id or "").strip()
            if existing and value != existing:
                raise forms.ValidationError(
                    "Το ΑΦΜ δεν μπορεί να αλλάξει αφού αποθηκευτεί. "
                    "Επικοινωνήστε με τον διαχειριστή."
                )
        return value


class CompanyUserForm(TailwindFormMixin, forms.ModelForm):
    """
    Form for creating/editing Company Users
    """
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={"placeholder": "Κωδικός πρόσβασης"}),
        required=False,
        label="Κωδικός Πρόσβασης",
        help_text="Αφήστε κενό για να κρατήσετε τον υπάρχοντα κωδικό",
    )
    role = forms.ChoiceField(
        choices=UserProfile.ROLE_CHOICES,
        label="Ρόλος",
        widget=forms.Select(),
    )

    class Meta:
        model = User
        fields = ["first_name", "last_name", "email", "username"]
        widgets = {
            "first_name": forms.TextInput(attrs={"placeholder": "π.χ. Γιώργος"}),
            "last_name": forms.TextInput(attrs={"placeholder": "π.χ. Παπαδόπουλος"}),
            "email": forms.EmailInput(attrs={"placeholder": "π.χ. user@company.gr"}),
            "username": forms.TextInput(attrs={"placeholder": "π.χ. gpapadopoulos"}),
        }
        labels = {
            "first_name": "Όνομα",
            "last_name": "Επώνυμο",
            "email": "Email",
            "username": "Username",
        }


class ExpenseCategoryForm(TailwindFormMixin, forms.ModelForm):
    """
    Form for creating custom Expense Categories
    """
    class Meta:
        model = ExpenseCategory
        fields = ["family", "name", "description"]
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "π.χ. Ενοίκιο Γραφείου"}),
            "description": forms.Textarea(attrs={"rows": 2, "placeholder": "Περιγραφή κατηγορίας"}),
        }
        labels = {
            "family": "Οικογένεια Εξόδων",
            "name": "Όνομα Κατηγορίας",
            "description": "Περιγραφή",
        }


class CompanyUserEditForm(TailwindFormMixin, forms.ModelForm):
    """
    Form for editing existing Company Users (ADMIN-only)
    """
    role = forms.ChoiceField(
        choices=UserProfile.ROLE_CHOICES,
        label="Ρόλος",
        widget=forms.Select(),
    )

    class Meta:
        model = User
        fields = ["first_name", "last_name", "email"]
        widgets = {
            "first_name": forms.TextInput(attrs={"placeholder": "π.χ. Γιώργος"}),
            "last_name": forms.TextInput(attrs={"placeholder": "π.χ. Παπαδόπουλος"}),
            "email": forms.EmailInput(attrs={"placeholder": "π.χ. user@company.gr"}),
        }
        labels = {
            "first_name": "Όνομα",
            "last_name": "Επώνυμο",
            "email": "Email",
        }

    def __init__(self, *args, **kwargs):
        self.company = kwargs.pop("company", None)
        self.is_self = kwargs.pop("is_self", False)
        super().__init__(*args, **kwargs)

        self.fields["email"].required = True

        if self.is_self:
            self.fields["role"].widget.attrs["disabled"] = True
            self.fields["role"].help_text = "Δεν μπορείτε να αλλάξετε τον δικό σας ρόλο"

        if self.instance and self.instance.pk:
            try:
                self.fields["role"].initial = self.instance.profile.role
            except AttributeError:
                pass

    def clean_email(self):
        email = (self.cleaned_data.get("email", "") or "").strip().lower()
        if not email:
            raise forms.ValidationError("Το email είναι υποχρεωτικό.")

        if self.company:
            existing_user = (
                User.objects.filter(email__iexact=email, profile__company=self.company)
                .exclude(pk=self.instance.pk if self.instance else None)
                .first()
            )
            if existing_user:
                raise forms.ValidationError(
                    f'Το email "{email}" χρησιμοποιείται ήδη από άλλο χρήστη της εταιρείας.'
                )

        return email