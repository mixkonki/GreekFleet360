"""
Tests for Cost Engine Persistence Layer
"""
from decimal import Decimal
from datetime import date
from django.test import TestCase
from core.models import Company
from core.tenant_context import tenant_context
from finance.models import (
    CostCenter, TransportOrder, CostRateSnapshot, OrderCostBreakdown
)
from finance.services.cost_engine.persist import CostEnginePersistence


class TestCostEnginePersistence(TestCase):
    """Test suite for Cost Engine Persistence"""
    
    def setUp(self):
        """Set up test data"""
        self.company = Company.objects.create(
            name="Test Transport Co",
            tax_id="123456789",
            address="Test Address"
        )
        
        # Create test data inside tenant context
        with tenant_context(self.company):
            self.cost_center = CostCenter.objects.create(
                company=self.company,
                name="Test Vehicle CC",
                type='VEHICLE',
                is_active=True
            )
            
            self.transport_order = TransportOrder.objects.create(
                company=self.company,
                customer_name="Test Customer",
                date=date(2026, 1, 15),
                origin="Athens",
                destination="Thessaloniki",
                distance_km=Decimal('500.00'),
                agreed_price=Decimal('800.00')
            )
        
        self.period_start = date(2026, 1, 1)
        self.period_end = date(2026, 1, 31)
        
        self.persistence = CostEnginePersistence()
    
    def test_save_cost_rate_snapshots(self):
        """Test saving cost rate snapshots"""
        cost_center_rates = {
            self.cost_center.id: {
                'total_cost': Decimal('1000.00'),
                'total_km': Decimal('5000.00'),
                'total_hours': Decimal('100.00'),
                'total_trips': Decimal('20.00'),
                'total_revenue': Decimal('8000.00'),
                'rate_per_km': Decimal('0.20'),
                'rate_per_hour': Decimal('10.00'),
                'rate_per_trip': Decimal('50.00'),
                'rate_per_revenue': Decimal('0.125'),
            }
        }
        
        with tenant_context(self.company):
            snapshots = self.persistence.save_cost_rate_snapshots(
                self.company,
                self.period_start,
                self.period_end,
                cost_center_rates
            )
            
            # Should create 4 snapshots (one for each basis unit)
            self.assertEqual(len(snapshots), 4)
            
            # Verify KM snapshot
            km_snapshot = CostRateSnapshot.objects.get(
                company=self.company,
                cost_center=self.cost_center,
                basis_unit='KM',
                period_start=self.period_start,
                period_end=self.period_end
            )
            self.assertEqual(km_snapshot.total_cost, Decimal('1000.00'))
            self.assertEqual(km_snapshot.total_units, Decimal('5000.00'))
            self.assertEqual(km_snapshot.rate, Decimal('0.20'))
            self.assertEqual(km_snapshot.status, 'OK')
    
    def test_save_cost_rate_snapshots_missing_activity(self):
        """Test saving snapshots with missing activity"""
        cost_center_rates = {
            self.cost_center.id: {
                'total_cost': Decimal('1000.00'),
                'total_km': Decimal('0.00'),  # No activity
                'total_hours': Decimal('0.00'),
                'total_trips': Decimal('0.00'),
                'total_revenue': Decimal('0.00'),
                'rate_per_km': Decimal('0.00'),
                'rate_per_hour': Decimal('0.00'),
                'rate_per_trip': Decimal('0.00'),
                'rate_per_revenue': Decimal('0.00'),
            }
        }
        
        with tenant_context(self.company):
            snapshots = self.persistence.save_cost_rate_snapshots(
                self.company,
                self.period_start,
                self.period_end,
                cost_center_rates
            )
            
            # Verify status is MISSING_ACTIVITY for KM, HOUR, TRIP
            km_snapshot = CostRateSnapshot.objects.get(
                company=self.company,
                cost_center=self.cost_center,
                basis_unit='KM'
            )
            self.assertEqual(km_snapshot.status, 'MISSING_ACTIVITY')
    
    def test_save_order_cost_breakdowns(self):
        """Test saving order cost breakdowns"""
        order_breakdowns = {
            self.transport_order.id: {
                'vehicle_alloc': Decimal('300.00'),
                'overhead_alloc': Decimal('100.00'),
                'direct_cost': Decimal('50.00'),
                'total_cost': Decimal('450.00'),
                'revenue': Decimal('800.00'),
                'profit': Decimal('350.00'),
                'margin': Decimal('43.75'),
                'status': 'OK'
            }
        }
        
        with tenant_context(self.company):
            breakdowns = self.persistence.save_order_cost_breakdowns(
                self.company,
                self.period_start,
                self.period_end,
                order_breakdowns
            )
            
            self.assertEqual(len(breakdowns), 1)
            
            # Verify breakdown
            breakdown = OrderCostBreakdown.objects.get(
                company=self.company,
                transport_order=self.transport_order,
                period_start=self.period_start,
                period_end=self.period_end
            )
            self.assertEqual(breakdown.vehicle_alloc, Decimal('300.00'))
            self.assertEqual(breakdown.overhead_alloc, Decimal('100.00'))
            self.assertEqual(breakdown.direct_cost, Decimal('50.00'))
            self.assertEqual(breakdown.total_cost, Decimal('450.00'))
            self.assertEqual(breakdown.revenue, Decimal('800.00'))
            self.assertEqual(breakdown.profit, Decimal('350.00'))
            self.assertEqual(breakdown.margin, Decimal('43.75'))
            self.assertEqual(breakdown.status, 'OK')
    
    def test_get_cost_rate_snapshot(self):
        """Test retrieving a specific cost rate snapshot"""
        with tenant_context(self.company):
            # Create a snapshot first
            snapshot = CostRateSnapshot.objects.create(
                company=self.company,
                period_start=self.period_start,
                period_end=self.period_end,
                cost_center=self.cost_center,
                basis_unit='KM',
                total_cost=Decimal('1000.00'),
                total_units=Decimal('5000.00'),
                rate=Decimal('0.20'),
                status='OK'
            )
            
            # Retrieve it
            retrieved = self.persistence.get_cost_rate_snapshot(
                self.company,
                self.period_start,
                self.period_end,
                self.cost_center,
                'KM'
            )
            
            self.assertIsNotNone(retrieved)
            self.assertEqual(retrieved.id, snapshot.id)
            self.assertEqual(retrieved.rate, Decimal('0.20'))
    
    def test_get_order_cost_breakdown(self):
        """Test retrieving a specific order cost breakdown"""
        with tenant_context(self.company):
            # Create a breakdown first
            breakdown = OrderCostBreakdown.objects.create(
                company=self.company,
                transport_order=self.transport_order,
                period_start=self.period_start,
                period_end=self.period_end,
                vehicle_alloc=Decimal('300.00'),
                overhead_alloc=Decimal('100.00'),
                direct_cost=Decimal('50.00'),
                total_cost=Decimal('450.00'),
                revenue=Decimal('800.00'),
                profit=Decimal('350.00'),
                margin=Decimal('43.75'),
                status='OK'
            )
            
            # Retrieve it
            retrieved = self.persistence.get_order_cost_breakdown(
                self.company,
                self.period_start,
                self.period_end,
                self.transport_order
            )
            
            self.assertIsNotNone(retrieved)
            self.assertEqual(retrieved.id, breakdown.id)
            self.assertEqual(retrieved.profit, Decimal('350.00'))
    
    def test_get_all_cost_rate_snapshots(self):
        """Test retrieving all cost rate snapshots for a period"""
        with tenant_context(self.company):
            # Create multiple snapshots
            CostRateSnapshot.objects.create(
                company=self.company,
                period_start=self.period_start,
                period_end=self.period_end,
                cost_center=self.cost_center,
                basis_unit='KM',
                total_cost=Decimal('1000.00'),
                total_units=Decimal('5000.00'),
                rate=Decimal('0.20'),
                status='OK'
            )
            
            CostRateSnapshot.objects.create(
                company=self.company,
                period_start=self.period_start,
                period_end=self.period_end,
                cost_center=self.cost_center,
                basis_unit='HOUR',
                total_cost=Decimal('1000.00'),
                total_units=Decimal('100.00'),
                rate=Decimal('10.00'),
                status='OK'
            )
            
            # Retrieve all
            snapshots = self.persistence.get_all_cost_rate_snapshots(
                self.company,
                self.period_start,
                self.period_end
            )
            
            self.assertEqual(len(snapshots), 2)
    
    def test_get_all_order_cost_breakdowns(self):
        """Test retrieving all order cost breakdowns for a period"""
        with tenant_context(self.company):
            # Create multiple breakdowns
            OrderCostBreakdown.objects.create(
                company=self.company,
                transport_order=self.transport_order,
                period_start=self.period_start,
                period_end=self.period_end,
                vehicle_alloc=Decimal('300.00'),
                overhead_alloc=Decimal('100.00'),
                direct_cost=Decimal('50.00'),
                total_cost=Decimal('450.00'),
                revenue=Decimal('800.00'),
                profit=Decimal('350.00'),
                margin=Decimal('43.75'),
                status='OK'
            )
            
            # Retrieve all
            breakdowns = self.persistence.get_all_order_cost_breakdowns(
                self.company,
                self.period_start,
                self.period_end
            )
            
            self.assertEqual(len(breakdowns), 1)
    
    def test_save_snapshots_replaces_existing(self):
        """Test that saving snapshots replaces existing ones"""
        # Create initial snapshot
        initial_rates = {
            self.cost_center.id: {
                'total_cost': Decimal('1000.00'),
                'total_km': Decimal('5000.00'),
                'total_hours': Decimal('100.00'),
                'total_trips': Decimal('20.00'),
                'total_revenue': Decimal('8000.00'),
                'rate_per_km': Decimal('0.20'),
                'rate_per_hour': Decimal('10.00'),
                'rate_per_trip': Decimal('50.00'),
                'rate_per_revenue': Decimal('0.125'),
            }
        }
        
        with tenant_context(self.company):
            self.persistence.save_cost_rate_snapshots(
                self.company,
                self.period_start,
                self.period_end,
                initial_rates
            )
            
            # Update with new rates
            updated_rates = {
                self.cost_center.id: {
                    'total_cost': Decimal('1200.00'),
                    'total_km': Decimal('6000.00'),
                    'total_hours': Decimal('120.00'),
                    'total_trips': Decimal('24.00'),
                    'total_revenue': Decimal('9600.00'),
                    'rate_per_km': Decimal('0.20'),
                    'rate_per_hour': Decimal('10.00'),
                    'rate_per_trip': Decimal('50.00'),
                    'rate_per_revenue': Decimal('0.125'),
                }
            }
            
            self.persistence.save_cost_rate_snapshots(
                self.company,
                self.period_start,
                self.period_end,
                updated_rates
            )
            
            # Should still have only 4 snapshots (replaced, not duplicated)
            snapshot_count = CostRateSnapshot.objects.filter(
                company=self.company,
                period_start=self.period_start,
                period_end=self.period_end
            ).count()
            
            self.assertEqual(snapshot_count, 4)
            
            # Verify updated values
            km_snapshot = CostRateSnapshot.objects.get(
                company=self.company,
                cost_center=self.cost_center,
                basis_unit='KM'
            )
            self.assertEqual(km_snapshot.total_cost, Decimal('1200.00'))
            self.assertEqual(km_snapshot.total_units, Decimal('6000.00'))
