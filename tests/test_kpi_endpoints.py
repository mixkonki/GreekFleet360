"""
Tests for KPI API Endpoints
GET /api/v1/kpis/company/summary/
GET /api/v1/kpis/company/cost-structure/
GET /api/v1/kpis/company/trend/

Covers:
- Auth / permissions (403 unauthenticated, 403 non-staff, 200 admin)
- Default period (previous full month)
- month=YYYY-MM shortcut
- Tenant isolation
- Correct aggregation math
- grain validation for trend
- basis_unit validation
- group_by validation
"""
from datetime import date
from decimal import Decimal

from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient

from core.models import Company
from core.tenant_context import tenant_context
from operations.models import Vehicle
from finance.models import CostCenter, CostRateSnapshot

SUMMARY_URL = '/api/v1/kpis/company/summary/'
STRUCTURE_URL = '/api/v1/kpis/company/cost-structure/'
TREND_URL = '/api/v1/kpis/company/trend/'


def _make_company(name, tax_id):
    return Company.objects.create(name=name, tax_id=tax_id, address=f"Addr {name}")


def _make_vehicle(company, plate):
    return Vehicle.objects.create(
        company=company, license_plate=plate,
        make='Mercedes', model='Actros',
        vehicle_class='TRUCK', body_type='CURTAIN',
        fuel_type='DIESEL', manufacturing_year=2020, status='ACTIVE',
    )


def _make_cc(company, name, vehicle=None):
    return CostCenter.objects.create(
        company=company, name=name,
        type='VEHICLE' if vehicle else 'OVERHEAD',
        vehicle=vehicle, is_active=True,
    )


def _make_snap(company, cc, period_start, period_end, *,
               basis_unit='KM', total_cost='1000.00',
               total_units='500.000', rate='2.000000', status='OK'):
    return CostRateSnapshot.objects.create(
        company=company, cost_center=cc,
        period_start=period_start, period_end=period_end,
        basis_unit=basis_unit,
        total_cost=Decimal(total_cost),
        total_units=Decimal(total_units),
        rate=Decimal(rate),
        status=status,
    )


class KPIBaseSetup(TestCase):
    """Shared setUp for all KPI test classes."""

    def setUp(self):
        self.company_a = _make_company('KPI-A', '111111111')
        self.company_b = _make_company('KPI-B', '222222222')

        self.superuser = User.objects.create_superuser(
            username='su_kpi', email='su@kpi.com', password='pass'
        )
        self.staff_user = User.objects.create_user(
            username='staff_kpi', email='staff@kpi.com', password='pass', is_staff=True
        )
        self.regular_user = User.objects.create_user(
            username='reg_kpi', email='reg@kpi.com', password='pass'
        )

        # Company A — January 2026
        with tenant_context(self.company_a):
            self.v_a = _make_vehicle(self.company_a, 'KPI-A-001')
            self.cc_a1 = _make_cc(self.company_a, 'CC-KPI-A1', self.v_a)
            self.cc_a2 = _make_cc(self.company_a, 'CC-KPI-A2')  # overhead

            # KM snapshots
            self.snap_a1 = _make_snap(
                self.company_a, self.cc_a1,
                date(2026, 1, 1), date(2026, 1, 31),
                total_cost='1000.00', total_units='500.000', rate='2.000000',
            )
            self.snap_a2 = _make_snap(
                self.company_a, self.cc_a2,
                date(2026, 1, 1), date(2026, 1, 31),
                total_cost='300.00', total_units='0.000', rate='0.000000',
                status='MISSING_ACTIVITY',
            )
            # February 2026 snapshot (for trend tests)
            self.snap_a_feb = _make_snap(
                self.company_a, self.cc_a1,
                date(2026, 2, 1), date(2026, 2, 28),
                total_cost='900.00', total_units='450.000', rate='2.000000',
            )

        # Company B — same period (for isolation tests)
        with tenant_context(self.company_b):
            self.v_b = _make_vehicle(self.company_b, 'KPI-B-001')
            self.cc_b = _make_cc(self.company_b, 'CC-KPI-B', self.v_b)
            _make_snap(
                self.company_b, self.cc_b,
                date(2026, 1, 1), date(2026, 1, 31),
                total_cost='9999.00', total_units='1000.000', rate='9.999000',
            )

        self.client = APIClient()


# ===========================================================================
# Summary endpoint
# ===========================================================================

