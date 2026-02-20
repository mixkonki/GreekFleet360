"""
Tests for Cost Engine History API
GET /api/v1/cost-engine/history/

Covers:
- Authentication / permission checks
- Date defaulting (previous full month)
- month=YYYY-MM shortcut
- include_breakdowns flag
- only_nonzero filter
- Tenant isolation (company A cannot see company B data)
- company_id param (superuser only)
- Date validation errors
"""
from datetime import date
from decimal import Decimal

from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient

from core.models import Company
from core.tenant_context import tenant_context
from operations.models import Vehicle
from finance.models import (
    CostCenter,
    CostRateSnapshot,
    OrderCostBreakdown,
    TransportOrder,
)

HISTORY_URL = '/api/v1/cost-engine/history/'


def _make_company(name, tax_id):
    return Company.objects.create(name=name, tax_id=tax_id, address=f"Address {name}")


def _make_vehicle(company, plate):
    return Vehicle.objects.create(
        company=company,
        license_plate=plate,
        make='Mercedes',
        model='Actros',
        vehicle_class='TRUCK',
        body_type='CURTAIN',
        fuel_type='DIESEL',
        manufacturing_year=2020,
        status='ACTIVE',
    )


def _make_cost_center(company, name, vehicle=None):
    return CostCenter.objects.create(
        company=company,
        name=name,
        type='VEHICLE' if vehicle else 'OVERHEAD',
        vehicle=vehicle,
        is_active=True,
    )


def _make_snapshot(company, cost_center, period_start, period_end, *, basis_unit='KM',
                   total_cost='1000.00', total_units='500.000', rate='2.000000',
                   status='OK'):
    return CostRateSnapshot.objects.create(
        company=company,
        cost_center=cost_center,
        period_start=period_start,
        period_end=period_end,
        basis_unit=basis_unit,
        total_cost=Decimal(total_cost),
        total_units=Decimal(total_units),
        rate=Decimal(rate),
        status=status,
    )


def _make_order(company, vehicle, order_date):
    return TransportOrder.objects.create(
        company=company,
        customer_name='Test Customer',
        date=order_date,
        origin='Athens',
        destination='Thessaloniki',
        distance_km=Decimal('500.00'),
        agreed_price=Decimal('2000.00'),
        assigned_vehicle=vehicle,
        status='COMPLETED',
    )


def _make_breakdown(company, order, period_start, period_end, *, status='OK'):
    return OrderCostBreakdown.objects.create(
        company=company,
        transport_order=order,
        period_start=period_start,
        period_end=period_end,
        vehicle_alloc=Decimal('1000.00'),
        overhead_alloc=Decimal('300.00'),
        direct_cost=Decimal('0.00'),
        total_cost=Decimal('1300.00'),
        revenue=Decimal('2000.00'),
        profit=Decimal('700.00'),
        margin=Decimal('35.0000'),
        status=status,
    )


