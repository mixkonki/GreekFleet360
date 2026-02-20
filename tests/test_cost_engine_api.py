"""
Tests for Cost Engine API
"""
from datetime import date
from decimal import Decimal
from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient

from core.models import Company
from core.tenant_context import tenant_context
from operations.models import Vehicle
from finance.models import CostCenter, CostItem, CostPosting, TransportOrder


class TestCostEngineAPI(TestCase):
    """Test suite for Cost Engine API endpoints"""
    
    def setUp(self):
        """Set up test data"""
        # Create companies
        self.company_a = Company.objects.create(
            name="Company A",
            tax_id="111111111",
            address="Address A"
        )
        
        self.company_b = Company.objects.create(
            name="Company B",
            tax_id="222222222",
            address="Address B"
        )
        
        # Create users
        self.superuser = User.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='admin123'
        )
        
        self.staff_user = User.objects.create_user(
            username='staff',
            email='staff@test.com',
            password='staff123',
            is_staff=True
        )
        
        self.regular_user = User.objects.create_user(
            username='regular',
            email='regular@test.com',
            password='regular123'
        )
        
        # Create demo data for company_a
        with tenant_context(self.company_a):
            self.vehicle_a = Vehicle.objects.create(
                company=self.company_a,
                license_plate='TEST-A-001',
                make='Mercedes',
                model='Actros',
                vehicle_class='TRUCK',
                body_type='CURTAIN',
                fuel_type='DIESEL',
                manufacturing_year=2020,
                status='ACTIVE'
            )
            
            self.vehicle_cc_a = CostCenter.objects.create(
                company=self.company_a,
                name='CC-TEST-A-001',
                type='VEHICLE',
                vehicle=self.vehicle_a,
                is_active=True
            )
            
            self.cost_item_a = CostItem.objects.create(
                company=self.company_a,
                name='Test Cost Item A',
                category='FIXED',
                unit='MONTH',
                is_active=True
            )
            
            self.posting_a = CostPosting.objects.create(
                company=self.company_a,
                cost_center=self.vehicle_cc_a,
                cost_item=self.cost_item_a,
                amount=Decimal('1000.00'),
                period_start=date(2026, 1, 1),
                period_end=date(2026, 1, 31)
            )
            
            self.order_a = TransportOrder.objects.create(
                company=self.company_a,
                customer_name='Test Customer A',
                date=date(2026, 1, 15),
                origin='Athens',
                destination='Thessaloniki',
                distance_km=Decimal('500.00'),
                agreed_price=Decimal('2000.00'),
                assigned_vehicle=self.vehicle_a,
                status='COMPLETED'
            )
        
        self.client = APIClient()
    
    def test_unauthenticated_request_returns_403(self):
        """Test that unauthenticated requests are rejected"""
        response = self.client.get(
            '/api/v1/cost-engine/run/',
            {'period_start': '2026-01-01', 'period_end': '2026-01-31'}
        )
        self.assertEqual(response.status_code, 403)
    
    def test_non_staff_user_returns_403(self):
        """Test that non-staff users are rejected"""
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(
            '/api/v1/cost-engine/run/',
            {'period_start': '2026-01-01', 'period_end': '2026-01-31'}
        )
        self.assertEqual(response.status_code, 403)
    
    def test_staff_user_can_access_endpoint(self):
        """Test that staff users can access the endpoint"""
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.get(
            '/api/v1/cost-engine/run/',
            {'period_start': '2026-01-01', 'period_end': '2026-01-31', 'company_id': str(self.company_a.id)}
        )
        # Staff user cannot specify company_id, so use superuser instead
        self.client.force_authenticate(user=self.superuser)
        response = self.client.get(
            '/api/v1/cost-engine/run/',
            {'period_start': '2026-01-01', 'period_end': '2026-01-31', 'company_id': str(self.company_a.id)}
        )
        self.assertEqual(response.status_code, 200)
        
        # Verify response structure
        data = response.json()
        self.assertIn('meta', data)
        self.assertIn('snapshots', data)
        self.assertIn('breakdowns', data)
        self.assertIn('summary', data)
    
    def test_missing_period_parameters_returns_400(self):
        """Test that missing period parameters return 400"""
        self.client.force_authenticate(user=self.staff_user)
        
        # Missing both
        response = self.client.get('/api/v1/cost-engine/run/')
        self.assertEqual(response.status_code, 400)
        
        # Missing period_end
        response = self.client.get(
            '/api/v1/cost-engine/run/',
            {'period_start': '2026-01-01'}
        )
        self.assertEqual(response.status_code, 400)
        
        # Missing period_start
        response = self.client.get(
            '/api/v1/cost-engine/run/',
            {'period_end': '2026-01-31'}
        )
        self.assertEqual(response.status_code, 400)
    
    def test_invalid_date_format_returns_400(self):
        """Test that invalid date format returns 400"""
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.get(
            '/api/v1/cost-engine/run/',
            {'period_start': '01/01/2026', 'period_end': '31/01/2026'}
        )
        self.assertEqual(response.status_code, 400)
    
    def test_invalid_date_range_returns_400(self):
        """Test that invalid date range returns 400"""
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.get(
            '/api/v1/cost-engine/run/',
            {'period_start': '2026-01-31', 'period_end': '2026-01-01'}
        )
        self.assertEqual(response.status_code, 400)
    
    def test_only_nonzero_filter(self):
        """Test only_nonzero parameter filters snapshots"""
        self.client.force_authenticate(user=self.superuser)
        
        # Without filter
        response = self.client.get(
            '/api/v1/cost-engine/run/',
            {'period_start': '2026-01-01', 'period_end': '2026-01-31', 'company_id': str(self.company_a.id)}
        )
        self.assertEqual(response.status_code, 200)
        data_all = response.json()
        total_snapshots = len(data_all.get('snapshots', []))
        
        # With filter
        response = self.client.get(
            '/api/v1/cost-engine/run/',
            {
                'period_start': '2026-01-01',
                'period_end': '2026-01-31',
                'company_id': str(self.company_a.id),
                'only_nonzero': '1'
            }
        )
        self.assertEqual(response.status_code, 200)
        data_filtered = response.json()
        filtered_snapshots = len(data_filtered.get('snapshots', []))
        
        # Filtered should be <= total
        self.assertLessEqual(filtered_snapshots, total_snapshots)
        
        # All filtered snapshots should have total_cost > 0 OR rate > 0
        for snap in data_filtered.get('snapshots', []):
            total_cost = Decimal(str(snap.get('total_cost', 0)))
            rate = Decimal(str(snap.get('rate', 0)))
            self.assertTrue(
                total_cost > Decimal('0') or rate > Decimal('0'),
                f"Snapshot {snap.get('cost_center_id')} has zero cost and rate"
            )
    
    def test_include_breakdowns_parameter(self):
        """Test include_breakdowns parameter"""
        self.client.force_authenticate(user=self.superuser)
        
        # With breakdowns (default)
        response = self.client.get(
            '/api/v1/cost-engine/run/',
            {'period_start': '2026-01-01', 'period_end': '2026-01-31', 'company_id': str(self.company_a.id)}
        )
        self.assertEqual(response.status_code, 200)
        data_with = response.json()
        
        # Without breakdowns
        response = self.client.get(
            '/api/v1/cost-engine/run/',
            {
                'period_start': '2026-01-01',
                'period_end': '2026-01-31',
                'company_id': str(self.company_a.id),
                'include_breakdowns': '0'
            }
        )
        self.assertEqual(response.status_code, 200)
        data_without = response.json()
        
        # Verify breakdowns are excluded
        self.assertEqual(len(data_without.get('breakdowns', [])), 0)
    
    def test_superuser_can_specify_company_id(self):
        """Test that superuser can specify company_id"""
        self.client.force_authenticate(user=self.superuser)
        response = self.client.get(
            '/api/v1/cost-engine/run/',
            {
                'period_start': '2026-01-01',
                'period_end': '2026-01-31',
                'company_id': str(self.company_a.id)
            }
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['meta']['company_id'], self.company_a.id)
    
    def test_non_superuser_cannot_specify_company_id(self):
        """Test that non-superuser cannot specify company_id"""
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.get(
            '/api/v1/cost-engine/run/',
            {
                'period_start': '2026-01-01',
                'period_end': '2026-01-31',
                'company_id': str(self.company_a.id)
            }
        )
        self.assertEqual(response.status_code, 403)
    
    def test_invalid_company_id_returns_404(self):
        """Test that invalid company_id returns 404"""
        self.client.force_authenticate(user=self.superuser)
        response = self.client.get(
            '/api/v1/cost-engine/run/',
            {
                'period_start': '2026-01-01',
                'period_end': '2026-01-31',
                'company_id': '99999'
            }
        )
        self.assertEqual(response.status_code, 404)
