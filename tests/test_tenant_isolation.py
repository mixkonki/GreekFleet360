"""
Tenant Isolation Security Tests
Ensures multi-tenant data segregation
"""
from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User
from core.models import Company
from core.mixins import set_current_company, get_current_company
from accounts.models import UserProfile
from finance.models import CompanyExpense, ExpenseCategory, ExpenseFamily, TransportOrder
from operations.models import FuelEntry, ServiceLog, Vehicle


class TenantIsolationTestCase(TestCase):
    """
    Test suite for tenant isolation enforcement
    
    Verifies that:
    1. Users can only access their own company's data
    2. Cross-tenant data leakage is prevented
    3. Thread-local context is properly managed
    """
    
    def setUp(self):
        """
        Set up test data: 2 companies, 2 users, expenses for each
        """
        self.company_a = Company.objects.create(
            name="Company A",
            tax_id="111111111",
            transport_type="FREIGHT"
        )
        
        self.company_b = Company.objects.create(
            name="Company B",
            tax_id="222222222",
            transport_type="FREIGHT"
        )
        
        self.user_a = User.objects.create_user(
            username='user_a',
            password='testpass123'
        )
        UserProfile.objects.create(
            user=self.user_a,
            company=self.company_a,
            role='MANAGER'
        )
        
        self.user_b = User.objects.create_user(
            username='user_b',
            password='testpass123'
        )
        UserProfile.objects.create(
            user=self.user_b,
            company=self.company_b,
            role='MANAGER'
        )
        
        family = ExpenseFamily.objects.create(
            name="Test Family",
            display_order=1
        )
        self.category = ExpenseCategory.objects.create(
            family=family,
            name="Test Category",
            is_system_default=True
        )
        
        self.expense_a1 = CompanyExpense.objects.create(
            company=self.company_a,
            category=self.category,
            expense_type='MONTHLY',
            periodicity='MONTHLY',
            amount=1000.00,
            start_date='2026-01-01',
            description='Company A Expense 1'
        )
        
        self.expense_a2 = CompanyExpense.objects.create(
            company=self.company_a,
            category=self.category,
            expense_type='MONTHLY',
            periodicity='MONTHLY',
            amount=2000.00,
            start_date='2026-01-01',
            description='Company A Expense 2'
        )
        
        self.expense_b1 = CompanyExpense.objects.create(
            company=self.company_b,
            category=self.category,
            expense_type='MONTHLY',
            periodicity='MONTHLY',
            amount=3000.00,
            start_date='2026-01-01',
            description='Company B Expense 1'
        )
        
        self.expense_b2 = CompanyExpense.objects.create(
            company=self.company_b,
            category=self.category,
            expense_type='MONTHLY',
            periodicity='MONTHLY',
            amount=4000.00,
            start_date='2026-01-01',
            description='Company B Expense 2'
        )
    
    def test_company_a_isolation(self):
        """
        Test that Company A user only sees Company A expenses
        """
        set_current_company(self.company_a)
        
        expenses = CompanyExpense.objects.all()
        
        self.assertEqual(expenses.count(), 2, "Company A should see exactly 2 expenses")
        self.assertIn(self.expense_a1, expenses, "Company A should see its own expense 1")
        self.assertIn(self.expense_a2, expenses, "Company A should see its own expense 2")
        self.assertNotIn(self.expense_b1, expenses, "Company A should NOT see Company B expense 1")
        self.assertNotIn(self.expense_b2, expenses, "Company A should NOT see Company B expense 2")
        
        set_current_company(None)
    
    def test_company_b_isolation(self):
        """
        Test that Company B user only sees Company B expenses
        """
        set_current_company(self.company_b)
        
        expenses = CompanyExpense.objects.all()
        
        self.assertEqual(expenses.count(), 2, "Company B should see exactly 2 expenses")
        self.assertIn(self.expense_b1, expenses, "Company B should see its own expense 1")
        self.assertIn(self.expense_b2, expenses, "Company B should see its own expense 2")
        self.assertNotIn(self.expense_a1, expenses, "Company B should NOT see Company A expense 1")
        self.assertNotIn(self.expense_a2, expenses, "Company B should NOT see Company A expense 2")
        
        set_current_company(None)
    
    def test_no_context_returns_empty(self):
        """
        Test that no company context returns empty queryset (safe default)
        """
        set_current_company(None)
        
        expenses = CompanyExpense.objects.all()
        
        self.assertEqual(expenses.count(), 0, "No company context should return empty queryset")
        
        set_current_company(None)
    
    def test_all_objects_manager_bypass(self):
        """
        Test that all_objects manager bypasses tenant filtering
        """
        set_current_company(self.company_a)
        
        all_expenses = CompanyExpense.all_objects.all()
        
        self.assertEqual(all_expenses.count(), 4, "all_objects should return all expenses")
        
        set_current_company(None)
    
    def test_direct_access_prevention(self):
        """
        Test that direct ID access is prevented across tenants
        """
        set_current_company(self.company_a)
        
        try:
            expense = CompanyExpense.objects.get(id=self.expense_b1.id)
            self.fail("Should not be able to access Company B expense from Company A context")
        except CompanyExpense.DoesNotExist:
            pass
        
        set_current_company(None)
    
    def test_middleware_integration(self):
        """
        Test full middleware-to-model lifecycle
        
        Simulates:
        1. Request with authenticated user
        2. Middleware sets company context
        3. Model manager filters by company
        4. Middleware cleans up context after response
        """
        from core.middleware import CurrentCompanyMiddleware
        from django.http import HttpResponse
        
        factory = RequestFactory()
        request = factory.get('/dashboard/')
        request.user = self.user_a
        
        middleware = CurrentCompanyMiddleware(get_response=lambda r: HttpResponse())
        
        middleware.process_request(request)
        
        current_company = get_current_company()
        self.assertEqual(current_company, self.company_a, "Middleware should set Company A context")
        
        expenses = CompanyExpense.objects.all()
        self.assertEqual(expenses.count(), 2, "Should see only Company A expenses")
        self.assertIn(self.expense_a1, expenses)
        self.assertIn(self.expense_a2, expenses)
        self.assertNotIn(self.expense_b1, expenses)
        self.assertNotIn(self.expense_b2, expenses)
        
        response = HttpResponse()
        middleware.process_response(request, response)
        
        current_company_after = get_current_company()
        self.assertIsNone(current_company_after, "Middleware should clear company context after response")
        
        expenses_after = CompanyExpense.objects.all()
        self.assertEqual(expenses_after.count(), 0, "No context should return empty queryset")
    
    def test_transportorder_isolation(self):
        """
        Test that TransportOrder respects tenant isolation
        """
        # Create TransportOrders for both companies
        order_a1 = TransportOrder.objects.create(
            company=self.company_a,
            customer_name="Customer A1",
            date='2026-02-01',
            origin="Athens",
            destination="Thessaloniki",
            distance_km=500,
            agreed_price=1000.00
        )
        
        order_a2 = TransportOrder.objects.create(
            company=self.company_a,
            customer_name="Customer A2",
            date='2026-02-02',
            origin="Patras",
            destination="Athens",
            distance_km=200,
            agreed_price=400.00
        )
        
        order_b1 = TransportOrder.objects.create(
            company=self.company_b,
            customer_name="Customer B1",
            date='2026-02-01',
            origin="Heraklion",
            destination="Chania",
            distance_km=150,
            agreed_price=300.00
        )
        
        # Test Company A isolation
        set_current_company(self.company_a)
        orders = TransportOrder.objects.all()
        self.assertEqual(orders.count(), 2, "Company A should see 2 orders")
        self.assertIn(order_a1, orders)
        self.assertIn(order_a2, orders)
        self.assertNotIn(order_b1, orders)
        
        # Test all_objects bypass
        all_orders = TransportOrder.all_objects.all()
        self.assertEqual(all_orders.count(), 3, "all_objects should return all 3 orders")
        
        set_current_company(None)
    
    def test_fuelentry_isolation(self):
        """
        Test that FuelEntry respects tenant isolation
        """
        # Create vehicles for both companies
        vehicle_a = Vehicle.objects.create(
            company=self.company_a,
            license_plate="AAA-1111",
            make="Mercedes",
            model="Actros",
            vehicle_class="TRUCK",
            body_type="BOX"
        )
        
        vehicle_b = Vehicle.objects.create(
            company=self.company_b,
            license_plate="BBB-2222",
            make="Volvo",
            model="FH16",
            vehicle_class="TRUCK",
            body_type="CURTAIN"
        )
        
        # Create FuelEntries for both companies
        fuel_a1 = FuelEntry.objects.create(
            company=self.company_a,
            vehicle=vehicle_a,
            date='2026-02-01',
            liters=100.00,
            cost_per_liter=1.50,
            total_cost=150.00,
            odometer_reading=10000
        )
        
        fuel_a2 = FuelEntry.objects.create(
            company=self.company_a,
            vehicle=vehicle_a,
            date='2026-02-02',
            liters=120.00,
            cost_per_liter=1.55,
            total_cost=186.00,
            odometer_reading=10500
        )
        
        fuel_b1 = FuelEntry.objects.create(
            company=self.company_b,
            vehicle=vehicle_b,
            date='2026-02-01',
            liters=150.00,
            cost_per_liter=1.52,
            total_cost=228.00,
            odometer_reading=20000
        )
        
        # Test Company A isolation
        set_current_company(self.company_a)
        fuel_entries = FuelEntry.objects.all()
        self.assertEqual(fuel_entries.count(), 2, "Company A should see 2 fuel entries")
        self.assertIn(fuel_a1, fuel_entries)
        self.assertIn(fuel_a2, fuel_entries)
        self.assertNotIn(fuel_b1, fuel_entries)
        
        # Test all_objects bypass
        all_fuel = FuelEntry.all_objects.all()
        self.assertEqual(all_fuel.count(), 3, "all_objects should return all 3 fuel entries")
        
        set_current_company(None)
    
    def test_servicelog_isolation(self):
        """
        Test that ServiceLog respects tenant isolation
        """
        # Create vehicles for both companies
        vehicle_a = Vehicle.objects.create(
            company=self.company_a,
            license_plate="CCC-3333",
            make="Scania",
            model="R450",
            vehicle_class="TRUCK",
            body_type="REFRIGERATOR"
        )
        
        vehicle_b = Vehicle.objects.create(
            company=self.company_b,
            license_plate="DDD-4444",
            make="MAN",
            model="TGX",
            vehicle_class="TRUCK",
            body_type="TANKER"
        )
        
        # Create ServiceLogs for both companies
        service_a1 = ServiceLog.objects.create(
            company=self.company_a,
            vehicle=vehicle_a,
            date='2026-02-01',
            service_type='REGULAR',
            odometer_reading=50000,
            cost_parts=200.00,
            cost_labor=100.00,
            total_cost=300.00,
            description="Regular maintenance"
        )
        
        service_a2 = ServiceLog.objects.create(
            company=self.company_a,
            vehicle=vehicle_a,
            date='2026-02-05',
            service_type='REPAIR',
            odometer_reading=51000,
            cost_parts=500.00,
            cost_labor=200.00,
            total_cost=700.00,
            description="Brake repair"
        )
        
        service_b1 = ServiceLog.objects.create(
            company=self.company_b,
            vehicle=vehicle_b,
            date='2026-02-01',
            service_type='KTEO',
            odometer_reading=60000,
            cost_parts=0.00,
            cost_labor=150.00,
            total_cost=150.00,
            description="KTEO inspection"
        )
        
        # Test Company A isolation
        set_current_company(self.company_a)
        service_logs = ServiceLog.objects.all()
        self.assertEqual(service_logs.count(), 2, "Company A should see 2 service logs")
        self.assertIn(service_a1, service_logs)
        self.assertIn(service_a2, service_logs)
        self.assertNotIn(service_b1, service_logs)
        
        # Test all_objects bypass
        all_services = ServiceLog.all_objects.all()
        self.assertEqual(all_services.count(), 3, "all_objects should return all 3 service logs")
        
        set_current_company(None)
    
    def tearDown(self):
        """
        Clean up thread-local state after each test
        """
        set_current_company(None)
