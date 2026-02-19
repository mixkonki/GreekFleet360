"""
Cost Engine Persistence Layer
Handles saving calculation results to database snapshots
"""
from decimal import Decimal
from datetime import date
from typing import Dict, List
from django.db import transaction
from finance.models import (
    CostRateSnapshot,
    OrderCostBreakdown,
    TransportOrder,
    CostCenter,
    Company
)


class CostEnginePersistence:
    """
    Persistence service for Cost Engine calculations
    Saves calculation results to database for historical tracking
    """
    
    @staticmethod
    @transaction.atomic
    def save_cost_rate_snapshots(
        company: Company,
        period_start: date,
        period_end: date,
        cost_center_rates: Dict[int, Dict[str, Decimal]]
    ) -> List[CostRateSnapshot]:
        """
        Save cost rate snapshots for all cost centers
        
        Args:
            company: Company instance
            period_start: Period start date
            period_end: Period end date
            cost_center_rates: Dict mapping cost_center_id to rate data
                {
                    cost_center_id: {
                        'total_cost': Decimal,
                        'total_km': Decimal,
                        'total_hours': Decimal,
                        'total_trips': Decimal,
                        'total_revenue': Decimal,
                        'rate_per_km': Decimal,
                        'rate_per_hour': Decimal,
                        'rate_per_trip': Decimal,
                        'rate_per_revenue': Decimal,
                        'status': str
                    }
                }
        
        Returns:
            List of created CostRateSnapshot instances
        """
        snapshots = []
        
        for cost_center_id, rates in cost_center_rates.items():
            try:
                cost_center = CostCenter.all_objects.get(id=cost_center_id, company=company)
            except CostCenter.DoesNotExist:
                continue
            
            # Create snapshots for each basis unit
            basis_units = [
                ('KM', rates.get('total_km', Decimal('0')), rates.get('rate_per_km', Decimal('0'))),
                ('HOUR', rates.get('total_hours', Decimal('0')), rates.get('rate_per_hour', Decimal('0'))),
                ('TRIP', rates.get('total_trips', Decimal('0')), rates.get('rate_per_trip', Decimal('0'))),
                ('REVENUE', rates.get('total_revenue', Decimal('0')), rates.get('rate_per_revenue', Decimal('0'))),
            ]
            
            for basis_unit, total_units, rate in basis_units:
                # Delete existing snapshot if exists
                CostRateSnapshot.all_objects.filter(
                    company=company,
                    period_start=period_start,
                    period_end=period_end,
                    cost_center=cost_center,
                    basis_unit=basis_unit
                ).delete()
                
                # Determine status
                status = 'OK'
                if total_units == Decimal('0') and basis_unit in ['KM', 'HOUR', 'TRIP']:
                    status = 'MISSING_ACTIVITY'
                
                # Create new snapshot
                snapshot = CostRateSnapshot.all_objects.create(
                    company=company,
                    period_start=period_start,
                    period_end=period_end,
                    cost_center=cost_center,
                    basis_unit=basis_unit,
                    total_cost=rates.get('total_cost', Decimal('0')),
                    total_units=total_units,
                    rate=rate,
                    status=status
                )
                snapshots.append(snapshot)
        
        return snapshots
    
    @staticmethod
    @transaction.atomic
    def save_order_cost_breakdowns(
        company: Company,
        period_start: date,
        period_end: date,
        order_breakdowns: Dict[int, Dict[str, Decimal]]
    ) -> List[OrderCostBreakdown]:
        """
        Save order cost breakdowns for all transport orders
        
        Args:
            company: Company instance
            period_start: Period start date
            period_end: Period end date
            order_breakdowns: Dict mapping order_id to breakdown data
                {
                    order_id: {
                        'vehicle_alloc': Decimal,
                        'overhead_alloc': Decimal,
                        'direct_cost': Decimal,
                        'total_cost': Decimal,
                        'revenue': Decimal,
                        'profit': Decimal,
                        'margin': Decimal,
                        'status': str
                    }
                }
        
        Returns:
            List of created OrderCostBreakdown instances
        """
        breakdowns = []
        
        for order_id, breakdown_data in order_breakdowns.items():
            try:
                transport_order = TransportOrder.all_objects.get(id=order_id, company=company)
            except TransportOrder.DoesNotExist:
                continue
            
            # Delete existing breakdown if exists
            OrderCostBreakdown.all_objects.filter(
                company=company,
                transport_order=transport_order,
                period_start=period_start,
                period_end=period_end
            ).delete()
            
            # Create new breakdown
            breakdown = OrderCostBreakdown.all_objects.create(
                company=company,
                transport_order=transport_order,
                period_start=period_start,
                period_end=period_end,
                vehicle_alloc=breakdown_data.get('vehicle_alloc', Decimal('0')),
                overhead_alloc=breakdown_data.get('overhead_alloc', Decimal('0')),
                direct_cost=breakdown_data.get('direct_cost', Decimal('0')),
                total_cost=breakdown_data.get('total_cost', Decimal('0')),
                revenue=breakdown_data.get('revenue', Decimal('0')),
                profit=breakdown_data.get('profit', Decimal('0')),
                margin=breakdown_data.get('margin', Decimal('0')),
                status=breakdown_data.get('status', 'OK')
            )
            breakdowns.append(breakdown)
        
        return breakdowns
    
    @staticmethod
    def get_cost_rate_snapshot(
        company: Company,
        period_start: date,
        period_end: date,
        cost_center: CostCenter,
        basis_unit: str
    ) -> CostRateSnapshot:
        """
        Retrieve a specific cost rate snapshot
        
        Args:
            company: Company instance
            period_start: Period start date
            period_end: Period end date
            cost_center: CostCenter instance
            basis_unit: Basis unit (KM, HOUR, TRIP, REVENUE)
        
        Returns:
            CostRateSnapshot instance or None
        """
        try:
            return CostRateSnapshot.all_objects.get(
                company=company,
                period_start=period_start,
                period_end=period_end,
                cost_center=cost_center,
                basis_unit=basis_unit
            )
        except CostRateSnapshot.DoesNotExist:
            return None
    
    @staticmethod
    def get_order_cost_breakdown(
        company: Company,
        period_start: date,
        period_end: date,
        transport_order: TransportOrder
    ) -> OrderCostBreakdown:
        """
        Retrieve a specific order cost breakdown
        
        Args:
            company: Company instance
            period_start: Period start date
            period_end: Period end date
            transport_order: TransportOrder instance
        
        Returns:
            OrderCostBreakdown instance or None
        """
        try:
            return OrderCostBreakdown.all_objects.get(
                company=company,
                transport_order=transport_order,
                period_start=period_start,
                period_end=period_end
            )
        except OrderCostBreakdown.DoesNotExist:
            return None
    
    @staticmethod
    def get_all_cost_rate_snapshots(
        company: Company,
        period_start: date,
        period_end: date
    ) -> List[CostRateSnapshot]:
        """
        Retrieve all cost rate snapshots for a period
        
        Args:
            company: Company instance
            period_start: Period start date
            period_end: Period end date
        
        Returns:
            List of CostRateSnapshot instances
        """
        return list(CostRateSnapshot.all_objects.filter(
            company=company,
            period_start=period_start,
            period_end=period_end
        ).select_related('cost_center'))
    
    @staticmethod
    def get_all_order_cost_breakdowns(
        company: Company,
        period_start: date,
        period_end: date
    ) -> List[OrderCostBreakdown]:
        """
        Retrieve all order cost breakdowns for a period
        
        Args:
            company: Company instance
            period_start: Period start date
            period_end: Period end date
        
        Returns:
            List of OrderCostBreakdown instances
        """
        return list(OrderCostBreakdown.all_objects.filter(
            company=company,
            period_start=period_start,
            period_end=period_end
        ).select_related('transport_order', 'transport_order__assigned_vehicle'))
