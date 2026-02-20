"""
KPI Analytics Service
Reads ONLY from CostRateSnapshot (persisted data).
Never calls the cost engine pipeline.
All functions must be called inside tenant_context(company).
"""
from __future__ import annotations

from calendar import monthrange
from datetime import date, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional

from django.db.models import Sum, Count, Avg, Q

from finance.models import CostRateSnapshot

VALID_BASIS_UNITS = {"KM", "HOUR", "TRIP", "REVENUE"}
VALID_GRAINS = {"month", "week"}


def _d(value: Any) -> str:
    """Serialize Decimal (or numeric) to string."""
    if value is None:
        return "0"
    if isinstance(value, Decimal):
        return str(value)
    try:
        return str(Decimal(str(value)))
    except Exception:
        return "0"


def _date_str(d: Any) -> Optional[str]:
    if d is None:
        return None
    if hasattr(d, "isoformat"):
        return d.isoformat()
    return str(d)


def _previous_full_month():
    """Return (period_start, period_end) for the previous full calendar month."""
    today = date.today()
    first_of_current = today.replace(day=1)
    last_of_prev = first_of_current - timedelta(days=1)
    first_of_prev = last_of_prev.replace(day=1)
    return first_of_prev, last_of_prev


def _month_range(year: int, month: int):
    """Return (first_day, last_day) for a given year/month."""
    last_day = monthrange(year, month)[1]
    return date(year, month, 1), date(year, month, last_day)


# ---------------------------------------------------------------------------
# 1. Company Summary KPIs
# ---------------------------------------------------------------------------

def get_company_summary(
    company,
    period_start: date,
    period_end: date,
    *,
    basis_unit: str = "KM",
) -> Dict[str, Any]:
    """
    Aggregate KPIs for a company over a period.

    Must be called inside tenant_context(company).

    Returns:
        dict with keys: meta, kpis
    """
    basis_unit = basis_unit.upper()

    qs = CostRateSnapshot.objects.filter(
        period_start__lte=period_end,
        period_end__gte=period_start,
        basis_unit=basis_unit,
    )

    agg = qs.aggregate(
        total_cost=Sum("total_cost"),
        total_units=Sum("total_units"),
        snapshot_count=Count("id"),
        missing_activity_count=Count("id", filter=Q(status="MISSING_ACTIVITY")),
        missing_rate_count=Count("id", filter=Q(status="MISSING_RATE")),
    )

    total_cost = agg["total_cost"] or Decimal("0")
    total_units = agg["total_units"] or Decimal("0")
    snapshot_count = agg["snapshot_count"] or 0
    missing_activity_count = agg["missing_activity_count"] or 0
    missing_rate_count = agg["missing_rate_count"] or 0

    # avg_rate = weighted average (total_cost / total_units) or simple avg of rates
    if total_units > Decimal("0"):
        avg_rate = total_cost / total_units
    else:
        rate_agg = qs.aggregate(avg_rate=Avg("rate"))
        avg_rate = rate_agg["avg_rate"] or Decimal("0")

    return {
        "meta": {
            "schema": "kpi-v1",
            "period_start": _date_str(period_start),
            "period_end": _date_str(period_end),
            "grain": "period",
            "basis_unit": basis_unit,
        },
        "kpis": {
            "total_cost": _d(total_cost),
            "total_units": _d(total_units),
            "avg_rate": _d(avg_rate),
            "cost_per_unit": _d(avg_rate),  # alias for clarity
            "snapshot_count": snapshot_count,
            "missing_activity_count": missing_activity_count,
            "missing_rate_count": missing_rate_count,
        },
    }


# ---------------------------------------------------------------------------
# 2. Cost Structure (breakdown by cost center)
# ---------------------------------------------------------------------------

