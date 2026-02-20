"""
Cost Engine History Service
Reads persisted CostRateSnapshot and OrderCostBreakdown records.
Never calls the cost engine pipeline — read-only analytics.
"""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional

from finance.models import CostRateSnapshot, OrderCostBreakdown

# Hard cap on result size
LIMIT_HARD_CAP = 2000
LIMIT_DEFAULT = 500


def _d(value: Any) -> str:
    """Serialize Decimal (or numeric) to string for JSON safety."""
    if value is None:
        return "0"
    if isinstance(value, Decimal):
        return str(value)
    return str(Decimal(str(value)))


def _date_str(d: Any) -> Optional[str]:
    """Serialize date to ISO string."""
    if d is None:
        return None
    if hasattr(d, "isoformat"):
        return d.isoformat()
    return str(d)


def get_cost_engine_history(
    company,
    period_start,
    period_end,
    *,
    cost_center_id: Optional[int] = None,
    basis_unit: Optional[str] = None,
    include_breakdowns: bool = False,
    only_nonzero: bool = False,
    limit: int = LIMIT_DEFAULT,
) -> Dict[str, Any]:
    """
    Return persisted cost engine data for a company and period.

    Must be called inside tenant_context(company).

    Args:
        company: Company instance (tenant)
        period_start: date — period start (inclusive)
        period_end: date — period end (inclusive)
        cost_center_id: optional filter by CostCenter pk
        basis_unit: optional filter by basis unit (KM|HOUR|TRIP|REVENUE)
        include_breakdowns: if True, include OrderCostBreakdown records
        only_nonzero: if True, exclude snapshots where total_cost==0 AND rate==0
        limit: max records to return (hard-capped at LIMIT_HARD_CAP)

    Returns:
        dict with keys: meta, snapshots, breakdowns, summary
    """
    # Enforce limit cap
    limit = min(int(limit), LIMIT_HARD_CAP)
    if limit <= 0:
        limit = LIMIT_DEFAULT

    # --- Snapshots ---
    snap_qs = CostRateSnapshot.objects.filter(
        period_start__lte=period_end,
        period_end__gte=period_start,
    ).select_related("cost_center").order_by("-period_start", "-created_at")

    if cost_center_id is not None:
        snap_qs = snap_qs.filter(cost_center_id=cost_center_id)

    if basis_unit:
        snap_qs = snap_qs.filter(basis_unit=basis_unit.upper())

    if only_nonzero:
        snap_qs = snap_qs.exclude(total_cost=Decimal("0"), rate=Decimal("0"))

    snap_qs = snap_qs[:limit]

    snapshots: List[Dict[str, Any]] = []
    for s in snap_qs:
        snapshots.append({
            "period_start": _date_str(s.period_start),
            "period_end": _date_str(s.period_end),
            "cost_center_id": s.cost_center_id,
            "cost_center_name": s.cost_center.name if s.cost_center else None,
            "basis_unit": s.basis_unit,
            "total_cost": _d(s.total_cost),
            "total_units": _d(s.total_units),
            "rate": _d(s.rate),
            "status": s.status,
        })

    # --- Breakdowns ---
    breakdowns: List[Dict[str, Any]] = []
    if include_breakdowns:
        bd_qs = OrderCostBreakdown.objects.filter(
            period_start__lte=period_end,
            period_end__gte=period_start,
        ).select_related(
            "transport_order",
        ).order_by("-period_start", "-created_at")

        bd_qs = bd_qs[:limit]

        for b in bd_qs:
            order = b.transport_order
            breakdowns.append({
                "order_id": b.transport_order_id,
                "order_date": _date_str(order.date) if order else None,
                "customer_name": order.customer_name if order else None,
                "origin": order.origin if order else None,
                "destination": order.destination if order else None,
                "distance_km": _d(order.distance_km) if order else "0",
                "period_start": _date_str(b.period_start),
                "period_end": _date_str(b.period_end),
                "vehicle_alloc": _d(b.vehicle_alloc),
                "overhead_alloc": _d(b.overhead_alloc),
                "direct_cost": _d(b.direct_cost),
                "total_cost": _d(b.total_cost),
                "revenue": _d(b.revenue),
                "profit": _d(b.profit),
                "margin": _d(b.margin),
                "status": b.status,
            })

    # --- Summary ---
    total_cost_sum = sum(Decimal(s["total_cost"]) for s in snapshots)
    total_units_sum = sum(Decimal(s["total_units"]) for s in snapshots)
    rates = [Decimal(s["rate"]) for s in snapshots if Decimal(s["rate"]) > 0]
    avg_rate = (sum(rates) / Decimal(len(rates))) if rates else Decimal("0")

    summary = {
        "total_cost_sum": _d(total_cost_sum),
        "total_units_sum": _d(total_units_sum),
        "avg_rate": _d(avg_rate),
        "snapshot_count": len(snapshots),
        "breakdown_count": len(breakdowns),
    }

    # --- Meta ---
    meta = {
        "schema": "v1.0",
        "source": "persisted",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "period_start": _date_str(period_start),
        "period_end": _date_str(period_end),
        "filters": {
            "cost_center_id": cost_center_id,
            "basis_unit": basis_unit,
            "include_breakdowns": include_breakdowns,
            "only_nonzero": only_nonzero,
            "limit": limit,
        },
    }

    return {
        "meta": meta,
        "snapshots": snapshots,
        "breakdowns": breakdowns,
        "summary": summary,
    }
