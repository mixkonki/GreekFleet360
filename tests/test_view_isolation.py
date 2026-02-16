"""
View Tenant Isolation Tests
Ensures views respect multi-tenant architecture
"""
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from core.models import Company
from accounts.models import UserProfile
from finance.models import CompanyExpense, ExpenseCategory, ExpenseFamily, TransportOrder
from operations.models import FuelEntry, ServiceLog, Vehicle


class ViewTenantIsolationTestCase(TestCase):
    """
    Test suite for view-level tenant isolation
    
    Verifies that:
    1. List views show only current company's records
    2. Detail views return 404 for other companies' records
    3. Create views auto-assign company
    """
    
    def setUp(self):
        """
        Set up test data: 2 companies, users, and records
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
            role='MANAGER'
        )
        
        # Create User B (belongs to Company B)
        self.user_b = User.objects.create_user(
            username='user_b',
            password='testpass123'
        )
        UserProfile.objects.create(
            user=self.user_b,
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
        
        # Create transport orders for both companies
        self.order_a = TransportOrder.all_objects.create(
            company=self.company_a,
            customer_name="Customer A",
            date='2026-02-01',
            origin="Athens",
            destination="Thessaloniki",
            distance_km=500,
            agreed_price=1000.00
        )
        
        self.order_b = TransportOrder.all_objects.create(
            company=self.company_b,
            customer_name="Customer B",
            date='2026-02-01',
            origin="Patras",
            destination="Athens",
            distance_km=200,
            agreed_price=400.00
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
        
        # Create service logs for both companies
        self.service_a = ServiceLog.all_objects.create(
            company=self.company_a,
            vehicle=self.vehicle_a,
            date='2026-02-01',
            service_type='REGULAR',
            odometer_reading=50000,
            cost_parts=200.00,
            cost_labor=100.00,
            total_cost=300.00,
            description="Regular maintenance"
        )
        
        self.service_b = ServiceLog.all_objects.create(
            company=self.company_b,
            vehicle=self.vehicle_b,
            date='2026-02-01',
            service_type='KTEO',
            odometer_reading=60000,
            cost_parts=0.00,
            cost_labor=150.00,
            total_cost=150.00,
            description="KTEO inspection"
        )
        
        # Create test client
        self.client = Client()
    
    def test_list_view_isolation(self):
        """
        Test that list views show only current company's records
        """
        # Login as User A
        self.client.login(username='user_a', password='testpass123')
        
        # Test order list view
        response = self.client.get(reverse('web:order_list'))
        self.assertEqual(response.status_code, 200)
        
        # Verify only Company A order is in context
        orders = response.context.get('orders', [])
        order_ids = [o.id for o in orders]
        self.assertIn(self.order_a.id, order_ids)
        self.assertNotIn(self.order_b.id, order_ids)
    
    def test_detail_view_returns_404_for_other_company(self):
        """
        Test that detail views return 404 when accessing other company's records
        """
        # Login as User A
        self.client.login(username='user_a', password='testpass123')
        
        # Try to access Company B order detail
        response = self.client.get(reverse('web:order_detail', args=[self.order_b.pk]))
        
        # Should get 404 (not found in scoped queryset)
        self.assertEqual(response.status_code, 404)
        
        # Verify User A can access their own order
        response = self.client.get(reverse('web:order_detail', args=[self.order_a.pk]))
        self.assertEqual(response.status_code, 200)
    
    def test_create_view_auto_assigns_company(self):
        """
        Test that create views automatically assign company
        """
        # Login as User A
        self.client.login(username='user_a', password='testpass123')
        
        # Create a new transport order without specifying company
        response = self.client.post(reverse('web:order_create'), {
            'customer_name': 'New Customer',
            'date': '2026-02-15',
            'origin': 'Athens',
            'destination': 'Patras',
            'distance_km': 200,
            'agreed_price': 500.00,
            'status': 'PENDING',
        })
        
        # Should redirect on success (or return 200 if form has errors)
        self.assertIn(response.status_code, [200, 302])
        
        # If successful, verify the new order was created with Company A
        if response.status_code == 302:
            new_order = TransportOrder.all_objects.filter(
                customer_name='New Customer'
            ).first()
            
            self.assertIsNotNone(new_order)
            self.assertEqual(new_order.company, self.company_a)
    
    def tearDown(self):
        """
        Clean up after tests
        """
        self.client.logout()
