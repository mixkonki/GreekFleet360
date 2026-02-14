"""
Cost Calculator Service - The Brain of GreekFleet 360
Calculates True Break-Even Point and Trip Profitability
"""
from decimal import Decimal
from django.db.models import Avg, Sum, Q
from datetime import datetime, timedelta


class CostCalculator:
    """
    The Financial Brain
    Calculates trip profitability incorporating all cost factors
    """
    
    # Default constants (can be overridden)
    DEFAULT_TIRE_SET_PRICE = Decimal('800.00')
    DEFAULT_TIRE_LIFESPAN_KM = Decimal('50000.00')
    DEFAULT_MAINTENANCE_PER_KM = Decimal('0.05')
    DEFAULT_FUEL_PRICE = Decimal('1.75')  # €/L
    
    def __init__(self, vehicle, distance_km, duration_hours, tolls_cost=Decimal('0.00'), ferry_cost=Decimal('0.00')):
        """
        Initialize calculator with trip parameters
        
        Args:
            vehicle: Vehicle instance (operations.Vehicle)
            distance_km: Trip distance in kilometers
            duration_hours: Trip duration in hours
            tolls_cost: Toll costs (optional)
            ferry_cost: Ferry costs (optional)
        """
        self.vehicle = vehicle
        self.distance_km = Decimal(str(distance_km))
        self.duration_hours = Decimal(str(duration_hours))
        self.tolls_cost = Decimal(str(tolls_cost))
        self.ferry_cost = Decimal(str(ferry_cost))
        
        self.company = vehicle.company
    
    def calculate_trip_profitability(self, agreed_price):
        """
        Calculate complete trip profitability
        
        Args:
            agreed_price: Revenue from the trip
        
        Returns:
            dict: Detailed cost breakdown and profit
        """
        fixed_cost = self._calculate_fixed_cost()
        overhead_cost = self._calculate_overhead_cost()
        variable_cost = self._calculate_variable_cost()
        
        total_cost = fixed_cost + overhead_cost + variable_cost + self.tolls_cost + self.ferry_cost
        profit = Decimal(str(agreed_price)) - total_cost
        profit_margin = (profit / Decimal(str(agreed_price)) * 100) if agreed_price > 0 else Decimal('0.00')
        
        return {
            'fixed_cost': fixed_cost.quantize(Decimal('0.01')),
            'overhead_cost': overhead_cost.quantize(Decimal('0.01')),
            'variable_cost': variable_cost.quantize(Decimal('0.01')),
            'tolls_cost': self.tolls_cost.quantize(Decimal('0.01')),
            'ferry_cost': self.ferry_cost.quantize(Decimal('0.01')),
            'total_cost': total_cost.quantize(Decimal('0.01')),
            'revenue': Decimal(str(agreed_price)).quantize(Decimal('0.01')),
            'profit': profit.quantize(Decimal('0.01')),
            'profit_margin': profit_margin.quantize(Decimal('0.01')),
        }
    
    def _calculate_fixed_cost(self):
        """
        Calculate fixed costs (depreciation, insurance, taxes, driver wage)
        
        Formula:
            (Annual Fixed Costs / Working Hours) * duration_hours
        """
        # Simplified calculation - in production, these would come from actual data
        # For now, we'll use placeholder logic
        
        # Depreciation: (Purchase Price - Salvage Value) / Expected Lifespan Years / Working Hours
        annual_depreciation = self.vehicle.purchase_price / Decimal('5.0')  # 5-year depreciation
        
        # Insurance & Taxes: Estimate based on vehicle value
        annual_insurance = self.vehicle.purchase_price * Decimal('0.03')  # 3% of value
        annual_taxes = Decimal('500.00')  # Placeholder
        
        # Driver wage: Estimate hourly rate
        driver_hourly_wage = Decimal('12.00')  # €12/hour
        
        working_hours_per_year = 252 * 8  # 252 working days * 8 hours
        
        fixed_cost_per_hour = (
            (annual_depreciation + annual_insurance + annual_taxes) / Decimal(str(working_hours_per_year))
        ) + driver_hourly_wage
        
        return fixed_cost_per_hour * self.duration_hours
    
    def _calculate_overhead_cost(self):
        """
        Calculate allocated overhead cost
        
        Uses RecurringExpense model to aggregate all expenses
        """
        from finance.models import RecurringExpense
        
        # Get all active recurring expenses for this company
        expenses = RecurringExpense.objects.filter(
            company=self.company,
            is_active=True
        )
        
        # Calculate total annual overhead
        total_annual_overhead = sum([exp.get_annual_cost() for exp in expenses])
        
        if total_annual_overhead == 0:
            return Decimal('0.00')
        
        # Get fleet size
        fleet_size = self.company.vehicles.filter(status='ACTIVE').count()
        
        if fleet_size == 0:
            return Decimal('0.00')
        
        # Calculate hourly rate
        working_days_per_year = 252
        hours_per_day = 8
        total_working_hours = working_days_per_year * hours_per_day * fleet_size
        
        hourly_rate = total_annual_overhead / Decimal(str(total_working_hours))
        return hourly_rate * self.duration_hours
    
    def _calculate_variable_cost(self):
        """
        Calculate variable costs (fuel, tires, maintenance)
        
        Returns:
            Decimal: Total variable cost
        """
        fuel_cost = self._calculate_fuel_cost()
        tire_cost = self._calculate_tire_cost()
        maintenance_cost = self._calculate_maintenance_cost()
        
        return fuel_cost + tire_cost + maintenance_cost
    
    def _calculate_fuel_cost(self):
        """
        Calculate fuel cost based on actual vehicle consumption history
        
        Formula:
            (Avg L/100km * Current Fuel Price * distance_km) / 100
        """
        from operations.models import FuelEntry
        
        # Get recent fuel entries (last 6 months) where tank was filled
        six_months_ago = datetime.now() - timedelta(days=180)
        
        fuel_entries = FuelEntry.objects.filter(
            vehicle=self.vehicle,
            is_full_tank=True,
            date__gte=six_months_ago
        ).order_by('date')
        
        if fuel_entries.count() < 2:
            # Not enough data - use default consumption
            avg_consumption_per_100km = Decimal('25.0')  # Default: 25L/100km
        else:
            # Calculate actual consumption from full-tank entries
            consumptions = []
            for i in range(1, len(fuel_entries)):
                prev_entry = fuel_entries[i-1]
                curr_entry = fuel_entries[i]
                
                km_driven = curr_entry.odometer_reading - prev_entry.odometer_reading
                liters_consumed = curr_entry.liters
                
                if km_driven > 0:
                    consumption_per_100km = (liters_consumed / Decimal(str(km_driven))) * 100
                    consumptions.append(consumption_per_100km)
            
            if consumptions:
                avg_consumption_per_100km = sum(consumptions) / len(consumptions)
            else:
                avg_consumption_per_100km = Decimal('25.0')
        
        # Get current fuel price (from most recent entry or use default)
        latest_fuel_entry = FuelEntry.objects.filter(vehicle=self.vehicle).order_by('-date').first()
        current_fuel_price = latest_fuel_entry.cost_per_liter if latest_fuel_entry else self.DEFAULT_FUEL_PRICE
        
        fuel_cost = (avg_consumption_per_100km * current_fuel_price * self.distance_km) / 100
        return fuel_cost
    
    def _calculate_tire_cost(self):
        """
        Calculate tire cost per km
        
        Formula:
            (Tire Set Price / Tire Lifespan KM) * distance_km
        """
        # TODO: Get actual tire prices from ServiceLog history
        # For now, use defaults
        tire_cost_per_km = self.DEFAULT_TIRE_SET_PRICE / self.DEFAULT_TIRE_LIFESPAN_KM
        return tire_cost_per_km * self.distance_km
    
    def _calculate_maintenance_cost(self):
        """
        Calculate maintenance cost accrual
        
        Formula:
            Fixed accrual per km (e.g., €0.05/km)
        """
        return self.DEFAULT_MAINTENANCE_PER_KM * self.distance_km
