"""
Tests for Fuel Entry API
Ensures tenant-scoped fuel entry management with strict isolation
"""
from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework.test import APIClient
from decimal import Decimal

from core.models import Company
from accounts.models import UserProfile
from operations.models import Vehicle, FuelEntry


class FuelEntryAPITests(TestCase):
    """Test Fuel Entry API with tenant isolation"""
    
    def setUp(self):
        """Set up test data with 2 companies"""
        # Company A
        self.company_a = Company.objects.create(
            name="Company A Transport",
            tax_id="111111111",
            business_type="TRANSPORT",
            is_active=True
        )
        
        # Company B
        self.company_b = Company.objects.create(
            name="Company B Logistics",
            tax_id="222222222",
            business_type="TRANSPORT",
            is_active=True
        )
        
        # Manager user for Company A (non-staff)
        self.admin_a = User.objects.create_user(
            username='manager_a',
            password='testpass123',
            email='manager@companya.gr',
            is_staff=False
        )
        UserProfile.objects.create(
            user=self.admin_a,
            company=self.company_a,
            role='MANAGER'
        )
        
        # Manager user for Company B (non-staff)
        self.admin_b = User.objects.create_user(
            username='manager_b',
            password='testpass123',
            email='manager@companyb.gr',
            is_staff=False
        )
        UserProfile.objects.create(
            user=self.admin_b,
            company=self.company_b,
            role='MANAGER'
        )
        
        # Orphan user (no UserProfile/company)
        self.orphan_user = User.objects.create_user(
            username='orphan',
            password='testpass123',
            email='orphan@example.com',
            is_staff=False
        )
        
        # Vehicle for Company A
        self.vehicle_a = Vehicle.objects.create(
            company=self.company_a,
            license_plate='AAA-1111',
            vin='VIN111111111111AA',
            make='Mercedes',
            model='Actros',
            vehicle_class='TRUCK',
            body_type='CURTAIN',
            manufacturing_year=2020,
            purchase_value=Decimal('80000.00')
        )
        
        # Vehicle for Company B
        self.vehicle_b = Vehicle.objects.create(
            company=self.company_b,
            license_plate='BBB-2222',
            vin='VIN222222222222BB',
            make='Volvo',
            model='FH16',
            vehicle_class='TRUCK',
            body_type='BOX',
            manufacturing_year=2021,
            purchase_value=Decimal('90000.00')
        )
        
        # Fuel entry for Company A
        self.fuel_entry_a = FuelEntry.objects.create(
            company=self.company_a,
            vehicle=self.vehicle_a,
            date=timezone.now().date(),
            liters=Decimal('200.00'),
            cost_per_liter=Decimal('1.50'),
            total_cost=Decimal('300.00'),
            odometer_reading=50000,
            is_full_tank=True
        )
        
        # Fuel entry for Company B
        self.fuel_entry_b = FuelEntry.objects.create(
            company=self.company_b,
            vehicle=self.vehicle_b,
            date=timezone.now().date(),
            liters=Decimal('180.00'),
            cost_per_liter=Decimal('1.55'),
            total_cost=Decimal('279.00'),
            odometer_reading=45000,
            is_full_tank=True
        )
        
        self.client = APIClient()
    
    def test_list_returns_only_current_company_entries(self):
        """Test that list returns only current company's fuel entries"""
        self.client.force_authenticate(user=self.admin_a)
        
        response = self.client.get('/api/v1/fuel-entries/')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Should return only Company A's entry
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['vehicle'], self.vehicle_a.id)
        self.assertEqual(data[0]['id'], self.fuel_entry_a.id)
    
    def test_create_succeeds_with_same_company_vehicle(self):
        """Test that valid create succeeds (same-company vehicle)"""
        self.client.force_authenticate(user=self.admin_a)
        
        payload = {
            'vehicle': self.vehicle_a.id,
            'date': timezone.now().date().isoformat(),
            'liters': '150.00',
            'cost_per_liter': '1.60',
            'total_cost': '240.00',
            'odometer_reading': 51000,
            'is_full_tank': True
        }
        
        response = self.client.post('/api/v1/fuel-entries/', payload, format='json')
        
        # Debug: print response if failed
        if response.status_code != 201:
            print(f"Response status: {response.status_code}")
            print(f"Response data: {response.json()}")
        
        self.assertEqual(response.status_code, 201)
        data = response.json()
        
        # Verify company was set server-side (use tenant context)
        from core.tenant_context import tenant_context
        with tenant_context(self.company_a):
            created_entry = FuelEntry.objects.get(id=data['id'])
            self.assertEqual(created_entry.company, self.company_a)
            self.assertEqual(created_entry.vehicle, self.vehicle_a)
    
    def test_create_fails_with_cross_tenant_vehicle(self):
        """Test that Company A cannot create entry for Company B's vehicle"""
        self.client.force_authenticate(user=self.admin_a)
        
        payload = {
            'vehicle': self.vehicle_b.id,  # Company B's vehicle
            'date': timezone.now().date().isoformat(),
            'liters': '150.00',
            'cost_per_liter': '1.60',
            'total_cost': '240.00',
            'odometer_reading': 46000,
            'is_full_tank': True
        }
        
        response = self.client.post('/api/v1/fuel-entries/', payload, format='json')
        
        # Should return validation error (404-style: vehicle not found)
        self.assertEqual(response.status_code, 400)
        self.assertIn('vehicle', response.json())
    
    def test_company_b_sees_only_own_entries(self):
        """Test that Company B sees only their own fuel entries"""
        self.client.force_authenticate(user=self.admin_b)
        
        response = self.client.get('/api/v1/fuel-entries/')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Should return only Company B's entry
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['vehicle'], self.vehicle_b.id)
        self.assertEqual(data[0]['id'], self.fuel_entry_b.id)
    
    def test_unauthenticated_request_denied(self):
        """Test that unauthenticated requests are denied"""
        response = self.client.get('/api/v1/fuel-entries/')
        
        # DRF returns 403 when both IsAuthenticated and IsAdminUser fail
        self.assertIn(response.status_code, [401, 403])
    
    def test_list_ordered_by_date_desc(self):
        """Test that list is ordered by date descending"""
        self.client.force_authenticate(user=self.admin_a)
        
        # Create another entry with earlier date
        earlier_entry = FuelEntry.objects.create(
            company=self.company_a,
            vehicle=self.vehicle_a,
            date=timezone.now().date() - timezone.timedelta(days=7),
            liters=Decimal('100.00'),
            cost_per_liter=Decimal('1.45'),
            total_cost=Decimal('145.00'),
            odometer_reading=49000,
            is_full_tank=False
        )
        
        response = self.client.get('/api/v1/fuel-entries/')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Should have 2 entries, newest first
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]['id'], self.fuel_entry_a.id)  # Newest
        self.assertEqual(data[1]['id'], earlier_entry.id)  # Older
    
    def test_orphan_user_get_returns_403(self):
        """Test that orphan user (no company) gets 403 on GET with Greek message"""
        self.client.force_authenticate(user=self.orphan_user)
        
        response = self.client.get('/api/v1/fuel-entries/')
        
        self.assertEqual(response.status_code, 403)
        data = response.json()
        self.assertIn('detail', data)
        self.assertEqual(
            data['detail'],
            'Ο λογαριασμός σας δεν έχει συσχετισμένη εταιρεία. Επικοινωνήστε με τον διαχειριστή.'
        )
    
    def test_orphan_user_post_returns_403(self):
        """Test that orphan user (no company) gets 403 on POST with Greek message"""
        self.client.force_authenticate(user=self.orphan_user)
        
        payload = {
            'vehicle': self.vehicle_a.id,
            'date': timezone.now().date().isoformat(),
            'liters': '150.00',
            'cost_per_liter': '1.60',
            'total_cost': '240.00',
            'odometer_reading': 51000,
            'is_full_tank': True
        }
        
        response = self.client.post('/api/v1/fuel-entries/', payload, format='json')
        
        self.assertEqual(response.status_code, 403)
        data = response.json()
        self.assertIn('detail', data)
        self.assertEqual(
            data['detail'],
            'Ο λογαριασμός σας δεν έχει συσχετισμένη εταιρεία. Επικοινωνήστε με τον διαχειριστή.'
        )
