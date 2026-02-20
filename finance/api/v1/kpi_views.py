"""
KPI API Views — persisted-only, dashboard-fast.
GET /api/v1/kpis/company/summary/
GET /api/v1/kpis/company/cost-structure/
GET /api/v1/kpis/company/trend/
"""
from calendar import monthrange
from datetime import date, timedelta

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, IsAdminUser

from core.tenant_context import tenant_context
from finance.services.analytics.kpis import (
    get_company_summary,
    get_cost_structure,
    get_trend,
    VALID_BASIS_UNITS,
    VALID_GRAINS,
)

# Reuse the shared company resolver from views.py
from finance.api.v1.views import _resolve_company, _previous_full_month


def _parse_period(params):
    """
    Parse period from query params.
    Priority: month > period_start+period_end > default (previous month).
    Returns (period_start, period_end, error_response).
    One of (dates, error_response) will be None.
    """
    month_str = params.get("month")
    period_start_str = params.get("period_start")
    period_end_str = params.get("period_end")

    if month_str:
        try:
            year, mon = int(month_str[:4]), int(month_str[5:7])
            last_day = monthrange(year, mon)[1]
            return date(year, mon, 1), date(year, mon, last_day), None
        except (ValueError, IndexError):
            return None, None, Response(
                {"error": "Invalid month format. Use YYYY-MM"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    if period_start_str or period_end_str:
        if not period_start_str or not period_end_str:
            return None, None, Response(
                {"error": "Provide both period_start and period_end, or use month=YYYY-MM"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            period_start = date.fromisoformat(period_start_str)
            period_end = date.fromisoformat(period_end_str)
        except ValueError:
            return None, None, Response(
                {"error": "Invalid date format. Use YYYY-MM-DD"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if period_start > period_end:
            return None, None, Response(
                {"error": "period_start must be before or equal to period_end"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return period_start, period_end, None

    # Default: previous full calendar month
    period_start, period_end = _previous_full_month()
    return period_start, period_end, None


def _validate_basis_unit(params):
    """Returns (basis_unit_or_None, error_response_or_None)."""
    bu = params.get("basis_unit")
    if bu and bu.upper() not in VALID_BASIS_UNITS:
        return None, Response(
            {"error": f"basis_unit must be one of: {', '.join(sorted(VALID_BASIS_UNITS))}"},
            status=status.HTTP_400_BAD_REQUEST,
        )
    return bu, None


class KPISummaryView(APIView):
    """
    GET /api/v1/kpis/company/summary/

    Aggregate KPIs for a company over a period.
    Reads only from CostRateSnapshot (persisted data).

    Query Parameters:
    - month (YYYY-MM) optional — preferred shortcut
    - period_start (YYYY-MM-DD) optional
    - period_end   (YYYY-MM-DD) optional
    - basis_unit   (KM|HOUR|TRIP|REVENUE) optional, default KM
    - company_id   int optional, superuser only

    Returns: {meta, kpis}
    """

    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        params = request.query_params

        company, err = _resolve_company(request, params.get("company_id"))
        if err:
            return err

        period_start, period_end, err = _parse_period(params)
        if err:
            return err

        basis_unit_raw, err = _validate_basis_unit(params)
        if err:
            return err
        basis_unit = (basis_unit_raw or "KM").upper()

        with tenant_context(company):
            payload = get_company_summary(
                company, period_start, period_end, basis_unit=basis_unit
            )

        return Response(payload, status=status.HTTP_200_OK)


class KPICostStructureView(APIView):
    """
    GET /api/v1/kpis/company/cost-structure/

    Cost distribution by cost center for a period.
    Reads only from CostRateSnapshot (persisted data).

    Query Parameters:
    - month (YYYY-MM) optional
    - period_start / period_end optional
    - basis_unit optional
    - group_by=cost_center (default, only supported value currently)
    - company_id int optional, superuser only

    Returns: {meta, items, totals}
    """

    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        params = request.query_params

        company, err = _resolve_company(request, params.get("company_id"))
        if err:
            return err

        period_start, period_end, err = _parse_period(params)
        if err:
            return err

        basis_unit_raw, err = _validate_basis_unit(params)
        if err:
            return err

        group_by = params.get("group_by", "cost_center")
        if group_by != "cost_center":
            return Response(
                {"error": "group_by must be 'cost_center' (only supported value)"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with tenant_context(company):
            payload = get_cost_structure(
                company, period_start, period_end,
                basis_unit=basis_unit_raw,
                group_by=group_by,
            )

        return Response(payload, status=status.HTTP_200_OK)


class KPITrendView(APIView):
    """
    GET /api/v1/kpis/company/trend/

    Time-series cost trend for a company.
    Reads only from CostRateSnapshot (persisted data).

    Query Parameters:
    - period_start (YYYY-MM-DD) required (or month=YYYY-MM)
    - period_end   (YYYY-MM-DD) required (or month=YYYY-MM)
    - month        (YYYY-MM) optional shortcut
    - grain        (month|week) optional, default month
    - basis_unit   (KM|HOUR|TRIP|REVENUE) optional, default KM
    - company_id   int optional, superuser only

    Returns: {meta, series}
    """

    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        params = request.query_params

        company, err = _resolve_company(request, params.get("company_id"))
        if err:
            return err

        period_start, period_end, err = _parse_period(params)
        if err:
            return err

        basis_unit_raw, err = _validate_basis_unit(params)
        if err:
            return err
        basis_unit = (basis_unit_raw or "KM").upper()

        grain = params.get("grain", "month").lower()
        if grain not in VALID_GRAINS:
            return Response(
                {"error": f"grain must be one of: {', '.join(sorted(VALID_GRAINS))}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with tenant_context(company):
            payload = get_trend(
                company, period_start, period_end,
                grain=grain,
                basis_unit=basis_unit,
            )

        return Response(payload, status=status.HTTP_200_OK)
