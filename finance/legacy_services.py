"""
Cost Calculator Service - The Brain of GreekFleet 360
Calculates True Break-Even Point and Trip Profitability

Phase 5: Freight Cost Intelligence System
Hierarchical Cost Model with 4 Levels
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


# ============================================================================
# FREIGHT COST INTELLIGENCE SYSTEM - Phase 5
# ============================================================================

class FreightCostEngine:
    """
    Freight Cost Intelligence Engine
    Implements hierarchical cost model with 4 levels:
    
    Level 1: Fixed Costs (Depreciation, Driver Wages)
    Level 2: Variable Costs per KM (Fuel, Tires, Maintenance)
    Level 3: Trip-Specific Costs (Tolls, Ferries)
    Level 4: Overhead Allocation (Office, Management, etc.)
    """
    
    # Default constants
    DEFAULT_FUEL_PRICE = Decimal('1.75')  # €/L
    DEFAULT_TIRE_COST_PER_KM = Decimal('0.05')  # €/km
    DEFAULT_MAINTENANCE_PER_KM = Decimal('0.08')  # €/km
    
    def __init__(self, vehicle):
        """
        Initialize engine with vehicle
        
        Args:
            vehicle: Vehicle instance (operations.Vehicle)
        """
        self.vehicle = vehicle
        self.company = vehicle.company
    
    def calculate_hourly_rate(self):
        """
        Calculate hourly rate (Level 1 Fixed + Level 4 Overheads)
        
        Formula:
            Hourly Rate = (Level 1 + Level 4) / (Working Days × Hours × Utilization Rate)
        
        Returns:
            Decimal: Hourly rate in €/hour
        """
        # Level 1: Fixed Costs (Depreciation + Driver Wages)
        annual_depreciation = self.vehicle.annual_depreciation
        
        # Get driver wage from assigned employee
        from core.models import Employee
        assigned_employee = Employee.objects.filter(
            company=self.company,
            assigned_vehicle=self.vehicle,
            is_active=True
        ).first()
        
        if assigned_employee:
            annual_driver_cost = assigned_employee.total_annual_cost
        else:
            # Default driver cost if no assignment
            annual_driver_cost = Decimal('25000.00')  # €25k/year
        
        level_1_annual = annual_depreciation + annual_driver_cost
        
        # Level 4: Overhead Allocation
        from finance.models import CompanyExpense
        
        # Get all company expenses (overheads)
        overhead_expenses = CompanyExpense.objects.filter(
            company=self.company,
            is_active=True
        )
        
        total_annual_overhead = sum([exp.annual_impact for exp in overhead_expenses])
        
        # Get fleet size for allocation
        from operations.models import Vehicle
        fleet_size = Vehicle.objects.filter(company=self.company, status='ACTIVE').count()
        
        if fleet_size > 0:
            level_4_per_vehicle = total_annual_overhead / Decimal(str(fleet_size))
        else:
            level_4_per_vehicle = Decimal('0.00')
        
        # Total annual cost per vehicle
        total_annual_cost = level_1_annual + level_4_per_vehicle
        
        # Calculate available hours with utilization rate
        working_days = self.company.working_days_per_year
        hours_per_day = self.company.working_hours_per_day
        utilization = self.company.utilization_rate
        
        effective_hours = Decimal(str(working_days)) * Decimal(str(hours_per_day)) * utilization
        
        if effective_hours <= 0:
            return Decimal('0.00')
        
        hourly_rate = total_annual_cost / effective_hours
        return hourly_rate.quantize(Decimal('0.01'))
    
    def calculate_km_rate(self, current_fuel_price=None):
        """
        Calculate cost per kilometer (Level 2: Variable Costs)
        
        Formula:
            KM Rate = Fuel Cost/km + Tire Cost/km + Maintenance Cost/km
        
        Args:
            current_fuel_price: Current fuel price (€/L), optional
        
        Returns:
            Decimal: Cost per kilometer in €/km
        """
        # Fuel cost per km
        if self.vehicle.average_fuel_consumption:
            consumption_per_km = self.vehicle.average_fuel_consumption / Decimal('100')
        else:
            # Default: 25L/100km
            consumption_per_km = Decimal('25.0') / Decimal('100')
        
        if current_fuel_price is None:
            # Get latest fuel price from FuelEntry
            from operations.models import FuelEntry
            latest_fuel = FuelEntry.objects.filter(
                vehicle=self.vehicle
            ).order_by('-date').first()
            
            current_fuel_price = latest_fuel.cost_per_liter if latest_fuel else self.DEFAULT_FUEL_PRICE
        
        fuel_cost_per_km = consumption_per_km * current_fuel_price
        
        # Tire cost per km
        tire_cost_per_km = self.vehicle.average_tire_cost_per_km or self.DEFAULT_TIRE_COST_PER_KM
        
        # Maintenance cost per km
        maintenance_cost_per_km = self.DEFAULT_MAINTENANCE_PER_KM
        
        km_rate = fuel_cost_per_km + tire_cost_per_km + maintenance_cost_per_km
        return km_rate.quantize(Decimal('0.01'))
    
    def estimate_trip_cost(self, distance_km, duration_hours, tolls=Decimal('0.00'), ferries=Decimal('0.00')):
        """
        Estimate total trip cost
        
        Formula:
            Total = (Hours × Hourly_Rate) + (Distance × KM_Rate) + Tolls + Ferries
        
        Args:
            distance_km: Trip distance
            duration_hours: Trip duration
            tolls: Toll costs
            ferries: Ferry costs
        
        Returns:
            dict: Detailed cost breakdown
        """
        distance = Decimal(str(distance_km))
        hours = Decimal(str(duration_hours))
        tolls = Decimal(str(tolls))
        ferries = Decimal(str(ferries))
        
        hourly_rate = self.calculate_hourly_rate()
        km_rate = self.calculate_km_rate()
        
        time_based_cost = hours * hourly_rate
        distance_based_cost = distance * km_rate
        total_cost = time_based_cost + distance_based_cost + tolls + ferries
        
        return {
            'hourly_rate': hourly_rate.quantize(Decimal('0.01')),
            'km_rate': km_rate.quantize(Decimal('0.01')),
            'time_based_cost': time_based_cost.quantize(Decimal('0.01')),
            'distance_based_cost': distance_based_cost.quantize(Decimal('0.01')),
            'tolls': tolls.quantize(Decimal('0.01')),
            'ferries': ferries.quantize(Decimal('0.01')),
            'total_cost': total_cost.quantize(Decimal('0.01')),
        }
    
    def calculate_suggested_price(self, distance_km, duration_hours, tolls=Decimal('0.00'), 
                                  ferries=Decimal('0.00'), margin_percentage=Decimal('15.00'), 
                                  empty_return_factor=Decimal('1.0')):
        """
        Calculate suggested selling price with margin and risk factors
        
        Args:
            distance_km: Trip distance
            duration_hours: Trip duration
            tolls: Toll costs
            ferries: Ferry costs
            margin_percentage: Desired profit margin (default 15%)
            empty_return_factor: Risk factor for empty return (1.0 = no return, 0.5 = 50% return load)
        
        Returns:
            dict: Suggested price with breakdown
        """
        # Get base cost
        cost_breakdown = self.estimate_trip_cost(distance_km, duration_hours, tolls, ferries)
        base_cost = cost_breakdown['total_cost']
        
        # Apply empty return factor (if vehicle returns empty, double the distance cost)
        adjusted_distance_cost = cost_breakdown['distance_based_cost'] * empty_return_factor
        adjusted_total_cost = (
            cost_breakdown['time_based_cost'] + 
            adjusted_distance_cost + 
            cost_breakdown['tolls'] + 
            cost_breakdown['ferries']
        )
        
        # Apply margin
        margin_multiplier = Decimal('1') + (margin_percentage / Decimal('100'))
        suggested_price = adjusted_total_cost * margin_multiplier
        
        return {
            'base_cost': base_cost.quantize(Decimal('0.01')),
            'adjusted_cost': adjusted_total_cost.quantize(Decimal('0.01')),
            'margin_percentage': margin_percentage,
            'empty_return_factor': empty_return_factor,
            'suggested_price': suggested_price.quantize(Decimal('0.01')),
            'breakdown': cost_breakdown,
        }