class KPISummaryTest(KPIBaseSetup):

    def test_unauthenticated_returns_403(self):
        r = self.client.get(SUMMARY_URL, {'period_start': '2026-01-01', 'period_end': '2026-01-31'})
        self.assertEqual(r.status_code, 403)

    def test_regular_user_returns_403(self):
        self.client.force_authenticate(user=self.regular_user)
        r = self.client.get(SUMMARY_URL, {'period_start': '2026-01-01', 'period_end': '2026-01-31'})
        self.assertEqual(r.status_code, 403)

    def test_superuser_returns_200(self):
        self.client.force_authenticate(user=self.superuser)
        r = self.client.get(SUMMARY_URL, {
            'period_start': '2026-01-01', 'period_end': '2026-01-31',
            'company_id': str(self.company_a.id),
        })
        self.assertEqual(r.status_code, 200)

    def test_response_structure(self):
        self.client.force_authenticate(user=self.superuser)
        r = self.client.get(SUMMARY_URL, {
            'period_start': '2026-01-01', 'period_end': '2026-01-31',
            'company_id': str(self.company_a.id),
        })
        data = r.json()
        self.assertIn('meta', data)
        self.assertIn('kpis', data)
        self.assertEqual(data['meta']['schema'], 'kpi-v1')
        for field in ('total_cost', 'total_units', 'avg_rate', 'cost_per_unit',
                      'snapshot_count', 'missing_activity_count', 'missing_rate_count'):
            self.assertIn(field, data['kpis'], f"Missing kpi field: {field}")

    def test_aggregation_math(self):
        """total_cost should be sum of KM snapshots for company_a in Jan 2026."""
        self.client.force_authenticate(user=self.superuser)
        r = self.client.get(SUMMARY_URL, {
            'period_start': '2026-01-01', 'period_end': '2026-01-31',
            'company_id': str(self.company_a.id),
            'basis_unit': 'KM',
        })
        kpis = r.json()['kpis']
        # snap_a1 has total_cost=1000, snap_a2 has basis_unit=KM but MISSING_ACTIVITY
        # Both are KM basis, so total_cost = 1000 + 300 = 1300
        self.assertEqual(Decimal(kpis['total_cost']), Decimal('1300.00'))
        self.assertEqual(kpis['snapshot_count'], 2)
        self.assertEqual(kpis['missing_activity_count'], 1)

    def test_missing_activity_count(self):
        self.client.force_authenticate(user=self.superuser)
        r = self.client.get(SUMMARY_URL, {
            'period_start': '2026-01-01', 'period_end': '2026-01-31',
            'company_id': str(self.company_a.id),
        })
        kpis = r.json()['kpis']
        self.assertEqual(kpis['missing_activity_count'], 1)

    def test_default_period_is_previous_month(self):
        self.client.force_authenticate(user=self.superuser)
        r = self.client.get(SUMMARY_URL, {'company_id': str(self.company_a.id)})
        self.assertEqual(r.status_code, 200)
        meta = r.json()['meta']
        period_end = date.fromisoformat(meta['period_end'])
        from calendar import monthrange
        self.assertEqual(period_end.day, monthrange(period_end.year, period_end.month)[1])

    def test_month_shortcut(self):
        self.client.force_authenticate(user=self.superuser)
        r = self.client.get(SUMMARY_URL, {
            'month': '2026-01',
            'company_id': str(self.company_a.id),
        })
        self.assertEqual(r.status_code, 200)
        meta = r.json()['meta']
        self.assertEqual(meta['period_start'], '2026-01-01')
        self.assertEqual(meta['period_end'], '2026-01-31')

    def test_invalid_month_returns_400(self):
        self.client.force_authenticate(user=self.superuser)
        r = self.client.get(SUMMARY_URL, {
            'month': '01-2026', 'company_id': str(self.company_a.id),
        })
        self.assertEqual(r.status_code, 400)

    def test_invalid_basis_unit_returns_400(self):
        self.client.force_authenticate(user=self.superuser)
        r = self.client.get(SUMMARY_URL, {
            'period_start': '2026-01-01', 'period_end': '2026-01-31',
            'company_id': str(self.company_a.id),
            'basis_unit': 'INVALID',
        })
        self.assertEqual(r.status_code, 400)

    def test_tenant_isolation(self):
        self.client.force_authenticate(user=self.superuser)
        r = self.client.get(SUMMARY_URL, {
            'period_start': '2026-01-01', 'period_end': '2026-01-31',
            'company_id': str(self.company_a.id),
        })
        kpis = r.json()['kpis']
        # company_b has total_cost=9999; company_a has 1000+300=1300
        self.assertNotEqual(Decimal(kpis['total_cost']), Decimal('9999.00'))

    def test_non_superuser_cannot_specify_company_id(self):
        self.client.force_authenticate(user=self.staff_user)
        r = self.client.get(SUMMARY_URL, {
            'period_start': '2026-01-01', 'period_end': '2026-01-31',
            'company_id': str(self.company_a.id),
        })
        self.assertEqual(r.status_code, 403)

    def test_invalid_company_id_returns_404(self):
        self.client.force_authenticate(user=self.superuser)
        r = self.client.get(SUMMARY_URL, {
            'period_start': '2026-01-01', 'period_end': '2026-01-31',
            'company_id': '99999',
        })
        self.assertEqual(r.status_code, 404)

    def test_date_validation_start_after_end(self):
        self.client.force_authenticate(user=self.superuser)
        r = self.client.get(SUMMARY_URL, {
            'period_start': '2026-01-31', 'period_end': '2026-01-01',
            'company_id': str(self.company_a.id),
        })
        self.assertEqual(r.status_code, 400)


