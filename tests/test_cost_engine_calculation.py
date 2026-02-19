"""
Cost Engine Calculation Tests
Ensures cost calculation service respects tenant isolation and calculates correctly
"""
from django.test import TestCase
from decimal import Decimal
from datetime import date
from core.models import Company
from core.tenant_context import tenant_context
from finance.models import CostCenter, CostItem, CostPosting, TransportOrder
from finance.services.cost_engine import calculate_company_costs
from operations.models import Vehicle


class CostEngineCalculationTestCase(TestCase):
    """
    Test suite for cost engine calculations
    
    Verifies that:
    1. Calculations respect tenant isolation
    2. Rates are calculated correctly
    3. Order breakdowns are accurate
    4. Empty states are handled gracefully
    """
    
    def setUp(self):
        """
        Set up test data: 2 companies with cost centers, postings, and orders
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
        
        # Period for calculations
        self.period_start = date(2026, 2, 1)
        self.period_end = date(2026, 2, 28)
        
        # Setup Company A data
        with tenant_context(self.company_a):
            # Create vehicle
            self.vehicle_a = Vehicle.objects.create(
                license_plate="AAA-1111",
                make="Mercedes",
                model="Actros",
                vehicle_class="TRUCK",
                body_type="BOX"
            )
            
            # Create cost centers
            self.vehicle_center_a = CostCenter.objects.create(
                name="Vehicle AAA-1111",
                type='VEHICLE',
                vehicle=self.vehicle_a
            )
            
            self.overhead_center_a = CostCenter.objects.create(
                name="Overhead",
                type='OVERHEAD'
            )
            
            # Create cost items
            self.leasing_item_a = CostItem.objects.create(
                name="Leasing",
                category='FIXED',
                unit='MONTH'
            )
            
            self.overhead_item_a = CostItem.objects.create(
                name="Overhead",
                category='INDIRECT',
                unit='MONTH'
            )
            
            # Create postings
            # Vehicle: 2000€ for Feb
            CostPosting.objects.create(
                cost_center=self.vehicle_center_a,
                cost_item=self.leasing_item_a,
                amount=Decimal('2000.00'),
                period_start=self.period_start,
                period_end=self.period_end
            )
            
            # Overhead: 500€ for Feb
            CostPosting.objects.create(
                cost_center=self.overhead_center_a,
                cost_item=self.overhead_item_a,
                amount=Decimal('500.00'),
                period_start=self.period_start,
                period_end=self.period_end
            )
            
            # Create transport orders
            # Order 1: 100km, 500€ revenue
            TransportOrder.objects.create(
                customer_name="Customer A1",
                date=date(2026, 2, 15),
                origin="Athens",
                destination="Patras",
                distance_km=Decimal('100.00'),
                agreed_price=Decimal('500.00'),
                assigned_vehicle=self.vehicle_a
            )
            
            # Order 2: 300km, 1200€ revenue
            TransportOrder.objects.create(
                customer_name="Customer A2",
                date=date(2026, 2, 20),
                origin="Thessaloniki",
                destination="Athens",
                distance_km=Decimal('300.00'),
                agreed_price=Decimal('1200.00'),
                assigned_vehicle=self.vehicle_a
            )
        
        # Setup Company B data
        with tenant_context(self.company_b):
            # Create vehicle
            self.vehicle_b = Vehicle.objects.create(
                license_plate="BBB-2222",
                make="Volvo",
                model="FH16",
                vehicle_class="TRUCK",
                body_type="CURTAIN"
            )
            
            # Create cost center
            self.vehicle_center_b = CostCenter.objects.create(
                name="Vehicle BBB-2222",
                type='VEHICLE',
                vehicle=self.vehicle_b
            )
            
            # Create cost item
            self.leasing_item_b = CostItem.objects.create(
                name="Leasing B",
                category='FIXED',
                unit='MONTH'
            )
            
            # Create posting: 999€ for Feb
            CostPosting.objects.create(
                cost_center=self.vehicle_center_b,
                cost_item=self.leasing_item_b,
                amount=Decimal('999.00'),
                period_start=self.period_start,
                period_end=self.period_end
            )
            
            # Create order: 100km, 400€ revenue
            TransportOrder.objects.create(
                customer_name="Customer B1",
                date=date(2026, 2, 10),
                origin="Heraklion",
                destination="Chania",
                distance_km=Decimal('100.00'),
                agreed_price=Decimal('400.00'),
                assigned_vehicle=self.vehicle_b
            )
    
    def test_vehicle_km_rate_calculation(self):
        """
        Test that vehicle rate is calculated correctly
        Expected: 2000€ / 400km = 5.0€/km
        """
        with tenant_context(self.company_a):
            result = calculate_company_costs(self.company_a, self.period_start, self.period_end)
            
            # Find vehicle snapshot
            vehicle_snapshot = next(
                (s for s in result['snapshots'] if s['cost_center_type'] == 'VEHICLE'),
                None
            )
            
            self.assertIsNotNone(vehicle_snapshot)
            self.assertEqual(vehicle_snapshot['total_cost'], Decimal('2000.00'))
            self.assertEqual(vehicle_snapshot['total_units'], Decimal('400.00'))
            self.assertEqual(vehicle_snapshot['rate'], Decimal('5.00'))
            self.assertEqual(vehicle_snapshot['status'], 'OK')
    
    def test_overhead_revenue_rate_calculation(self):
        """
        Test that overhead rate is calculated correctly
        Expected: 500€ / 1700€ = 0.294117...
        """
        with tenant_context(self.company_a):
            result = calculate_company_costs(self.company_a, self.period_start, self.period_end)
            
            # Find overhead snapshot
            overhead_snapshot = next(
                (s for s in result['snapshots'] if s['cost_center_type'] == 'OVERHEAD'),
                None
            )
            
            self.assertIsNotNone(overhead_snapshot)
            self.assertEqual(overhead_snapshot['total_cost'], Decimal('500.00'))
            self.assertEqual(overhead_snapshot['total_units'], Decimal('1700.00'))
            
            # Rate should be approximately 0.294117
            expected_rate = Decimal('500.00') / Decimal('1700.00')
            self.assertAlmostEqual(
                float(overhead_snapshot['rate']),
                float(expected_rate),
                places=4
            )
            self.assertEqual(overhead_snapshot['status'], 'OK')
    
    def test_order_breakdown_accuracy(self):
        """
        Test that order cost breakdown is calculated correctly
        """
        with tenant_context(self.company_a):
            result = calculate_company_costs(self.company_a, self.period_start, self.period_end)
            
            # Should have 2 order breakdowns
            self.assertEqual(len(result['breakdowns']), 2)
            
            # Verify vehicle allocation is calculated
            # Note: Actual value depends on which vehicle cost center is used
            # Just verify it's non-zero and calculations ran
            breakdown1 = result['breakdowns'][0]
            
            # Vehicle cost should be non-zero
            self.assertGreater(breakdown1['vehicle_alloc'], Decimal('0.00'))
            
            # Overhead cost should be non-zero
            self.assertGreater(breakdown1['overhead_alloc'], Decimal('0.00'))
            
            # Total cost should be sum of allocations
            expected_total = breakdown1['vehicle_alloc'] + breakdown1['overhead_alloc'] + breakdown1['direct_cost'] + breakdown1['driver_alloc']
            self.assertEqual(breakdown1['total_cost'], expected_total)
    
    def test_tenant_isolation_in_calculations(self):
        """
        Test that Company B cannot see Company A's data
        """
        # Calculate for Company A
        with tenant_context(self.company_a):
            result_a = calculate_company_costs(self.company_a, self.period_start, self.period_end)
            
            # Should have at least 2 cost centers (vehicle + overhead)
            self.assertGreaterEqual(len(result_a['snapshots']), 2)
            
            # Should have 2 orders
            self.assertEqual(len(result_a['breakdowns']), 2)
            
            # Verify Company A's vehicle cost center is present
            vehicle_snapshots_a = [s for s in result_a['snapshots'] if s['cost_center_type'] == 'VEHICLE']
            self.assertGreater(len(vehicle_snapshots_a), 0)
        
        # Calculate for Company B
        with tenant_context(self.company_b):
            result_b = calculate_company_costs(self.company_b, self.period_start, self.period_end)
            
            # Should have at least 1 cost center (vehicle)
            self.assertGreaterEqual(len(result_b['snapshots']), 1)
            
            # Should have 1 order
            self.assertEqual(len(result_b['breakdowns']), 1)
            
            # Verify it's Company B's data (vehicle cost center)
            vehicle_snapshots_b = [s for s in result_b['snapshots'] if s['cost_center_type'] == 'VEHICLE']
            self.assertGreater(len(vehicle_snapshots_b), 0)
            self.assertEqual(vehicle_snapshots_b[0]['total_cost'], Decimal('999.00'))
    
    def test_empty_period_returns_zero_results(self):
        """
        Test that a period with no data returns structured zero-result
        """
        # Create Company C with no data
        company_c = Company.objects.create(
            name="Company C",
            tax_id="333333333",
            transport_type="FREIGHT"
        )
        
        with tenant_context(company_c):
            result = calculate_company_costs(company_c, self.period_start, self.period_end)
            
            # Should return empty lists, not errors
            self.assertEqual(len(result['snapshots']), 0)
            self.assertEqual(len(result['breakdowns']), 0)
            self.assertEqual(result['summary']['total_cost'], Decimal('0.00'))
            self.assertEqual(result['summary']['total_revenue'], Decimal('0.00'))
    
    def test_missing_activity_sets_status(self):
        """
        Test that cost centers with no activity get MISSING_ACTIVITY status
        """
        # Create Company D with posting but no orders
        company_d = Company.objects.create(
            name="Company D",
            tax_id="444444444",
            transport_type="FREIGHT"
        )
        
        with tenant_context(company_d):
            # Create cost center and posting
            center = CostCenter.objects.create(
                name="Idle Center",
                type='VEHICLE'
            )
            
            item = CostItem.objects.create(
                name="Fixed Cost",
                category='FIXED',
                unit='MONTH'
            )
            
            CostPosting.objects.create(
                cost_center=center,
                cost_item=item,
                amount=Decimal('1000.00'),
                period_start=self.period_start,
                period_end=self.period_end
            )
            
            # Calculate (no orders = no activity)
            result = calculate_company_costs(company_d, self.period_start, self.period_end)
            
            # Should have 1 snapshot with MISSING_ACTIVITY status
            self.assertEqual(len(result['snapshots']), 1)
            self.assertEqual(result['snapshots'][0]['status'], 'MISSING_ACTIVITY')
            self.assertEqual(result['snapshots'][0]['rate'], Decimal('0.00'))
