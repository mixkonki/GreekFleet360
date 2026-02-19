"""
Cost Engine Calculator
Main orchestrator for cost calculations
"""
from decimal import Decimal
from .queries import fetch_cost_postings, fetch_transport_orders, get_order_activity
from .aggregations import aggregate_postings_by_cost_center
from .snapshots import build_cost_center_snapshot, build_order_breakdown, format_calculation_summary


def calculate_company_costs(company, period_start, period_end):
    """
    Calculate costs for a company for a given period
    
    Main entrypoint for cost engine calculations.
    
    Args:
        company: Company instance
        period_start: date
        period_end: date
    
    Returns:
        dict with:
            - snapshots: list of cost center snapshot dicts
            - breakdowns: list of order breakdown dicts
            - summary: summary statistics dict
    """
    from finance.models import CostCenter
    
    # Step 1: Fetch data
    postings = fetch_cost_postings(company, period_start, period_end)
    orders = fetch_transport_orders(company, period_start, period_end)
    
    # Step 2: Get activity metrics
    activity = get_order_activity(orders)
    
    # Step 3: Aggregate postings by cost center
    cost_by_center = aggregate_postings_by_cost_center(postings)
    
    # Step 4: Build snapshots for each cost center
    snapshots = []
    cost_centers = CostCenter.objects.all()
    
    for cost_center in cost_centers:
        total_cost = cost_by_center.get(cost_center.id, Decimal('0.00'))
        
        # Determine basis unit based on cost center type
        if cost_center.type == 'OVERHEAD':
            basis_unit = 'REVENUE'
            total_units = activity['total_revenue']
        else:
            # Default to KM for VEHICLE and other types
            basis_unit = 'KM'
            
            # If cost center is linked to a vehicle, use that vehicle's activity
            if cost_center.vehicle_id:
                total_units = activity['km_by_vehicle'].get(cost_center.vehicle_id, Decimal('0.00'))
            else:
                # Use total km for unlinked cost centers
                total_units = activity['total_km']
        
        snapshot = build_cost_center_snapshot(
            cost_center,
            total_cost,
            total_units,
            basis_unit,
            period_start,
            period_end
        )
        snapshots.append(snapshot)
    
    # Step 5: Build order breakdowns
    breakdowns = []
    
    # Create lookup for rates by cost center
    rates_by_center = {s['cost_center_id']: s['rate'] for s in snapshots}
    
    for order in orders:
        # Get revenue
        revenue = Decimal('0.00')
        if hasattr(order, 'revenue') and order.revenue:
            revenue = order.revenue
        elif hasattr(order, 'agreed_price') and order.agreed_price:
            revenue = order.agreed_price
        
        # Get distance
        distance = order.distance_km if order.distance_km else Decimal('0.00')
        
        # Calculate vehicle cost
        vehicle_cost = Decimal('0.00')
        if order.assigned_vehicle_id:
            # Find vehicle cost center
            vehicle_center = cost_centers.filter(
                type='VEHICLE',
                vehicle_id=order.assigned_vehicle_id
            ).first()
            
            if vehicle_center:
                vehicle_rate = rates_by_center.get(vehicle_center.id, Decimal('0.00'))
                vehicle_cost = distance * vehicle_rate
        
        # Calculate overhead cost
        overhead_cost = Decimal('0.00')
        overhead_center = cost_centers.filter(type='OVERHEAD').first()
        
        if overhead_center:
            overhead_rate = rates_by_center.get(overhead_center.id, Decimal('0.00'))
            overhead_cost = revenue * overhead_rate
        
        # Build breakdown
        breakdown = build_order_breakdown(order, vehicle_cost, overhead_cost, revenue)
        breakdowns.append(breakdown)
    
    # Step 6: Format summary
    summary = format_calculation_summary(snapshots, breakdowns)
    
    return {
        'snapshots': snapshots,
        'breakdowns': breakdowns,
        'summary': summary,
    }