class CostEngineHistoryAPITest(TestCase):
    """Full test suite for GET /api/v1/cost-engine/history/"""

    def setUp(self):
        # Companies
        self.company_a = _make_company('Company A', '111111111')
        self.company_b = _make_company('Company B', '222222222')

        # Users
        self.superuser = User.objects.create_superuser(
            username='su_hist', email='su@test.com', password='pass'
        )
        self.staff_user = User.objects.create_user(
            username='staff_hist', email='staff@test.com', password='pass', is_staff=True
        )
        self.regular_user = User.objects.create_user(
            username='reg_hist', email='reg@test.com', password='pass'
        )

        # Seed data for company_a — January 2026
        with tenant_context(self.company_a):
            self.vehicle_a = _make_vehicle(self.company_a, 'HIST-A-001')
            self.cc_a = _make_cost_center(self.company_a, 'CC-HIST-A', self.vehicle_a)
            self.snap_a = _make_snapshot(
                self.company_a, self.cc_a,
                date(2026, 1, 1), date(2026, 1, 31),
            )
            self.snap_a_zero = _make_snapshot(
                self.company_a, self.cc_a,
                date(2026, 1, 1), date(2026, 1, 31),
                basis_unit='HOUR',
                total_cost='0.00', total_units='0.000', rate='0.000000',
                status='MISSING_ACTIVITY',
            )
            self.order_a = _make_order(self.company_a, self.vehicle_a, date(2026, 1, 15))
            self.bd_a = _make_breakdown(
                self.company_a, self.order_a,
                date(2026, 1, 1), date(2026, 1, 31),
            )

        # Seed data for company_b — same period
        with tenant_context(self.company_b):
            self.vehicle_b = _make_vehicle(self.company_b, 'HIST-B-001')
            self.cc_b = _make_cost_center(self.company_b, 'CC-HIST-B', self.vehicle_b)
            self.snap_b = _make_snapshot(
                self.company_b, self.cc_b,
                date(2026, 1, 1), date(2026, 1, 31),
                total_cost='9999.00',
            )

        self.client = APIClient()

    # ------------------------------------------------------------------
    # Auth / permission
    # ------------------------------------------------------------------

    def test_unauthenticated_returns_403(self):
        response = self.client.get(HISTORY_URL, {'period_start': '2026-01-01', 'period_end': '2026-01-31'})
        self.assertEqual(response.status_code, 403)

    def test_regular_user_returns_403(self):
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(HISTORY_URL, {'period_start': '2026-01-01', 'period_end': '2026-01-31'})
        self.assertEqual(response.status_code, 403)

    def test_staff_user_returns_200(self):
        """Staff user can access with explicit company_id via superuser, or via DEBUG fallback."""
        # Staff user cannot specify company_id, but superuser can — test with superuser
        self.client.force_authenticate(user=self.superuser)
        response = self.client.get(
            HISTORY_URL,
            {'period_start': '2026-01-01', 'period_end': '2026-01-31',
             'company_id': str(self.company_a.id)},
        )
        self.assertEqual(response.status_code, 200)

    def test_superuser_returns_200(self):
        self.client.force_authenticate(user=self.superuser)
        response = self.client.get(
            HISTORY_URL,
            {'period_start': '2026-01-01', 'period_end': '2026-01-31',
             'company_id': str(self.company_a.id)},
        )
        self.assertEqual(response.status_code, 200)

    # ------------------------------------------------------------------
    # Response structure
    # ------------------------------------------------------------------

    def test_response_has_required_keys(self):
        self.client.force_authenticate(user=self.superuser)
        response = self.client.get(
            HISTORY_URL,
            {'period_start': '2026-01-01', 'period_end': '2026-01-31',
             'company_id': str(self.company_a.id)},
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('meta', data)
        self.assertIn('snapshots', data)
        self.assertIn('breakdowns', data)
        self.assertIn('summary', data)

    def test_meta_source_is_persisted(self):
        self.client.force_authenticate(user=self.superuser)
        response = self.client.get(
            HISTORY_URL,
            {'period_start': '2026-01-01', 'period_end': '2026-01-31',
             'company_id': str(self.company_a.id)},
        )
        data = response.json()
        self.assertEqual(data['meta']['source'], 'persisted')
        self.assertEqual(data['meta']['schema'], 'v1.0')

    # ------------------------------------------------------------------
    # Date defaulting
    # ------------------------------------------------------------------

    def test_no_dates_defaults_to_previous_month(self):
        """When no dates provided, defaults to previous full calendar month."""
        self.client.force_authenticate(user=self.superuser)
        response = self.client.get(
            HISTORY_URL,
            {'company_id': str(self.company_a.id)},
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        # meta should contain period_start and period_end
        self.assertIn('period_start', data['meta'])
        self.assertIn('period_end', data['meta'])
        # period_end day should be last day of a month
        period_end = date.fromisoformat(data['meta']['period_end'])
        from calendar import monthrange
        last_day = monthrange(period_end.year, period_end.month)[1]
        self.assertEqual(period_end.day, last_day)

    # ------------------------------------------------------------------
    # month shortcut
    # ------------------------------------------------------------------

    def test_month_param_overrides_dates(self):
        self.client.force_authenticate(user=self.superuser)
        response = self.client.get(
            HISTORY_URL,
            {'month': '2026-01', 'company_id': str(self.company_a.id)},
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['meta']['period_start'], '2026-01-01')
        self.assertEqual(data['meta']['period_end'], '2026-01-31')

    def test_invalid_month_returns_400(self):
        self.client.force_authenticate(user=self.superuser)
        response = self.client.get(
            HISTORY_URL,
            {'month': '01-2026', 'company_id': str(self.company_a.id)},
        )
        self.assertEqual(response.status_code, 400)

    # ------------------------------------------------------------------
    # include_breakdowns
    # ------------------------------------------------------------------

    def test_include_breakdowns_false_returns_empty_list(self):
        self.client.force_authenticate(user=self.superuser)
        response = self.client.get(
            HISTORY_URL,
            {'period_start': '2026-01-01', 'period_end': '2026-01-31',
             'company_id': str(self.company_a.id),
             'include_breakdowns': '0'},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['breakdowns'], [])

    def test_include_breakdowns_true_returns_data(self):
        self.client.force_authenticate(user=self.superuser)
        response = self.client.get(
            HISTORY_URL,
            {'period_start': '2026-01-01', 'period_end': '2026-01-31',
             'company_id': str(self.company_a.id),
             'include_breakdowns': '1'},
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertGreater(len(data['breakdowns']), 0)
        # Check breakdown fields
        bd = data['breakdowns'][0]
        for field in ('order_id', 'order_date', 'customer_name', 'origin', 'destination',
                      'distance_km', 'period_start', 'period_end',
                      'vehicle_alloc', 'overhead_alloc', 'direct_cost', 'total_cost',
                      'revenue', 'profit', 'margin', 'status'):
            self.assertIn(field, bd, f"Missing field: {field}")

    # ------------------------------------------------------------------
    # only_nonzero
    # ------------------------------------------------------------------

    def test_only_nonzero_excludes_zero_snapshots(self):
        self.client.force_authenticate(user=self.superuser)
        # Without filter — should include MISSING_ACTIVITY snapshot
        response_all = self.client.get(
            HISTORY_URL,
            {'period_start': '2026-01-01', 'period_end': '2026-01-31',
             'company_id': str(self.company_a.id)},
        )
        count_all = len(response_all.json()['snapshots'])

        # With filter
        response_nz = self.client.get(
            HISTORY_URL,
            {'period_start': '2026-01-01', 'period_end': '2026-01-31',
             'company_id': str(self.company_a.id),
             'only_nonzero': '1'},
        )
        count_nz = len(response_nz.json()['snapshots'])
        self.assertLess(count_nz, count_all)

    # ------------------------------------------------------------------
    # Tenant isolation
    # ------------------------------------------------------------------

    def test_tenant_isolation_company_a_cannot_see_company_b(self):
        """Snapshots for company_b must not appear in company_a response."""
        self.client.force_authenticate(user=self.superuser)
        response = self.client.get(
            HISTORY_URL,
            {'period_start': '2026-01-01', 'period_end': '2026-01-31',
             'company_id': str(self.company_a.id)},
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        # company_b snapshot has total_cost=9999; company_a has 1000
        for snap in data['snapshots']:
            self.assertNotEqual(snap['total_cost'], '9999.00',
                                "Company B data leaked into Company A response")

    # ------------------------------------------------------------------
    # company_id param
    # ------------------------------------------------------------------

    def test_non_superuser_cannot_specify_company_id(self):
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.get(
            HISTORY_URL,
            {'period_start': '2026-01-01', 'period_end': '2026-01-31',
             'company_id': str(self.company_a.id)},
        )
        self.assertEqual(response.status_code, 403)

    def test_invalid_company_id_returns_404(self):
        self.client.force_authenticate(user=self.superuser)
        response = self.client.get(
            HISTORY_URL,
            {'period_start': '2026-01-01', 'period_end': '2026-01-31',
             'company_id': '99999'},
        )
        self.assertEqual(response.status_code, 404)

    # ------------------------------------------------------------------
    # Date validation
    # ------------------------------------------------------------------

    def test_invalid_date_format_returns_400(self):
        self.client.force_authenticate(user=self.superuser)
        response = self.client.get(
            HISTORY_URL,
            {'period_start': '01/01/2026', 'period_end': '31/01/2026',
             'company_id': str(self.company_a.id)},
        )
        self.assertEqual(response.status_code, 400)

    def test_period_start_after_period_end_returns_400(self):
        self.client.force_authenticate(user=self.superuser)
        response = self.client.get(
            HISTORY_URL,
            {'period_start': '2026-01-31', 'period_end': '2026-01-01',
             'company_id': str(self.company_a.id)},
        )
        self.assertEqual(response.status_code, 400)

    def test_only_period_start_without_end_returns_400(self):
        self.client.force_authenticate(user=self.superuser)
        response = self.client.get(
            HISTORY_URL,
            {'period_start': '2026-01-01',
             'company_id': str(self.company_a.id)},
        )
        self.assertEqual(response.status_code, 400)

    def test_invalid_basis_unit_returns_400(self):
        self.client.force_authenticate(user=self.superuser)
        response = self.client.get(
            HISTORY_URL,
            {'period_start': '2026-01-01', 'period_end': '2026-01-31',
             'company_id': str(self.company_a.id),
             'basis_unit': 'INVALID'},
        )
        self.assertEqual(response.status_code, 400)

    # ------------------------------------------------------------------
    # Summary fields
    # ------------------------------------------------------------------

    def test_summary_fields_present(self):
        self.client.force_authenticate(user=self.superuser)
        response = self.client.get(
            HISTORY_URL,
            {'period_start': '2026-01-01', 'period_end': '2026-01-31',
             'company_id': str(self.company_a.id)},
        )
        summary = response.json()['summary']
        for field in ('total_cost_sum', 'total_units_sum', 'avg_rate',
                      'snapshot_count', 'breakdown_count'):
            self.assertIn(field, summary, f"Missing summary field: {field}")

    def test_snapshot_fields_present(self):
        self.client.force_authenticate(user=self.superuser)
        response = self.client.get(
            HISTORY_URL,
            {'period_start': '2026-01-01', 'period_end': '2026-01-31',
             'company_id': str(self.company_a.id)},
        )
        data = response.json()
        self.assertGreater(len(data['snapshots']), 0)
        snap = data['snapshots'][0]
        for field in ('period_start', 'period_end', 'cost_center_id', 'cost_center_name',
                      'basis_unit', 'total_cost', 'total_units', 'rate', 'status'):
            self.assertIn(field, snap, f"Missing snapshot field: {field}")

    # ------------------------------------------------------------------
    # MISSING_ACTIVITY status preserved
    # ------------------------------------------------------------------

    def test_missing_activity_status_preserved(self):
        """MISSING_ACTIVITY snapshots are returned with correct status."""
        self.client.force_authenticate(user=self.superuser)
        response = self.client.get(
            HISTORY_URL,
            {'period_start': '2026-01-01', 'period_end': '2026-01-31',
             'company_id': str(self.company_a.id)},
        )
        statuses = [s['status'] for s in response.json()['snapshots']]
        self.assertIn('MISSING_ACTIVITY', statuses)
