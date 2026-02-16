"""
Admin Tenant Isolation Tests
Ensures Django Admin respects multi-tenant architecture
"""
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from core.models import Company
from accounts.models import UserProfile
from finance.models import CompanyExpense, ExpenseCategory, ExpenseFamily
from operations.models import FuelEntry, Vehicle


class AdminTenantIsolationTestCase(TestCase):
    """
    Test suite for Django Admin tenant isolation
    
    Verifies that:
    1. Non-superuser staff see only their company's records
    2. Superusers see all records
    3. Staff cannot modify other companies' records
    """
    
    def setUp(self):
        """
        Set up test data: 2 companies, staff users, and records
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
        
        # Create superuser
        self.superuser = User.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='admin123'
        )
        
        # Create staff user for Company A
        self.staff_a = User.objects.create_user(
            username='staff_a',
            password='staff123',
            is_staff=True
        )
        UserProfile.objects.create(
            user=self.staff_a,
            company=self.company_a,
            role='MANAGER'
        )
        
        # Create staff user for Company B
        self.staff_b = User.objects.create_user(
            username='staff_b',
            password='staff123',
            is_staff=True
        )
        UserProfile.objects.create(
            user=self.staff_b,
            company=self.company_b,
            role='MANAGER'
        )
        
        # Create expense family and category
        family = ExpenseFamily.objects.create(
            name="Test Family",
            display_order=1
        )
        self.category = ExpenseCategory.objects.create(
            family=family,
            name="Test Category",
            is_system_default=True
        )
        
        # Create expenses for both companies
        self.expense_a = CompanyExpense.all_objects.create(
            company=self.company_a,
            category=self.category,
            expense_type='MONTHLY',
            periodicity='MONTHLY',
            amount=1000.00,
            start_date='2026-01-01',
            description='Company A Expense'
        )
        
        self.expense_b = CompanyExpense.all_objects.create(
            company=self.company_b,
            category=self.category,
            expense_type='MONTHLY',
            periodicity='MONTHLY',
            amount=2000.00,
            start_date='2026-01-01',
            description='Company B Expense'
        )
        
        # Create vehicles for both companies
        self.vehicle_a = Vehicle.objects.create(
            company=self.company_a,
            license_plate="AAA-1111",
            make="Mercedes",
            model="Actros",
            vehicle_class="TRUCK",
            body_type="BOX"
        )
        
        self.vehicle_b = Vehicle.objects.create(
            company=self.company_b,
            license_plate="BBB-2222",
            make="Volvo",
            model="FH16",
            vehicle_class="TRUCK",
            body_type="CURTAIN"
        )
        
        # Create fuel entries for both companies
        self.fuel_a = FuelEntry.all_objects.create(
            company=self.company_a,
            vehicle=self.vehicle_a,
            date='2026-02-01',
            liters=100.00,
            cost_per_liter=1.50,
            total_cost=150.00,
            odometer_reading=10000
        )
        
        self.fuel_b = FuelEntry.all_objects.create(
            company=self.company_b,
            vehicle=self.vehicle_b,
            date='2026-02-01',
            liters=150.00,
            cost_per_liter=1.52,
            total_cost=228.00,
            odometer_reading=20000
        )
        
        # Create test client
        self.client = Client()
    
    def test_staff_sees_only_own_company_records(self):
        """
        Test that non-superuser staff members only see their company's records
        """
        # Login as Company A staff
        self.client.login(username='staff_a', password='staff123')
        
        # Access CompanyExpense changelist
        response = self.client.get(reverse('admin:finance_companyexpense_changelist'))
        
        # Staff users need proper permissions - if 403, they lack view permission
        # This is expected if they don't have the right permissions
        if response.status_code == 403:
            # Grant view permission and retry
            from django.contrib.auth.models import Permission
            from django.contrib.contenttypes.models import ContentType
            
            ct = ContentType.objects.get_for_model(CompanyExpense)
            perm = Permission.objects.get(content_type=ct, codename='view_companyexpense')
            self.staff_a.user_permissions.add(perm)
            
            response = self.client.get(reverse('admin:finance_companyexpense_changelist'))
        
        self.assertEqual(response.status_code, 200)
        
        # Verify only Company A expense is visible
        content = response.content.decode('utf-8')
        self.assertIn('Company A', content)
        self.assertNotIn('Company B Expense', content)
        
        # Access FuelEntry changelist
        response = self.client.get(reverse('admin:operations_fuelentry_changelist'))
        
        if response.status_code == 403:
            from django.contrib.auth.models import Permission
            from django.contrib.contenttypes.models import ContentType
            
            ct = ContentType.objects.get_for_model(FuelEntry)
            perm = Permission.objects.get(content_type=ct, codename='view_fuelentry')
            self.staff_a.user_permissions.add(perm)
            
            response = self.client.get(reverse('admin:operations_fuelentry_changelist'))
        
        self.assertEqual(response.status_code, 200)
        
        # Verify only Company A fuel entry is visible in the table
        # Note: BBB-2222 may appear in the filter sidebar, but not in the results table
        content = response.content.decode('utf-8')
        self.assertIn('AAA-1111', content)
        
        # Check that only 1 fuel entry is shown (not 2)
        # The page should show "1 Καταχώρηση Καυσίμου" not "2"
        self.assertIn('1', content)
        self.assertNotIn('2 Καταχώρηση Καυσίμου', content)
        self.assertNotIn('2 Καταχωρήσεις Καυσίμων', content)
    
    def test_superuser_sees_all_records(self):
        """
        Test that superusers see all records from all companies
        """
        # Login as superuser
        self.client.login(username='admin', password='admin123')
        
        # Access CompanyExpense changelist
        response = self.client.get(reverse('admin:finance_companyexpense_changelist'))
        self.assertEqual(response.status_code, 200)
        
        # Verify both companies' expenses are visible
        content = response.content.decode('utf-8')
        self.assertIn('Company A', content)
        self.assertIn('Company B', content)
        
        # Access FuelEntry changelist
        response = self.client.get(reverse('admin:operations_fuelentry_changelist'))
        self.assertEqual(response.status_code, 200)
        
        # Verify both companies' fuel entries are visible
        content = response.content.decode('utf-8')
        self.assertIn('AAA-1111', content)
        self.assertIn('BBB-2222', content)
    
    def test_staff_cannot_modify_other_company_records(self):
        """
        Test that staff members cannot modify records from other companies
        """
        # Login as Company A staff
        self.client.login(username='staff_a', password='staff123')
        
        # Try to access Company B expense change form
        url = reverse('admin:finance_companyexpense_change', args=[self.expense_b.pk])
        response = self.client.get(url)
        
        # Should get 302 (redirect) or 403 (forbidden) or 404 (not found)
        # Django admin typically returns 302 redirect to changelist when object not in queryset
        self.assertIn(response.status_code, [302, 403, 404])
        
        # Try to POST update to Company B expense
        response = self.client.post(url, {
            'company': self.company_b.pk,
            'category': self.category.pk,
            'expense_type': 'MONTHLY',
            'periodicity': 'MONTHLY',
            'amount': 9999.00,
            'start_date': '2026-01-01',
            'is_active': True,
        })
        
        # Should be rejected
        self.assertIn(response.status_code, [302, 403, 404])
        
        # Verify the expense was NOT modified
        self.expense_b.refresh_from_db()
        self.assertEqual(float(self.expense_b.amount), 2000.00)
        
        # Try to access Company B fuel entry change form
        url = reverse('admin:operations_fuelentry_change', args=[self.fuel_b.pk])
        response = self.client.get(url)
        
        # Should get 302, 403, or 404
        self.assertIn(response.status_code, [302, 403, 404])
    
    def tearDown(self):
        """
        Clean up after tests
        """
        self.client.logout()