# ===========================================================================
# Cost Structure endpoint
# ===========================================================================

class KPICostStructureTest(KPIBaseSetup):

    def test_unauthenticated_returns_403(self):
        r = self.client.get(STRUCTURE_URL, {'period_start': '2026-01-01', 'period_end': '2026-01-31'})
        self.assertEqual(r.status_code, 403)

    def test_superuser_returns_200(self):
        self.client.force_authenticate(user=self.superuser)
        r = self.client.get(STRUCTURE_URL, {
            'period_start': '2026-01-01', 'period_end': '2026-01-31',
            'company_id': str(self.company_a.id),
        })
        self.assertEqual(r.status_code, 200)

    def test_response_structure(self):
        self.client.force_authenticate(user=self.superuser)
        r = self.client.get(STRUCTURE_URL, {
            'period_start': '2026-01-01', 'period_end': '2026-01-31',
            'company_id': str(self.company_a.id),
        })
        data = r.json()
        self.assertIn('meta', data)
        self.assertIn('items', data)
        self.assertIn('totals', data)
        self.assertIn('total_cost', data['totals'])

    def test_items_have_required_fields(self):
        self.client.force_authenticate(user=self.superuser)
        r = self.client.get(STRUCTURE_URL, {
            'period_start': '2026-01-01', 'period_end': '2026-01-31',
            'company_id': str(self.company_a.id),
        })
        data = r.json()
        self.assertGreater(len(data['items']), 0)
        item = data['items'][0]
        for field in ('group_id', 'group_name', 'total_cost', 'share_pct'):
            self.assertIn(field, item, f"Missing field: {field}")

    def test_share_pct_sums_to_100(self):
        self.client.force_authenticate(user=self.superuser)
        r = self.client.get(STRUCTURE_URL, {
            'period_start': '2026-01-01', 'period_end': '2026-01-31',
            'company_id': str(self.company_a.id),
        })
        items = r.json()['items']
        total_share = sum(Decimal(i['share_pct']) for i in items)
        # Allow small rounding tolerance
        self.assertAlmostEqual(float(total_share), 100.0, delta=0.1)

    def test_totals_match_sum_of_items(self):
        self.client.force_authenticate(user=self.superuser)
        r = self.client.get(STRUCTURE_URL, {
            'period_start': '2026-01-01', 'period_end': '2026-01-31',
            'company_id': str(self.company_a.id),
        })
        data = r.json()
        items_sum = sum(Decimal(i['total_cost']) for i in data['items'])
        self.assertEqual(items_sum, Decimal(data['totals']['total_cost']))

    def test_tenant_isolation(self):
        self.client.force_authenticate(user=self.superuser)
        r = self.client.get(STRUCTURE_URL, {
            'period_start': '2026-01-01', 'period_end': '2026-01-31',
            'company_id': str(self.company_a.id),
        })
        data = r.json()
        for item in data['items']:
            self.assertNotEqual(item['total_cost'], '9999.00',
                                "Company B data leaked into Company A response")

    def test_invalid_group_by_returns_400(self):
        self.client.force_authenticate(user=self.superuser)
        r = self.client.get(STRUCTURE_URL, {
            'period_start': '2026-01-01', 'period_end': '2026-01-31',
            'company_id': str(self.company_a.id),
            'group_by': 'driver',
        })
        self.assertEqual(r.status_code, 400)

    def test_month_shortcut(self):
        self.client.force_authenticate(user=self.superuser)
        r = self.client.get(STRUCTURE_URL, {
            'month': '2026-01',
            'company_id': str(self.company_a.id),
        })
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()['meta']['period_start'], '2026-01-01')


# ===========================================================================
# Trend endpoint
# ===========================================================================

