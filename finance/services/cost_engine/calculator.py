"""
Cost Engine Calculator
Main orchestrator for cost calculations
"""

from __future__ import annotations

from datetime import datetime, timezone, date
from decimal import Decimal
from typing import Any, Dict, List, Optional

from django.conf import settings

from .queries import fetch_cost_postings, fetch_transport_orders, get_order_activity
from .aggregations import aggregate_postings_by_cost_center
from .snapshots import (
    build_cost_center_snapshot,
    build_order_breakdown,
    format_calculation_summary,
)

# -----------------------------
# Result schema + normalization
# -----------------------------

VALID_BASIS_UNITS = {"KM", "HOUR", "TRIP", "REVENUE"}


def _to_decimal(value: Any) -> Decimal:
    if value is None:
        return Decimal("0")
    if isinstance(value, Decimal):
        return value
    try:
        return Decimal(str(value))
    except Exception:
        return Decimal("0")


def _normalize_basis_unit(basis_unit: Any) -> str:
    bu = str(basis_unit or "KM").upper()
    return bu if bu in VALID_BASIS_UNITS else "KM"


def _normalize_snapshot(snapshot: Dict[str, Any]) -> Dict[str, Any]:
    """
    Ensures snapshot has consistent types and status rules.
    """
    basis_unit = _normalize_basis_unit(snapshot.get("basis_unit"))
    total_units = _to_decimal(snapshot.get("total_units"))
    total_cost = _to_decimal(snapshot.get("total_cost"))
    rate = _to_decimal(snapshot.get("rate"))

    status = snapshot.get("status") or "OK"

    # Deterministic missing-activity rule
    if total_units == Decimal("0") and basis_unit in {"KM", "HOUR", "TRIP"}:
        status = "MISSING_ACTIVITY"

    snapshot["basis_unit"] = basis_unit
    snapshot["total_units"] = total_units
    snapshot["total_cost"] = total_cost
    snapshot["rate"] = rate
    snapshot["status"] = status
    return snapshot


def _engine_version() -> str:
    """
    Keep this lightweight and safe on Windows / non-git deployments.
    Uses env var if available; otherwise returns 'dev'.
    """
    # If you later set something like ENGINE_VERSION in environment, it will show up here.
    try:
        import os

        v = os.environ.get("ENGINE_VERSION")
        if v:
            return v
    except Exception:
        pass
    return "dev"


def _require_tenant_context() -> None:
    """
    Fail-fast in DEBUG if tenant context is missing.
    Adjust the import below if your tenant context stores state differently.
    """
    if not settings.DEBUG:
        return

    # Best-effort detection: if your tenant_context sets a threadlocal,
    # you can improve this check later. For now, we don't block non-debug.
    # If you already have a function like get_current_company(), use it here.
    try:
        from core.tenant_context import get_current_company  # type: ignore

        if get_current_company() is None:
            raise RuntimeError(
                "Tenant context is missing. Run calculations inside: with tenant_context(company): ..."
            )
    except ImportError:
        # If you don't expose get_current_company, we cannot assert here.
        # We'll rely on scoped managers returning empty sets by design.
        return


# -----------------------------
# Public service entry point
# -----------------------------


