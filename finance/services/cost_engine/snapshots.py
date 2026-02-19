"""
Cost Engine Snapshots
Logic for formatting calculation results into snapshot structures
"""
from decimal import Decimal


def build_cost_center_snapshot(cost_center, total_cost, total_units, basis_unit, period_start, period_end):
    """
    Build a snapshot dictionary for a CostCenter
    
    Args:
        cost_center: CostCenter instance
        total_cost: Decimal
        total_units: Decimal
        basis_unit: str ('KM' or 'REVENUE')
        period_start: date
        period_end: date
    
    Returns:
        dict with snapshot data
    """
    from .aggregations import calculate_rate
    
    rate, status = calculate_rate(total_cost, total_units)
    
    return {
        'cost_center_id': cost_center.id,
        'cost_center_name': cost_center.name,
        'cost_center_type': cost_center.type,
        'period_start': period_start,
        'period_end': period_end,
        'basis_unit': basis_unit,
        'total_cost': total_cost,
        'total_units': total_units,
        'rate': rate,
        'status': status,
    }


def build_order_breakdown(order, vehicle_cost, overhead_cost, revenue):
    """
    Build a cost breakdown dictionary for a TransportOrder
    
    Args:
        order: TransportOrder instance
        vehicle_cost: Decimal
        overhead_cost: Decimal
        revenue: Decimal
    
    Returns:
        dict with breakdown data
    """
    from .aggregations import calculate_profit_margin
    
    total_cost = vehicle_cost + overhead_cost
    profit_data = calculate_profit_margin(revenue, total_cost)
    
    return {
        'order_id': order.id,
        'order_ref': str(order),
        'direct_cost': Decimal('0.00'),  # v1: no direct costs yet
        'vehicle_alloc': vehicle_cost,
        'driver_alloc': Decimal('0.00'),  # v1: no driver allocation yet
        'overhead_alloc': overhead_cost,
        'total_cost': total_cost,
        'revenue': revenue,
        'profit': profit_data['profit'],
        'margin': profit_data['margin'],
        'status': 'OK',
    }


def format_calculation_summary(snapshots, breakdowns):
    """
    Format overall calculation summary
    
    Args:
        snapshots: list of snapshot dicts
        breakdowns: list of breakdown dicts
    
    Returns:
        dict with summary statistics
    """
    total_cost = sum(s['total_cost'] for s in snapshots)
    total_revenue = sum(b['revenue'] for b in breakdowns)
    total_profit = sum(b['profit'] for b in breakdowns)
    
    avg_margin = Decimal('0.00')
    if breakdowns:
        avg_margin = sum(b['margin'] for b in breakdowns) / Decimal(str(len(breakdowns)))
    
    return {
        'total_snapshots': len(snapshots),
        'total_breakdowns': len(breakdowns),
        'total_cost': total_cost,
        'total_revenue': total_revenue,
        'total_profit': total_profit,
        'average_margin': avg_margin,
    }