class KPITrendTest(KPIBaseSetup):

    def test_unauthenticated_returns_403(self):
        r = self.client.get(TREND_URL, {'period_start': '2026-01-01', 'period_end': '2026-02-28'})
        self.assertEqual(r.status_code, 403)

    def test_superuser_returns_200(self):
        self.client.force_authenticate(user=self.superuser)
        r = self.client.get(TREND_URL, {
            'period_start': '2026-01-01', 'period_end': '2026-02-28',
            'company_id': str(self.company_a.id),
        })
        self.assertEqual(r.status_code, 200)

    def test_response_structure(self):
        self.client.force_authenticate(user=self.superuser)
        r = self.client.get(TREND_URL, {
            'period_start': '2026-01-01', 'period_end': '2026-02-28',
            'company_id': str(self.company_a.id),
        })
        data = r.json()
        self.assertIn('meta', data)
        self.assertIn('series', data)
        self.assertEqual(data['meta']['schema'], 'kpi-v1')

    def test_series_items_have_required_fields(self):
        self.client.force_authenticate(user=self.superuser)
        r = self.client.get(TREND_URL, {
            'period_start': '2026-01-01', 'period_end': '2026-02-28',
            'company_id': str(self.company_a.id),
        })
        series = r.json()['series']
        self.assertGreater(len(series), 0)
        for item in series:
            for field in ('period_start', 'period_end', 'total_cost', 'total_units', 'avg_rate'):
                self.assertIn(field, item, f"Missing series field: {field}")

    def test_grain_month_produces_2_buckets_for_2_months(self):
        self.client.force_authenticate(user=self.superuser)
        r = self.client.get(TREND_URL, {
            'period_start': '2026-01-01', 'period_end': '2026-02-28',
            'company_id': str(self.company_a.id),
            'grain': 'month',
        })
        series = r.json()['series']
        self.assertEqual(len(series), 2)
        self.assertEqual(series[0]['period_start'], '2026-01-01')
        self.assertEqual(series[1]['period_start'], '2026-02-01')

    def test_grain_week_produces_multiple_buckets(self):
        self.client.force_authenticate(user=self.superuser)
        r = self.client.get(TREND_URL, {
            'period_start': '2026-01-01', 'period_end': '2026-01-31',
            'company_id': str(self.company_a.id),
            'grain': 'week',
        })
        series = r.json()['series']
        # January 2026 has 5 weeks (partial)
        self.assertGreaterEqual(len(series), 4)

    def test_invalid_grain_returns_400(self):
        self.client.force_authenticate(user=self.superuser)
        r = self.client.get(TREND_URL, {
            'period_start': '2026-01-01', 'period_end': '2026-02-28',
            'company_id': str(self.company_a.id),
            'grain': 'day',
        })
        self.assertEqual(r.status_code, 400)

    def test_correct_cost_per_month(self):
        """January bucket should have total_cost=1300 (snap_a1+snap_a2 both KM)."""
        self.client.force_authenticate(user=self.superuser)
        r = self.client.get(TREND_URL, {
            'period_start': '2026-01-01', 'period_end': '2026-02-28',
            'company_id': str(self.company_a.id),
            'grain': 'month',
            'basis_unit': 'KM',
        })
        series = r.json()['series']
        jan = next(s for s in series if s['period_start'] == '2026-01-01')
        self.assertEqual(Decimal(jan['total_cost']), Decimal('1300.00'))

    def test_tenant_isolation(self):
        self.client.force_authenticate(user=self.superuser)
        r = self.client.get(TREND_URL, {
            'period_start': '2026-01-01', 'period_end': '2026-01-31',
            'company_id': str(self.company_a.id),
        })
        series = r.json()['series']
        for bucket in series:
            self.assertNotEqual(Decimal(bucket['total_cost']), Decimal('9999.00'),
                                "Company B data leaked into Company A trend")

    def test_month_shortcut(self):
        self.client.force_authenticate(user=self.superuser)
        r = self.client.get(TREND_URL, {
            'month': '2026-01',
            'company_id': str(self.company_a.id),
        })
        self.assertEqual(r.status_code, 200)
        meta = r.json()['meta']
        self.assertEqual(meta['period_start'], '2026-01-01')

    def test_default_period_is_previous_month(self):
        self.client.force_authenticate(user=self.superuser)
        r = self.client.get(TREND_URL, {'company_id': str(self.company_a.id)})
        self.assertEqual(r.status_code, 200)
        meta = r.json()['meta']
        period_end = date.fromisoformat(meta['period_end'])
        from calendar import monthrange
        self.assertEqual(period_end.day, monthrange(period_end.year, period_end.month)[1])

    def test_invalid_basis_unit_returns_400(self):
        self.client.force_authenticate(user=self.superuser)
        r = self.client.get(TREND_URL, {
            'period_start': '2026-01-01', 'period_end': '2026-01-31',
            'company_id': str(self.company_a.id),
            'basis_unit': 'INVALID',
        })
        self.assertEqual(r.status_code, 400)
