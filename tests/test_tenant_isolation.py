"""
Tenant Isolation Security Tests
Ensures multi-tenant data segregation
"""
from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User
from core.models import Company
from core.mixins import set_current_company, get_current_company
from accounts.models import UserProfile
from finance.models import CompanyExpense, ExpenseCategory, ExpenseFamily


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
        
        # Create Expense Family and Category
        family = ExpenseFamily.objects.create(
            name="Test Family",
            display_order=1
        )
        self.category = ExpenseCategory.objects.create(
            family=family,
            name="Test Category",
            is_system_default=True
        )
        
        # Create expenses for Company A
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
        
        # Create expenses for Company B
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
        # Set Company A context
        set_current_company(self.company_a)
        
        # Query expenses
        expenses = CompanyExpense.objects.all()
        
        # Assertions
        self.assertEqual(expenses.count(), 2, "Company A should see exactly 2 expenses")
        self.assertIn(self.expense_a1, expenses, "Company A should see its own expense 1")
        self.assertIn(self.expense_a2, expenses, "Company A should see its own expense 2")
        self.assertNotIn(self.expense_b1, expenses, "Company A should NOT see Company B expense 1")
        self.assertNotIn(self.expense_b2, expenses, "Company A should NOT see Company B expense 2")
        
        # Cleanup
        set_current_company(None)
    
    def test_company_b_isolation(self):
        """
        Test that Company B user only sees Company B expenses
        """
        # Set Company B context
        set_current_company(self.company_b)
        
        # Query expenses
        expenses = CompanyExpense.objects.all()
        
        # Assertions
        self.assertEqual(expenses.count(), 2, "Company B should see exactly 2 expenses")
        self.assertIn(self.expense_b1, expenses, "Company B should see its own expense 1")
        self.assertIn(self.expense_b2, expenses, "Company B should see its own expense 2")
        self.assertNotIn(self.expense_a1, expenses, "Company B should NOT see Company A expense 1")
        self.assertNotIn(self.expense_a2, expenses, "Company B should NOT see Company A expense 2")
        
        # Cleanup
        set_current_company(None)
    
    def test_no_context_returns_empty(self):
        """
        Test that no company context returns empty queryset (safe default)
        """
        # Clear company context
        set_current_company(None)
        
        # Query expenses
        expenses = CompanyExpense.objects.all()
        
        # Assertion: Should return empty queryset
        self.assertEqual(expenses.count(), 0, "No company context should return empty queryset")
        
        # Cleanup
        set_current_company(None)
    
    def test_all_objects_manager_bypass(self):
        """
        Test that all_objects manager bypasses tenant filtering
        """
        # Set Company A context
        set_current_company(self.company_a)
        
        # Query with all_objects (should bypass filtering)
        all_expenses = CompanyExpense.all_objects.all()
        
        # Assertions: Should see all 4 expenses
        self.assertEqual(all_expenses.count(), 4, "all_objects should return all expenses")
        
        # Cleanup
        set_current_company(None)
    
    def test_direct_access_prevention(self):
        """
        Test that direct ID access is prevented across tenants
        """
        # Set Company A context
        set_current_company(self.company_a)
        
        # Try to access Company B expense by ID
        try:
            expense = CompanyExpense.objects.get(id=self.expense_b1.id)
            self.fail("Should not be able to access Company B expense from Company A context")
        except CompanyExpense.DoesNotExist:
            # Expected behavior - cross-tenant access blocked
            pass
        
        # Cleanup
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
        
        # Create mock request
        factory = RequestFactory()
        request = factory.get('/dashboard/')
        request.user = self.user_a  # User A belongs to Company A
        
        # Instantiate middleware
        middleware = CurrentCompanyMiddleware(get_response=lambda r: HttpResponse())
        
        # Simulate process_request
        middleware.process_request(request)
        
        # Assert: Company context is set to Company A
        current_company = get_current_company()
        self.assertEqual(current_company, self.company_a, "Middleware should set Company A context")
        
        # Assert: CompanyExpense.objects.all() returns only Company A expenses
        expenses = CompanyExpense.objects.all()
        self.assertEqual(expenses.count(), 2, "Should see only Company A expenses")
        self.assertIn(self.expense_a1, expenses)
        self.assertIn(self.expense_a2, expenses)
        self.assertNotIn(self.expense_b1, expenses)
        self.assertNotIn(self.expense_b2, expenses)
        
        # Simulate process_response (cleanup)
        response = HttpResponse()
        middleware.process_response(request, response)
        
        # Assert: Company context is cleared
        current_company_after = get_current_company()
        self.assertIsNone(current_company_after, "Middleware should clear company context after response")
        
        # Assert: After cleanup, no context returns empty queryset
        expenses_after = CompanyExpense.objects.all()
        self.assertEqual(expenses_after.count(), 0, "No context should return empty queryset")
    
    def tearDown(self):
        """
        Clean up thread-local state after each test
        """
        set_current_company(None)
