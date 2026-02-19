"""
Cost Engine Aggregations
Logic for summing costs and calculating totals
"""
from decimal import Decimal
from collections import defaultdict


def aggregate_postings_by_cost_center(postings):
    """
    Sum CostPosting amounts per CostCenter
    
    Args:
        postings: QuerySet of CostPosting
    
    Returns:
        dict {cost_center_id: Decimal total_amount}
    """
    totals = defaultdict(lambda: Decimal('0.00'))
    
    for posting in postings:
        totals[posting.cost_center_id] += posting.amount
    
    return dict(totals)


def calculate_rate(total_cost, total_units):
    """
    Calculate rate per unit with ZeroDivisionError handling
    
    Args:
        total_cost: Decimal
        total_units: Decimal
    
    Returns:
        tuple (rate: Decimal, status: str)
        status: 'OK' or 'MISSING_ACTIVITY'
    """
    if total_units == 0 or total_units is None:
        return Decimal('0.00'), 'MISSING_ACTIVITY'
    
    try:
        rate = total_cost / total_units
        return rate, 'OK'
    except (ZeroDivisionError, TypeError):
        return Decimal('0.00'), 'MISSING_ACTIVITY'


def calculate_profit_margin(revenue, total_cost):
    """
    Calculate profit and margin
    
    Args:
        revenue: Decimal
        total_cost: Decimal
    
    Returns:
        dict with:
            - profit: Decimal
            - margin: Decimal (as percentage, e.g., 15.5 for 15.5%)
    """
    profit = revenue - total_cost
    
    if revenue > 0:
        margin = (profit / revenue) * Decimal('100.00')
    else:
        margin = Decimal('0.00')
    
    return {
        'profit': profit,
        'margin': margin,
    }
