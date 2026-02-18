"""
Cost Engine Tests
Ensures cost models respect tenant isolation
"""
from django.test import TestCase
from core.models import Company
from core.mixins import set_current_company
from finance.models import CostCenter, CostItem, CostPosting
from operations.models import Vehicle


class CostEngineTenantIsolationTestCase(TestCase):
    """
    Test suite for cost engine tenant isolation
    
    Verifies that:
    1. CostCenter respects tenant isolation
    2. CostItem respects tenant isolation
    3. CostPosting correctly links to company context
    """
    
    def setUp(self):
        """
        Set up test data: 2 companies with cost centers, items, and postings
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
        
        # Create vehicles for entity linking
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
        
        # Create cost centers for both companies
        self.center_a = CostCenter.all_objects.create(
            company=self.company_a,
            name="Vehicle AAA-1111",
            type='VEHICLE',
            vehicle=self.vehicle_a
        )
        
        self.center_b = CostCenter.all_objects.create(
            company=self.company_b,
            name="Vehicle BBB-2222",
            type='VEHICLE',
            vehicle=self.vehicle_b
        )
        
        # Create cost items for both companies
        self.item_a = CostItem.all_objects.create(
            company=self.company_a,
            name="Fuel",
            category='VARIABLE',
            unit='KM'
        )
        
        self.item_b = CostItem.all_objects.create(
            company=self.company_b,
            name="Insurance",
            category='FIXED',
            unit='MONTH'
        )
        
        # Create cost postings for both companies
        self.posting_a = CostPosting.all_objects.create(
            company=self.company_a,
            cost_center=self.center_a,
            cost_item=self.item_a,
            amount=500.00,
            period_start='2026-02-01',
            period_end='2026-02-28'
        )
        
        self.posting_b = CostPosting.all_objects.create(
            company=self.company_b,
            cost_center=self.center_b,
            cost_item=self.item_b,
            amount=1000.00,
            period_start='2026-02-01',
            period_end='2026-02-28'
        )
    
    def test_costcenter_isolation(self):
        """
        Test that CostCenter respects tenant isolation
        """
        # Set Company A context
        set_current_company(self.company_a)
        
        # Query cost centers
        centers = CostCenter.objects.all()
        
        # Debug: Print what we got
        center_ids = [c.id for c in centers]
        
        # Assertions - check that center_a is in results and center_b is not
        self.assertIn(self.center_a.id, center_ids, "Company A center should be visible")
        self.assertNotIn(self.center_b.id, center_ids, "Company B center should NOT be visible")
        
        # Verify Company A center is accessible
        self.assertIn(self.center_a, centers)
        self.assertNotIn(self.center_b, centers)
        
        # Test all_objects bypass - should see at least our 2 test centers
        all_centers = CostCenter.all_objects.all()
        all_center_ids = [c.id for c in all_centers]
        self.assertIn(self.center_a.id, all_center_ids)
        self.assertIn(self.center_b.id, all_center_ids)
        
        # Cleanup
        set_current_company(None)
    
    def test_costitem_isolation(self):
        """
        Test that CostItem respects tenant isolation
        """
        # Set Company A context
        set_current_company(self.company_a)
        
        # Query cost items
        items = CostItem.objects.all()
        
        # Assertions
        self.assertEqual(items.count(), 1)
        self.assertIn(self.item_a, items)
        self.assertNotIn(self.item_b, items)
        
        # Test all_objects bypass
        all_items = CostItem.all_objects.all()
        self.assertEqual(all_items.count(), 2)
        
        # Cleanup
        set_current_company(None)
    
    def test_costposting_isolation(self):
        """
        Test that CostPosting respects tenant isolation
        """
        # Set Company A context
        set_current_company(self.company_a)
        
        # Query cost postings
        postings = CostPosting.objects.all()
        
        # Assertions
        self.assertEqual(postings.count(), 1)
        self.assertIn(self.posting_a, postings)
        self.assertNotIn(self.posting_b, postings)
        
        # Test all_objects bypass
        all_postings = CostPosting.all_objects.all()
        self.assertEqual(all_postings.count(), 2)
        
        # Cleanup
        set_current_company(None)
    
    def test_costposting_links_to_company_context(self):
        """
        Test that CostPosting correctly links to company context
        """
        # Set Company A context
        set_current_company(self.company_a)
        
        # Query posting and verify relationships
        posting = CostPosting.objects.first()
        
        self.assertIsNotNone(posting)
        self.assertEqual(posting.company, self.company_a)
        self.assertEqual(posting.cost_center.company, self.company_a)
        self.assertEqual(posting.cost_item.company, self.company_a)
        
        # Cleanup
        set_current_company(None)
    
    def test_no_context_returns_empty(self):
        """
        Test that no company context returns empty queryset for all models
        """
        # Clear context
        set_current_company(None)
        
        # Query all cost engine models
        centers = CostCenter.objects.all()
        items = CostItem.objects.all()
        postings = CostPosting.objects.all()
        
        # All should return empty
        self.assertEqual(centers.count(), 0)
        self.assertEqual(items.count(), 0)
        self.assertEqual(postings.count(), 0)
        
        # Cleanup
        set_current_company(None)
    
    def tearDown(self):
        """
        Clean up thread-local state after each test
        """
        set_current_company(None)
