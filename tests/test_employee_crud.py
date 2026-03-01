"""
Employee CRUD Tests
Tests for Employee Create, Read, Update, Delete operations with HTMX modals
"""
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from core.models import Company, Employee, EmployeePosition
from accounts.models import UserProfile


class EmployeeCRUDTestCase(TestCase):
    """
    Test suite for Employee CRUD operations
    
    Verifies:
    1. Employee creation via HTMX modal
    2. Employee editing via HTMX modal
    3. Employee deletion
    4. Tenant isolation (users can only manage their company's employees)
    5. Form validation
    """
    
    def setUp(self):
        """
        Set up test data: 2 companies, users, and employee positions
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
        
        # Create employees for both companies
        self.employee_a = Employee.objects.create(
            company=self.company_a,
            first_name="Γιώργος",
            last_name="Παπαδόπουλος",
            position=self.position_driver,
            email="gpapadopoulos@companya.gr",
            phone="6901234567",
            is_active=True
        )
        
        self.employee_b = Employee.objects.create(
            company=self.company_b,
            first_name="Μαρία",
            last_name="Ιωάννου",
            position=self.position_manager,
            email="mioannou@companyb.gr",
            phone="6909876543",
            is_active=True
        )
        
        # Create test client
        self.client = Client()
    
    def test_employee_create_get_modal(self):
        """
        Test GET request to employee_create returns modal form
        """
        # Login as User A
        self.client.login(username='user_a', password='testpass123')
        
        # GET request with HTMX header
        response = self.client.get(
            reverse('web:employee_create'),
            HTTP_HX_REQUEST='true'
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'partials/employee_form_modal.html')
        self.assertIn('form', response.context)
        self.assertEqual(response.context['title'], 'Προσθήκη Υπαλλήλου')
    
    def test_employee_create_post_success(self):
        """
        Test POST request to employee_create successfully creates employee
        """
        # Login as User A
        self.client.login(username='user_a', password='testpass123')
        
        # Count employees before
        initial_count = Employee.objects.filter(company=self.company_a).count()
        
        # POST request with valid data
        response = self.client.post(
            reverse('web:employee_create'),
            {
                'first_name': 'Νίκος',
                'last_name': 'Κωνσταντίνου',
                'position': self.position_driver.id,
                'email': 'nkonstantinou@companya.gr',
                'phone': '6901111111',
                'monthly_gross_salary': '1500.00',
                'employer_contributions_rate': '0.22',
                'available_hours_per_year': '1936',
            },
            HTTP_HX_REQUEST='true'
        )
        
        # Should return 204 with HX-Redirect header
        self.assertEqual(response.status_code, 204)
        self.assertIn('HX-Redirect', response.headers)
        
        # Verify employee was created
        new_count = Employee.objects.filter(company=self.company_a).count()
        self.assertEqual(new_count, initial_count + 1)
        
        # Verify employee data
        new_employee = Employee.objects.get(
            company=self.company_a,
            first_name='Νίκος',
            last_name='Κωνσταντίνου'
        )
        self.assertEqual(new_employee.position, self.position_driver)
        self.assertEqual(new_employee.email, 'nkonstantinou@companya.gr')
        self.assertTrue(new_employee.is_active)
    
    def test_employee_create_post_validation_error(self):
        """
        Test POST request with invalid data returns form with errors
        """
        # Login as User A
        self.client.login(username='user_a', password='testpass123')
        
        # POST request with missing required fields
        response = self.client.post(
            reverse('web:employee_create'),
            {
                'first_name': '',  # Missing
                'last_name': 'Κωνσταντίνου',
                'position': self.position_driver.id,
            },
            HTTP_HX_REQUEST='true'
        )
        
        # Should return 200 with form errors
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'partials/employee_form_modal.html')
        self.assertIn('form', response.context)
        self.assertTrue(response.context['form'].errors)
    
    def test_employee_edit_get_modal(self):
        """
        Test GET request to employee_edit returns modal form with employee data
        """
        # Login as User A
        self.client.login(username='user_a', password='testpass123')
        
        # GET request with HTMX header
        response = self.client.get(
            reverse('web:employee_edit', args=[self.employee_a.id]),
            HTTP_HX_REQUEST='true'
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'partials/employee_form_modal.html')
        self.assertIn('form', response.context)
        self.assertEqual(response.context['title'], 'Επεξεργασία Υπαλλήλου')
        self.assertEqual(response.context['employee_id'], self.employee_a.id)
        
        # Verify form is populated with employee data
        form = response.context['form']
        self.assertEqual(form.instance, self.employee_a)
    
    def test_employee_edit_post_success(self):
        """
        Test POST request to employee_edit successfully updates employee
        """
        # Login as User A
        self.client.login(username='user_a', password='testpass123')
        
        # POST request with updated data
        response = self.client.post(
            reverse('web:employee_edit', args=[self.employee_a.id]),
            {
                'first_name': 'Γιώργος',
                'last_name': 'Παπαδόπουλος',
                'position': self.position_manager.id,  # Changed position
                'email': 'gpapadopoulos_updated@companya.gr',  # Changed email
                'phone': '6901234567',
                'monthly_gross_salary': '1500.00',
                'employer_contributions_rate': '0.22',
                'available_hours_per_year': '1936',
            },
            HTTP_HX_REQUEST='true'
        )
        
        # Should return 204 with HX-Redirect header
        self.assertEqual(response.status_code, 204)
        self.assertIn('HX-Redirect', response.headers)
        
        # Verify employee was updated
        self.employee_a.refresh_from_db()
        self.assertEqual(self.employee_a.position, self.position_manager)
        self.assertEqual(self.employee_a.email, 'gpapadopoulos_updated@companya.gr')
    
    def test_employee_edit_tenant_isolation(self):
        """
        Test that User A cannot edit Company B's employee
        """
        # Login as User A
        self.client.login(username='user_a', password='testpass123')
        
        # Try to access Company B employee edit form
        response = self.client.get(
            reverse('web:employee_edit', args=[self.employee_b.id]),
            HTTP_HX_REQUEST='true'
        )
        
        # Should get 404 (not found in scoped queryset)
        self.assertEqual(response.status_code, 404)
    
    def test_employee_delete_success(self):
        """
        Test DELETE request successfully deletes employee
        """
        # Login as User A
        self.client.login(username='user_a', password='testpass123')
        
        # Count employees before
        initial_count = Employee.objects.filter(company=self.company_a).count()
        
        # POST request to delete (HTMX uses POST for delete)
        response = self.client.post(
            reverse('web:employee_delete', args=[self.employee_a.id])
        )
        
        # Should return 200 with empty response
        self.assertEqual(response.status_code, 200)
        
        # Verify employee was deleted
        new_count = Employee.objects.filter(company=self.company_a).count()
        self.assertEqual(new_count, initial_count - 1)
        
        # Verify employee no longer exists
        with self.assertRaises(Employee.DoesNotExist):
            Employee.objects.get(id=self.employee_a.id)
    
    def test_employee_delete_tenant_isolation(self):
        """
        Test that User A cannot delete Company B's employee
        """
        # Login as User A
        self.client.login(username='user_a', password='testpass123')
        
        # Try to delete Company B employee
        response = self.client.post(
            reverse('web:employee_delete', args=[self.employee_b.id])
        )
        
        # Should get 404 (not found in scoped queryset)
        self.assertEqual(response.status_code, 404)
        
        # Verify employee still exists
        self.assertTrue(
            Employee.objects.filter(id=self.employee_b.id).exists()
        )
    
    def test_employee_create_without_htmx_redirects(self):
        """
        Test that non-HTMX GET request to employee_create redirects
        """
        # Login as User A
        self.client.login(username='user_a', password='testpass123')
        
        # GET request WITHOUT HTMX header
        response = self.client.get(reverse('web:employee_create'))
        
        # Should redirect to finance_settings
        self.assertEqual(response.status_code, 302)
        self.assertIn('finance/settings', response.url)
    
    def test_employee_list_in_finance_settings(self):
        """
        Test that finance_settings view includes employees list
        """
        # Login as User A
        self.client.login(username='user_a', password='testpass123')
        
        # GET finance_settings page
        response = self.client.get(reverse('web:finance_settings'))
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('employees', response.context)
        
        # Verify only Company A employees are shown
        employees = response.context['employees']
        employee_ids = [e.id for e in employees]
        self.assertIn(self.employee_a.id, employee_ids)
        self.assertNotIn(self.employee_b.id, employee_ids)
    
    def test_employee_form_scopes_position_choices(self):
        """
        Test that EmployeeForm properly handles position choices
        """
        # Login as User A
        self.client.login(username='user_a', password='testpass123')
        
        # GET employee create form
        response = self.client.get(
            reverse('web:employee_create'),
            HTTP_HX_REQUEST='true'
        )
        
        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        
        # Verify position field exists and has choices
        self.assertIn('position', form.fields)
        position_field = form.fields['position']
        
        # Verify both positions are available (not company-scoped)
        position_choices = [choice[0] for choice in position_field.choices if choice[0]]
        self.assertIn(self.position_driver.id, position_choices)
        self.assertIn(self.position_manager.id, position_choices)
    
    def tearDown(self):
        """
        Clean up after tests
        """
        self.client.logout()


class EmployeeFormValidationTestCase(TestCase):
    """
    Test suite for EmployeeForm validation
    """
    
    def setUp(self):
        """
        Set up test data
        """
        self.company = Company.objects.create(
            name="Test Company",
            tax_id="999999999",
            transport_type="FREIGHT"
        )
        
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        UserProfile.objects.create(
            user=self.user,
            company=self.company,
            role='ADMIN'
        )
        
        self.position = EmployeePosition.objects.create(
            title="Οδηγός",
            is_driver_role=True
        )
        
        self.client = Client()
        self.client.login(username='testuser', password='testpass123')
    
    def test_required_fields(self):
        """
        Test that required fields are enforced
        """
        # POST with missing first_name
        response = self.client.post(
            reverse('web:employee_create'),
            {
                'first_name': '',
                'last_name': 'Παπαδόπουλος',
                'position': self.position.id,
            },
            HTTP_HX_REQUEST='true'
        )
        
        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertIn('first_name', form.errors)
    
    def test_optional_fields(self):
        """
        Test that optional fields (email, phone) are not required
        """
        # POST without email and phone (but with required salary fields)
        response = self.client.post(
            reverse('web:employee_create'),
            {
                'first_name': 'Νίκος',
                'last_name': 'Κωνσταντίνου',
                'position': self.position.id,
                'monthly_gross_salary': '1500.00',
                'employer_contributions_rate': '0.22',
                'available_hours_per_year': '1936',
            },
            HTTP_HX_REQUEST='true'
        )
        
        # Should succeed
        self.assertEqual(response.status_code, 204)
        
        # Verify employee was created
        employee = Employee.objects.get(
            company=self.company,
            first_name='Νίκος',
            last_name='Κωνσταντίνου'
        )
        self.assertEqual(employee.email, '')
        self.assertEqual(employee.phone, '')
    
    def tearDown(self):
        """
        Clean up after tests
        """
        self.client.logout()