def calculate_company_costs(company, period_start: date, period_end: date) -> Dict[str, Any]:
    """
    Calculate costs for a company for a given period.

    Main entrypoint for cost engine calculations.

    Args:
        company: Company instance
        period_start: date
        period_end: date

    Returns:
        dict (schema v1):
            - meta: dict (schema_version, engine_version, company_id, period_start, period_end, generated_at)
            - snapshots: list of cost center snapshot dicts
            - breakdowns: list of order breakdown dicts
            - summary: summary statistics dict
    """
    from finance.models import CostCenter

    _require_tenant_context()

    # Step 0: Load cost centers once (scoped manager -> company-safe)
    cost_centers_qs = CostCenter.objects.all()
    cost_centers = list(cost_centers_qs)

    # Build handy lookups to avoid repeated filtering in loops
    vehicle_center_by_vehicle_id: Dict[int, Any] = {}
    overhead_centers: List[Any] = []
    for cc in cost_centers:
        if getattr(cc, "type", None) == "VEHICLE" and getattr(cc, "vehicle_id", None):
            vehicle_center_by_vehicle_id[cc.vehicle_id] = cc
        if getattr(cc, "type", None) == "OVERHEAD":
            overhead_centers.append(cc)

    overhead_center = overhead_centers[0] if overhead_centers else None

    # Step 1: Fetch data (must be scoped internally by tenant context / safe managers)
    postings = fetch_cost_postings(company, period_start, period_end)
    orders = fetch_transport_orders(company, period_start, period_end)

    # Step 2: Activity metrics
    activity = get_order_activity(orders)

    total_revenue = _to_decimal(activity.get("total_revenue"))
    total_km = _to_decimal(activity.get("total_km"))
    km_by_vehicle = activity.get("km_by_vehicle") or {}

    # Step 3: Aggregate postings by cost center
    cost_by_center = aggregate_postings_by_cost_center(postings)

    # Step 4: Build cost-center snapshots
    snapshots: List[Dict[str, Any]] = []

    for cost_center in cost_centers:
        total_cost = _to_decimal(cost_by_center.get(cost_center.id, Decimal("0.00")))

        # Determine basis and units
        if getattr(cost_center, "type", None) == "OVERHEAD":
            basis_unit = "REVENUE"
            units = total_revenue
        else:
            basis_unit = "KM"
            if getattr(cost_center, "vehicle_id", None):
                units = _to_decimal(km_by_vehicle.get(cost_center.vehicle_id, Decimal("0.00")))
            else:
                units = total_km

        snapshot = build_cost_center_snapshot(
            cost_center=cost_center,
            total_cost=total_cost,
            total_units=units,
            basis_unit=basis_unit,
            period_start=period_start,
            period_end=period_end,
        )

        snapshots.append(_normalize_snapshot(snapshot))

    # Step 5: Build order breakdowns
    breakdowns: List[Dict[str, Any]] = []

    # Create lookup for rates by cost center
    rates_by_center: Dict[int, Decimal] = {}
    for s in snapshots:
        try:
            cid = int(s.get("cost_center_id"))
        except Exception:
            continue
        rates_by_center[cid] = _to_decimal(s.get("rate"))

    for order in orders:
        # Revenue
        revenue = Decimal("0.00")
        if hasattr(order, "revenue") and order.revenue:
            revenue = _to_decimal(order.revenue)
        elif hasattr(order, "agreed_price") and order.agreed_price:
            revenue = _to_decimal(order.agreed_price)

        # Distance
        distance = _to_decimal(getattr(order, "distance_km", None))

        # Vehicle cost
        vehicle_cost = Decimal("0.00")
        assigned_vehicle_id = getattr(order, "assigned_vehicle_id", None)
        if assigned_vehicle_id:
            vehicle_center = vehicle_center_by_vehicle_id.get(assigned_vehicle_id)
            if vehicle_center:
                vehicle_rate = rates_by_center.get(vehicle_center.id, Decimal("0.00"))
                vehicle_cost = distance * _to_decimal(vehicle_rate)

        # Overhead cost
        overhead_cost = Decimal("0.00")
        if overhead_center:
            overhead_rate = rates_by_center.get(overhead_center.id, Decimal("0.00"))
            overhead_cost = revenue * _to_decimal(overhead_rate)

        breakdown = build_order_breakdown(order, vehicle_cost, overhead_cost, revenue)
        breakdowns.append(breakdown)

    # Step 6: Summary
    summary = format_calculation_summary(snapshots, breakdowns)

    # Ensure summary fields are Decimals where appropriate
    # (prevents mixed int/Decimal in JSON rendering)
    if isinstance(summary, dict):
        summary["total_cost"] = _to_decimal(summary.get("total_cost"))
        summary["total_revenue"] = _to_decimal(summary.get("total_revenue"))
        summary["total_profit"] = _to_decimal(summary.get("total_profit"))
        summary["average_margin"] = _to_decimal(summary.get("average_margin"))

    meta = {
        "schema_version": 1,
        "engine_version": _engine_version(),
        "company_id": getattr(company, "id", None),
        "period_start": period_start,
        "period_end": period_end,
        "generated_at": datetime.now(timezone.utc),
    }

    return {
        "meta": meta,
        "snapshots": snapshots,
        "breakdowns": breakdowns,
        "summary": summary,
    }
