"""
Cost Engine Queries
Data fetching functions for cost calculations
"""
from decimal import Decimal
from django.db.models import Q


def fetch_cost_postings(company, period_start, period_end):
    """
    Fetch CostPosting records overlapping the given period
    
    Args:
        company: Company instance
        period_start: date
        period_end: date
    
    Returns:
        QuerySet of CostPosting filtered by period overlap
    """
    from finance.models import CostPosting
    
    # Fetch postings that overlap with the period
    # Overlap condition: posting.period_start <= period_end AND posting.period_end >= period_start
    postings = CostPosting.objects.filter(
        Q(period_start__lte=period_end) & Q(period_end__gte=period_start)
    ).select_related('cost_center', 'cost_item')
    
    return postings


def fetch_transport_orders(company, period_start, period_end):
    """
    Fetch TransportOrder records for the given period
    
    Args:
        company: Company instance
        period_start: date
        period_end: date
    
    Returns:
        QuerySet of TransportOrder filtered by date range
    """
    from finance.models import TransportOrder
    
    # Fetch orders within the period
    orders = TransportOrder.objects.filter(
        date__gte=period_start,
        date__lte=period_end
    ).select_related('assigned_vehicle')
    
    return orders


def get_order_activity(orders):
    """
    Extract activity metrics from orders
    
    Args:
        orders: QuerySet of TransportOrder
    
    Returns:
        dict with:
            - total_km: Decimal
            - total_revenue: Decimal
            - km_by_vehicle: dict {vehicle_id: Decimal}
            - revenue_by_vehicle: dict {vehicle_id: Decimal}
    """
    total_km = Decimal('0.00')
    total_revenue = Decimal('0.00')
    km_by_vehicle = {}
    revenue_by_vehicle = {}
    
    for order in orders:
        # Distance
        distance = order.distance_km if order.distance_km else Decimal('0.00')
        total_km += distance
        
        # Revenue (check multiple possible field names)
        revenue = Decimal('0.00')
        if hasattr(order, 'revenue') and order.revenue:
            revenue = order.revenue
        elif hasattr(order, 'agreed_price') and order.agreed_price:
            revenue = order.agreed_price
        
        total_revenue += revenue
        
        # Track by vehicle
        if order.assigned_vehicle_id:
            vehicle_id = order.assigned_vehicle_id
            km_by_vehicle[vehicle_id] = km_by_vehicle.get(vehicle_id, Decimal('0.00')) + distance
            revenue_by_vehicle[vehicle_id] = revenue_by_vehicle.get(vehicle_id, Decimal('0.00')) + revenue
    
    return {
        'total_km': total_km,
        'total_revenue': total_revenue,
        'km_by_vehicle': km_by_vehicle,
        'revenue_by_vehicle': revenue_by_vehicle,
    }
