"""
Company Auto-Assignment Tests
Ensures CompanyScopedQuerySet auto-assigns company on create operations
"""
from django.test import TestCase
from django.db import IntegrityError
from core.models import Company
from core.mixins import set_current_company, get_current_company
from core.tenant_context import tenant_context
from finance.models import CostItem, ExpenseFamily, ExpenseCategory


class CompanyAutoAssignmentTestCase(TestCase):
    """
    Test suite for automatic company assignment
    
    Verifies that:
    1. create() auto-assigns company when tenant_context is active
    2. bulk_create() auto-assigns company
    3. get_or_create() auto-assigns company
    4. update_or_create() auto-assigns company
    5. Outside context, explicit company is still required
    """
    
    def setUp(self):
        """
        Set up test data: companies
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
    
    def test_create_auto_assigns_company(self):
        """
        Test that create() auto-assigns company inside tenant_context
        """
        # Verify no company context initially
        self.assertIsNone(get_current_company())
        
        # Use tenant_context
        with tenant_context(self.company_a):
            # Create without specifying company
            item = CostItem.objects.create(
                name="Test Item",
                category='FIXED',
                unit='MONTH'
            )
            
            # Verify company was auto-assigned
            self.assertEqual(item.company, self.company_a)
        
        # Verify context is cleared
        self.assertIsNone(get_current_company())
    
    def test_bulk_create_auto_assigns_company(self):
        """
        Test that bulk_create() auto-assigns company
        """
        with tenant_context(self.company_a):
            # Create multiple objects without specifying company
            items = [
                CostItem(name="Item 1", category='FIXED', unit='MONTH'),
                CostItem(name="Item 2", category='VARIABLE', unit='KM'),
                CostItem(name="Item 3", category='INDIRECT', unit='HOUR'),
            ]
            
            created_items = CostItem.objects.bulk_create(items)
            
            # Verify all items have company assigned
            for item in created_items:
                item.refresh_from_db()
                self.assertEqual(item.company, self.company_a)
    
    def test_get_or_create_auto_assigns_company(self):
        """
        Test that get_or_create() auto-assigns company
        """
        with tenant_context(self.company_a):
            # First call - should create
            item1, created1 = CostItem.objects.get_or_create(
                name="Unique Item",
                defaults={'category': 'FIXED', 'unit': 'MONTH'}
            )
            
            self.assertTrue(created1)
            self.assertEqual(item1.company, self.company_a)
            
            # Second call - should get existing
            item2, created2 = CostItem.objects.get_or_create(
                name="Unique Item",
                defaults={'category': 'FIXED', 'unit': 'MONTH'}
            )
            
            self.assertFalse(created2)
            self.assertEqual(item1.id, item2.id)
            self.assertEqual(item2.company, self.company_a)
    
    def test_update_or_create_auto_assigns_company(self):
        """
        Test that update_or_create() auto-assigns company
        """
        with tenant_context(self.company_a):
            # First call - should create
            item1, created1 = CostItem.objects.update_or_create(
                name="Update Test Item",
                defaults={'category': 'FIXED', 'unit': 'MONTH'}
            )
            
            self.assertTrue(created1)
            self.assertEqual(item1.company, self.company_a)
            self.assertEqual(item1.category, 'FIXED')
            
            # Second call - should update
            item2, created2 = CostItem.objects.update_or_create(
                name="Update Test Item",
                defaults={'category': 'VARIABLE', 'unit': 'KM'}
            )
            
            self.assertFalse(created2)
            self.assertEqual(item1.id, item2.id)
            self.assertEqual(item2.category, 'VARIABLE')
            self.assertEqual(item2.unit, 'KM')
    
    def test_explicit_company_overrides_context(self):
        """
        Test that explicitly providing company overrides auto-assignment
        """
        with tenant_context(self.company_a):
            # Explicitly specify Company B
            item = CostItem.objects.create(
                company=self.company_b,
                name="Explicit Company Item",
                category='FIXED',
                unit='MONTH'
            )
            
            # Verify Company B was used (not auto-assigned Company A)
            self.assertEqual(item.company, self.company_b)
    
    def test_outside_context_requires_explicit_company(self):
        """
        Test that outside tenant_context, company must be explicit
        """
        # Clear any context
        set_current_company(None)
        
        # Try to create without company - should fail
        with self.assertRaises(IntegrityError):
            CostItem.objects.create(
                name="No Company Item",
                category='FIXED',
                unit='MONTH'
            )
    
    def test_different_contexts_assign_different_companies(self):
        """
        Test that different contexts assign different companies
        """
        # Create with Company A context
        with tenant_context(self.company_a):
            item_a = CostItem.objects.create(
                name="Company A Item",
                category='FIXED',
                unit='MONTH'
            )
            self.assertEqual(item_a.company, self.company_a)
        
        # Create with Company B context
        with tenant_context(self.company_b):
            item_b = CostItem.objects.create(
                name="Company B Item",
                category='VARIABLE',
                unit='KM'
            )
            self.assertEqual(item_b.company, self.company_b)
        
        # Verify both items exist with correct companies
        item_a.refresh_from_db()
        item_b.refresh_from_db()
        self.assertEqual(item_a.company, self.company_a)
        self.assertEqual(item_b.company, self.company_b)
    
    def tearDown(self):
        """
        Clean up thread-local state after each test
        """
        set_current_company(None)
