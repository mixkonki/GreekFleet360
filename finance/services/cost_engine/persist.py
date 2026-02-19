"""
Cost Engine Persistence Layer
Handles saving calculation results to database snapshots.

Guardrails:
- Only scoped managers (objects) are allowed in this module.
- This module must be used inside tenant_context(company) so that ORM scoping applies.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any, Dict, Iterable, List, Optional, Tuple, Union

from django.conf import settings
from django.db import transaction

from finance.models import (
    Company,
    CostCenter,
    CostRateSnapshot,
    OrderCostBreakdown,
    TransportOrder,
)


def _to_decimal(value: Any) -> Decimal:
    if value is None:
        return Decimal("0")
    if isinstance(value, Decimal):
        return value
    try:
        return Decimal(str(value))
    except Exception:
        return Decimal("0")


def _iter_mapping_or_list(
    payload: Union[Dict[Any, Any], List[Any], Tuple[Any, ...]]
) -> Iterable[Tuple[Optional[int], Any]]:
    """
    Normalizes payload into (id, data) pairs.

    Supports:
      - dict: {id: data_dict}
      - list/tuple: [data_dict, data_dict, ...] (id inferred from keys inside dict if needed)
    """
    if isinstance(payload, dict):
        for k, v in payload.items():
            try:
                kid = int(k)
            except Exception:
                kid = None
            yield kid, v
        return

    if isinstance(payload, (list, tuple)):
        for item in payload:
            yield None, item
        return

    return []


def _require_tenant_context() -> None:
    """
    Fail-fast in DEBUG if tenant context is missing.
    This avoids silent empty queryset behavior during development/tests.
    """
    if not settings.DEBUG:
        return
    try:
        from core.tenant_context import get_current_company  # type: ignore

        if get_current_company() is None:
            raise RuntimeError(
                "Tenant context is missing. Use persistence inside: with tenant_context(company): ..."
            )
    except ImportError:
        # If you don't expose get_current_company, we cannot assert here.
        # Scoping will still protect data, but missing context may look like empty data.
        return


class CostEnginePersistence:
    """
    Persistence service for Cost Engine calculations.

    IMPORTANT:
    - Must be called within tenant_context(company).
    - Uses scoped managers only (objects).
    """

    @staticmethod
    @transaction.atomic
    def save_cost_rate_snapshots(
        company: Company,
        period_start: date,
        period_end: date,
        cost_center_rates_or_snapshots: Union[Dict[Any, Any], List[Any], Tuple[Any, ...]],
    ) -> List[CostRateSnapshot]:
        """
        Accepts either:
          A) dict format (tests):
             { cost_center_id: { total_cost, total_km, rate_per_km, ... } }
             -> creates 4 snapshots per cost center: KM/HOUR/TRIP/REVENUE
          B) list format (calculator):
             [
               {cost_center_id, basis_unit, total_cost, total_units, rate, status},
               ...
             ]
             -> creates exactly those snapshots.
        """
        _require_tenant_context()

        created: List[CostRateSnapshot] = []

        # ----------------------------
        # A) dict-of-dicts format
        # ----------------------------
        if isinstance(cost_center_rates_or_snapshots, dict):
            for maybe_id, data in _iter_mapping_or_list(cost_center_rates_or_snapshots):
                cost_center_id = maybe_id
                rates = data

                if not cost_center_id or not isinstance(rates, dict):
                    continue

                # Use scoped manager + explicit company filter (belt & suspenders)
                try:
                    cost_center = CostCenter.objects.get(id=cost_center_id, company=company)
                except CostCenter.DoesNotExist:
                    continue

                total_cost = _to_decimal(rates.get("total_cost"))

                basis_units = [
                    ("KM", rates.get("total_km", Decimal("0")), rates.get("rate_per_km", Decimal("0"))),
                    ("HOUR", rates.get("total_hours", Decimal("0")), rates.get("rate_per_hour", Decimal("0"))),
                    ("TRIP", rates.get("total_trips", Decimal("0")), rates.get("rate_per_trip", Decimal("0"))),
                    ("REVENUE", rates.get("total_revenue", Decimal("0")), rates.get("rate_per_revenue", Decimal("0"))),
                ]

                for basis_unit, total_units, rate in basis_units:
                    # Replace existing snapshot for this key
                    CostRateSnapshot.objects.filter(
                        company=company,
                        period_start=period_start,
                        period_end=period_end,
                        cost_center=cost_center,
                        basis_unit=basis_unit,
                    ).delete()

                    status = rates.get("status") or "OK"
                    if _to_decimal(total_units) == Decimal("0") and basis_unit in ("KM", "HOUR", "TRIP"):
                        status = "MISSING_ACTIVITY"

                    obj = CostRateSnapshot.objects.create(
                        company=company,
                        period_start=period_start,
                        period_end=period_end,
                        cost_center=cost_center,
                        basis_unit=basis_unit,
                        total_cost=total_cost,
                        total_units=_to_decimal(total_units),
                        rate=_to_decimal(rate),
                        status=status,
                    )
                    created.append(obj)

            return created

        # ----------------------------
        # B) list-of-dicts snapshot format
        # ----------------------------
        for _, data in _iter_mapping_or_list(cost_center_rates_or_snapshots):
            snap = data
            if not isinstance(snap, dict):
                continue

            cost_center_id = snap.get("cost_center_id", snap.get("cost_center"))
            if cost_center_id is None:
                continue
            try:
                cost_center_id = int(cost_center_id)
            except Exception:
                continue

            try:
                cost_center = CostCenter.objects.get(id=cost_center_id, company=company)
            except CostCenter.DoesNotExist:
                continue

            basis_unit = (snap.get("basis_unit") or "KM")
            basis_unit = str(basis_unit).upper()

            # Replace existing snapshot
            CostRateSnapshot.objects.filter(
                company=company,
                period_start=period_start,
                period_end=period_end,
                cost_center=cost_center,
                basis_unit=basis_unit,
            ).delete()

            total_units = _to_decimal(snap.get("total_units"))
            status = snap.get("status") or "OK"
            if total_units == Decimal("0") and basis_unit in ("KM", "HOUR", "TRIP"):
                status = "MISSING_ACTIVITY"

            obj = CostRateSnapshot.objects.create(
                company=company,
                period_start=period_start,
                period_end=period_end,
                cost_center=cost_center,
                basis_unit=basis_unit,
                total_cost=_to_decimal(snap.get("total_cost")),
                total_units=total_units,
                rate=_to_decimal(snap.get("rate")),
                status=status,
            )
            created.append(obj)

        return created

    @staticmethod
    @transaction.atomic
    def save_order_cost_breakdowns(
        company: Company,
        period_start: date,
        period_end: date,
        order_breakdowns_or_list: Union[Dict[Any, Any], List[Any], Tuple[Any, ...]],
    ) -> List[OrderCostBreakdown]:
        """
        Accepts either:
          A) dict format (tests): { order_id: {...} }
          B) list format (calculator): [ {order_id:.., ...}, ... ]
        """
        _require_tenant_context()

        created: List[OrderCostBreakdown] = []

        # A) dict format
        if isinstance(order_breakdowns_or_list, dict):
            for order_id_any, breakdown_data in order_breakdowns_or_list.items():
                try:
                    order_id = int(order_id_any)
                except Exception:
                    continue

                if not isinstance(breakdown_data, dict):
                    continue

                try:
                    transport_order = TransportOrder.objects.get(id=order_id, company=company)
                except TransportOrder.DoesNotExist:
                    continue

                OrderCostBreakdown.objects.filter(
                    company=company,
                    transport_order=transport_order,
                    period_start=period_start,
                    period_end=period_end,
                ).delete()

                obj = OrderCostBreakdown.objects.create(
                    company=company,
                    transport_order=transport_order,
                    period_start=period_start,
                    period_end=period_end,
                    vehicle_alloc=_to_decimal(breakdown_data.get("vehicle_alloc")),
                    overhead_alloc=_to_decimal(breakdown_data.get("overhead_alloc")),
                    direct_cost=_to_decimal(breakdown_data.get("direct_cost")),
                    total_cost=_to_decimal(breakdown_data.get("total_cost")),
                    revenue=_to_decimal(breakdown_data.get("revenue")),
                    profit=_to_decimal(breakdown_data.get("profit")),
                    margin=_to_decimal(breakdown_data.get("margin")),
                    status=breakdown_data.get("status") or "OK",
                )
                created.append(obj)

            return created

        # B) list format
        for b in order_breakdowns_or_list or []:
            if not isinstance(b, dict):
                continue

            order_id = b.get("order_id", b.get("transport_order_id"))
            if not order_id:
                continue

            try:
                order_id = int(order_id)
            except Exception:
                continue

            try:
                transport_order = TransportOrder.objects.get(id=order_id, company=company)
            except TransportOrder.DoesNotExist:
                continue

            OrderCostBreakdown.objects.filter(
                company=company,
                transport_order=transport_order,
                period_start=period_start,
                period_end=period_end,
            ).delete()

            obj = OrderCostBreakdown.objects.create(
                company=company,
                transport_order=transport_order,
                period_start=period_start,
                period_end=period_end,
                vehicle_alloc=_to_decimal(b.get("vehicle_alloc")),
                overhead_alloc=_to_decimal(b.get("overhead_alloc")),
                direct_cost=_to_decimal(b.get("direct_cost")),
                total_cost=_to_decimal(b.get("total_cost")),
                revenue=_to_decimal(b.get("revenue")),
                profit=_to_decimal(b.get("profit")),
                margin=_to_decimal(b.get("margin")),
                status=b.get("status") or "OK",
            )
            created.append(obj)

        return created

    @staticmethod
    def get_cost_rate_snapshot(
        company: Company,
        period_start: date,
        period_end: date,
        cost_center: CostCenter,
        basis_unit: str,
    ) -> Optional[CostRateSnapshot]:
        _require_tenant_context()
        try:
            return CostRateSnapshot.objects.get(
                company=company,
                period_start=period_start,
                period_end=period_end,
                cost_center=cost_center,
                basis_unit=basis_unit,
            )
        except CostRateSnapshot.DoesNotExist:
            return None

    @staticmethod
    def get_order_cost_breakdown(
        company: Company,
        period_start: date,
        period_end: date,
        transport_order: TransportOrder,
    ) -> Optional[OrderCostBreakdown]:
        _require_tenant_context()
        try:
            return OrderCostBreakdown.objects.get(
                company=company,
                transport_order=transport_order,
                period_start=period_start,
                period_end=period_end,
            )
        except OrderCostBreakdown.DoesNotExist:
            return None

    @staticmethod
    def get_all_cost_rate_snapshots(
        company: Company,
        period_start: date,
        period_end: date,
    ) -> List[CostRateSnapshot]:
        _require_tenant_context()
        return list(
            CostRateSnapshot.objects.filter(
                company=company,
                period_start=period_start,
                period_end=period_end,
            ).select_related("cost_center")
        )

    @staticmethod
    def get_all_order_cost_breakdowns(
        company: Company,
        period_start: date,
        period_end: date,
    ) -> List[OrderCostBreakdown]:
        _require_tenant_context()
        return list(
            OrderCostBreakdown.objects.filter(
                company=company,
                period_start=period_start,
                period_end=period_end,
            ).select_related("transport_order", "transport_order__assigned_vehicle")
        )