def get_cost_structure(
    company,
    period_start: date,
    period_end: date,
    *,
    basis_unit: Optional[str] = None,
    group_by: str = "cost_center",
) -> Dict[str, Any]:
    """
    Cost distribution by cost center for a period.

    Must be called inside tenant_context(company).

    Returns:
        dict with keys: meta, items, totals
    """
    qs = CostRateSnapshot.objects.filter(
        period_start__lte=period_end,
        period_end__gte=period_start,
    ).select_related("cost_center")

    if basis_unit:
        qs = qs.filter(basis_unit=basis_unit.upper())

    # Aggregate total cost per cost center
    from django.db.models import Sum as _Sum
    rows = (
        qs.values("cost_center_id", "cost_center__name")
        .annotate(total_cost=_Sum("total_cost"))
        .order_by("-total_cost")
    )

    grand_total = sum(r["total_cost"] or Decimal("0") for r in rows)

    items = []
    for row in rows:
        cost = row["total_cost"] or Decimal("0")
        share = (cost / grand_total * Decimal("100")) if grand_total > 0 else Decimal("0")
        items.append({
            "group_id": row["cost_center_id"],
            "group_name": row["cost_center__name"] or "",
            "total_cost": _d(cost),
            "share_pct": _d(share.quantize(Decimal("0.01"))),
        })

    return {
        "meta": {
            "schema": "kpi-v1",
            "period_start": _date_str(period_start),
            "period_end": _date_str(period_end),
            "grain": "period",
            "basis_unit": basis_unit,
            "group_by": group_by,
        },
        "items": items,
        "totals": {
            "total_cost": _d(grand_total),
        },
    }


# ---------------------------------------------------------------------------
# 3. Trend (time series)
# ---------------------------------------------------------------------------

def _month_buckets(period_start: date, period_end: date) -> List[tuple]:
    """Generate (bucket_start, bucket_end) tuples by calendar month."""
    buckets = []
    current = period_start.replace(day=1)
    while current <= period_end:
        last_day = monthrange(current.year, current.month)[1]
        bucket_end = min(date(current.year, current.month, last_day), period_end)
        bucket_start = max(current, period_start)
        buckets.append((bucket_start, bucket_end))
        # Advance to next month
        if current.month == 12:
            current = date(current.year + 1, 1, 1)
        else:
            current = date(current.year, current.month + 1, 1)
    return buckets


def _week_buckets(period_start: date, period_end: date) -> List[tuple]:
    """Generate (bucket_start, bucket_end) tuples by ISO week (Mon-Sun)."""
    buckets = []
    # Start from Monday of the week containing period_start
    current = period_start - timedelta(days=period_start.weekday())
    while current <= period_end:
        bucket_start = max(current, period_start)
        bucket_end = min(current + timedelta(days=6), period_end)
        buckets.append((bucket_start, bucket_end))
        current += timedelta(days=7)
    return buckets


def get_trend(
    company,
    period_start: date,
    period_end: date,
    *,
    grain: str = "month",
    basis_unit: str = "KM",
) -> Dict[str, Any]:
    """
    Time-series cost trend for a company.

    Must be called inside tenant_context(company).

    Args:
        grain: 'month' or 'week'
        basis_unit: KM|HOUR|TRIP|REVENUE

    Returns:
        dict with keys: meta, series
    """
    grain = grain.lower()
    basis_unit = basis_unit.upper()

    if grain == "month":
        buckets = _month_buckets(period_start, period_end)
    else:
        buckets = _week_buckets(period_start, period_end)

    series = []
    for bucket_start, bucket_end in buckets:
        qs = CostRateSnapshot.objects.filter(
            period_start__lte=bucket_end,
            period_end__gte=bucket_start,
            basis_unit=basis_unit,
        )
        agg = qs.aggregate(
            total_cost=Sum("total_cost"),
            total_units=Sum("total_units"),
        )
        total_cost = agg["total_cost"] or Decimal("0")
        total_units = agg["total_units"] or Decimal("0")
        avg_rate = (total_cost / total_units) if total_units > 0 else Decimal("0")

        series.append({
            "period_start": _date_str(bucket_start),
            "period_end": _date_str(bucket_end),
            "total_cost": _d(total_cost),
            "total_units": _d(total_units),
            "avg_rate": _d(avg_rate),
        })

    return {
        "meta": {
            "schema": "kpi-v1",
            "period_start": _date_str(period_start),
            "period_end": _date_str(period_end),
            "grain": grain,
            "basis_unit": basis_unit,
        },
        "series": series,
    }
