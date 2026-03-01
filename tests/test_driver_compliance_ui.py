"""
Driver Compliance UI Tests
Tests for HTMX-based driver compliance management interface
"""
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from datetime import date, timedelta
from core.models import Company, Employee, EmployeePosition
from core.driver_compliance_models import DriverCompliance, DrivingLicenseCategory, AdrCategory
from accounts.models import UserProfile


class DriverComplianceUITestCase(TestCase):
    """
    Test suite for Driver Compliance UI (HTMX modals)
    
    Verifies:
    1. HTMX GET returns modal for same-company employee
    2. HTMX POST creates compliance with license fields and categories
    3. HTMX POST edits existing compliance
    4. Tenant isolation: cannot access or save compliance for other company employee
    5. ADR validation: category without expiry blocked, expiry without category blocked
    """
    
    def setUp(self):
        """
        Set up test data: companies, users, employees, positions
        """
        # Create Company A
        self.company_a = Company.objects.create(
            name="Company A",
            tax_id="111111111",
            transport_type="FREIGHT"
        )
        
        # Create Company B
        self.company_b = Company.objects.create(
            name="Company B",
            tax_id="222222222",
            transport_type="FREIGHT"
        )
        
        # Create User A (belongs to Company A)
        self.user_a = User.objects.create_user(
            username='user_a',
            password='testpass123'
        )
        UserProfile.objects.create(
            user=self.user_a,
            company=self.company_a,
            role='ADMIN'
        )
        
        # Create User B (belongs to Company B)
        self.user_b = User.objects.create_user(
            username='user_b',
            password='testpass123'
        )
        UserProfile.objects.create(
            user=self.user_b,
            company=self.company_b,
            role='ADMIN'
        )
        
        # Create Employee Positions
        self.position_driver = EmployeePosition.objects.create(
            title="Οδηγός",
            is_driver_role=True
        )
        
        self.position_manager = EmployeePosition.objects.create(
            title="Διευθυντής",
            is_driver_role=False
        )
        
        # Get License Categories (seeded by migration)
        self.license_b = DrivingLicenseCategory.objects.get(code='B')
        self.license_c = DrivingLicenseCategory.objects.get(code='C')
        self.license_ce = DrivingLicenseCategory.objects.get(code='CE')
        
        # Get ADR Category (seeded by migration)
        self.adr_p3 = AdrCategory.objects.get(code='Π3')
        
        # Create Driver (Company A)
        self.driver_a = Employee.objects.create(
            company=self.company_a,
            first_name="Γιώργος",
            last_name="Οδηγός",
            position=self.position_driver,
            is_active=True
        )
        
        # Create Driver (Company B)
        self.driver_b = Employee.objects.create(
            company=self.company_b,
            first_name="Μαρία",
            last_name="Οδηγός Β",
            position=self.position_driver,
            is_active=True
        )
        
        # Create Non-Driver (Company A)
        self.manager_a = Employee.objects.create(
            company=self.company_a,
            first_name="Νίκος",
            last_name="Διευθυντής",
            position=self.position_manager,
            is_active=True
        )
        
        # Create test client
        self.client = Client()
        self.client.login(username='user_a', password='testpass123')
    
    def test_get_compliance_modal_for_driver(self):
        """
        Test HTMX GET returns modal for driver
        """
        response = self.client.get(
            reverse('web:driver_compliance_form', args=[self.driver_a.id]),
            HTTP_HX_REQUEST='true'
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'partials/driver_compliance_modal.html')
        self.assertIn('form', response.context)
        self.assertIn('employee', response.context)
        self.assertEqual(response.context['employee'], self.driver_a)
    
    def test_create_compliance_success(self):
        """
        Test HTMX POST creates compliance with license fields
        """
        response = self.client.post(
            reverse('web:driver_compliance_save', args=[self.driver_a.id]),
            {
                'license_number': '123456789',  # Must be exactly 9 digits
                'license_expiry_date': (date.today() + timedelta(days=365)).strftime('%Y-%m-%d'),
                'license_categories': [self.license_c.id, self.license_ce.id],
                'pei_truck_expiry': (date.today() + timedelta(days=365)).strftime('%Y-%m-%d'),
                'tachograph_card_number': 'ABCD1234567890XY',  # Must be exactly 16 alphanumeric
                'tachograph_card_expiry': (date.today() + timedelta(days=365)).strftime('%Y-%m-%d'),
            },
            HTTP_HX_REQUEST='true'
        )
        
        # Should return 204 with HX-Redirect
        self.assertEqual(response.status_code, 204)
        self.assertIn('HX-Redirect', response.headers)
        
        # Verify compliance was created
        self.driver_a.refresh_from_db()
        self.assertTrue(hasattr(self.driver_a, 'driver_compliance'))
        compliance = self.driver_a.driver_compliance
        self.assertEqual(compliance.license_number, '123456789')
        self.assertTrue(compliance.has_license_category('C'))
        self.assertTrue(compliance.has_license_category('CE'))
    
    def test_edit_existing_compliance(self):
        """
        Test HTMX POST edits existing compliance
        """
        # Create initial compliance
        compliance = DriverCompliance.objects.create(
            employee=self.driver_a,
            license_number='111111111',  # Must be exactly 9 digits
            license_expiry_date=date.today() + timedelta(days=365)
        )
        compliance.license_categories.add(self.license_b)
        
        # Update compliance
        response = self.client.post(
            reverse('web:driver_compliance_save', args=[self.driver_a.id]),
            {
                'license_number': '999999999',  # Must be exactly 9 digits
                'license_expiry_date': (date.today() + timedelta(days=730)).strftime('%Y-%m-%d'),
                'license_categories': [self.license_c.id],
                'pei_truck_expiry': (date.today() + timedelta(days=365)).strftime('%Y-%m-%d'),
                'tachograph_card_number': 'ABCD1234567890XY',  # Add required field
                'tachograph_card_expiry': (date.today() + timedelta(days=365)).strftime('%Y-%m-%d'),
            },
            HTTP_HX_REQUEST='true'
        )
        
        # Debug: print form errors if validation fails
        if response.status_code == 200:
            print("Form errors:", response.context.get('form').errors if 'form' in response.context else 'No form in context')
        
        # Should return 204 with HX-Redirect
        self.assertEqual(response.status_code, 204)
        
        # Verify compliance was updated
        compliance.refresh_from_db()
        self.assertEqual(compliance.license_number, '999999999')
        self.assertTrue(compliance.has_license_category('C'))
        self.assertFalse(compliance.has_license_category('B'))
    
    def test_tenant_isolation_get(self):
        """
        Test that User A cannot access Company B driver compliance
        """
        response = self.client.get(
            reverse('web:driver_compliance_form', args=[self.driver_b.id]),
            HTTP_HX_REQUEST='true'
        )
        
        # Should get 404 (not found in scoped queryset)
        self.assertEqual(response.status_code, 404)
    
    def test_tenant_isolation_post(self):
        """
        Test that User A cannot save compliance for Company B driver
        """
        response = self.client.post(
            reverse('web:driver_compliance_save', args=[self.driver_b.id]),
            {
                'license_number': '123456789',  # Must be exactly 9 digits
                'license_expiry_date': (date.today() + timedelta(days=365)).strftime('%Y-%m-%d'),
                'license_categories': [self.license_c.id],
            },
            HTTP_HX_REQUEST='true'
        )
        
        # Should get 404 (not found in scoped queryset)
        self.assertEqual(response.status_code, 404)
        
        # Verify no compliance was created for driver_b
        self.assertFalse(hasattr(self.driver_b, 'driver_compliance'))
    
    def test_block_non_driver_compliance(self):
        """
        Test that non-driver employee cannot have compliance
        """
        response = self.client.get(
            reverse('web:driver_compliance_form', args=[self.manager_a.id]),
            HTTP_HX_REQUEST='true'
        )
        
        # Should get 403 (not a driver)
        self.assertEqual(response.status_code, 403)
    
    def test_adr_validation_category_without_expiry(self):
        """
        Test that ADR category without expiry is blocked
        """
        response = self.client.post(
            reverse('web:driver_compliance_save', args=[self.driver_a.id]),
            {
                'license_number': '123456789',  # Must be exactly 9 digits
                'license_expiry_date': (date.today() + timedelta(days=365)).strftime('%Y-%m-%d'),
                'license_categories': [self.license_c.id],
                'adr_categories': [self.adr_p3.id],  # ADR category selected
                'adr_expiry': '',  # But no expiry
            },
            HTTP_HX_REQUEST='true'
        )
        
        # Should return 200 with form errors
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'partials/driver_compliance_modal.html')
        self.assertIn('ADR', str(response.content.decode()))
    
    def test_adr_validation_expiry_without_category(self):
        """
        Test that ADR expiry without category is blocked
        """
        response = self.client.post(
            reverse('web:driver_compliance_save', args=[self.driver_a.id]),
            {
                'license_number': '123456789',  # Must be exactly 9 digits
                'license_expiry_date': (date.today() + timedelta(days=365)).strftime('%Y-%m-%d'),
                'license_categories': [self.license_c.id],
                'adr_categories': [],  # No ADR category
                'adr_expiry': (date.today() + timedelta(days=365)).strftime('%Y-%m-%d'),  # But expiry set
            },
            HTTP_HX_REQUEST='true'
        )
        
        # Should return 200 with form errors
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'partials/driver_compliance_modal.html')
        self.assertIn('ADR', str(response.content.decode()))
    
    def test_adr_valid_both_set(self):
        """
        Test that ADR with both category and expiry is allowed
        """
        response = self.client.post(
            reverse('web:driver_compliance_save', args=[self.driver_a.id]),
            {
                'license_number': '123456789',  # Must be exactly 9 digits
                'license_expiry_date': (date.today() + timedelta(days=365)).strftime('%Y-%m-%d'),
                'license_categories': [self.license_c.id],
                'adr_categories': [self.adr_p3.id],
                'adr_expiry': (date.today() + timedelta(days=365)).strftime('%Y-%m-%d'),
                'tachograph_card_number': 'ABCD1234567890XY',  # Add required field
                'tachograph_card_expiry': (date.today() + timedelta(days=365)).strftime('%Y-%m-%d'),
            },
            HTTP_HX_REQUEST='true'
        )
        
        # Debug: print form errors if validation fails
        if response.status_code == 200:
            print("Form errors:", response.context.get('form').errors if 'form' in response.context else 'No form in context')
        
        # Should return 204 with HX-Redirect
        self.assertEqual(response.status_code, 204)
        
        # Verify compliance was created with ADR
        self.driver_a.refresh_from_db()
        compliance = self.driver_a.driver_compliance
        self.assertTrue(compliance.has_any_adr_category())
        self.assertIsNotNone(compliance.adr_expiry)
    
    def tearDown(self):
        """
        Clean up after tests
        """
        self.client.logout()
