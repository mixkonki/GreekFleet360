"""
Web Views for GreekFleet 360
Frontend Interface with HTMX and Leaflet
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Avg, Count, Q
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal

from core.models import VehicleAsset, Company
from finance.models import TransportOrder, CompanyExpense, CostCenter
from finance.services import CostCalculator
from operations.models import FuelEntry, ServiceLog
from .forms import CompanyExpenseForm, CostCenterForm, TransportOrderForm, FuelEntryForm


@login_required
def dashboard_home(request):
    """
    Dashboard with KPI Cards
    """
    # Get company from logged-in user's profile
    try:
        company = request.user.profile.company
    except:
        company = Company.objects.first()  # Fallback for development
    
    if not company:
        context = {
            'monthly_revenue': 0,
            'fleet_profit_margin': 0,
            'active_vehicles': 0,
            'upcoming_maintenance': 0,
        }
        return render(request, 'dashboard.html', context)
    
    # Calculate current month date range
    now = timezone.now()
    first_day_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    # KPI 1: Monthly Revenue
    monthly_orders = TransportOrder.objects.filter(
        company=company,
        date__gte=first_day_of_month,
        status__in=['COMPLETED', 'INVOICED']
    )
    monthly_revenue = monthly_orders.aggregate(total=Sum('agreed_price'))['total'] or Decimal('0.00')
    
    # KPI 2: Fleet Profit Margin (Average)
    profit_margins = []
    for order in monthly_orders.filter(assigned_vehicle__isnull=False, duration_hours__isnull=False):
        try:
            calculator = CostCalculator(
                vehicle=order.assigned_vehicle,
                distance_km=order.distance_km,
                duration_hours=order.duration_hours,
                tolls_cost=order.tolls_cost,
                ferry_cost=order.ferry_cost
            )
            result = calculator.calculate_trip_profitability(order.agreed_price)
            profit_margins.append(float(result['profit_margin']))
        except:
            pass
    
    fleet_profit_margin = sum(profit_margins) / len(profit_margins) if profit_margins else 0
    
    # KPI 3: Active Vehicles
    active_vehicles = VehicleAsset.objects.filter(company=company, status='ACTIVE').count()
    
    # KPI 4: Upcoming Maintenance (vehicles due for service in next 30 days or 1000 km)
    # Simplified logic: vehicles with odometer > 10000 km since last service
    upcoming_maintenance = 0
    for vehicle in VehicleAsset.objects.filter(company=company, status='ACTIVE'):
        last_service = ServiceLog.objects.filter(
            vehicle=vehicle,
            service_type='REGULAR'
        ).order_by('-date').first()
        
        if last_service:
            km_since_service = vehicle.current_odometer - last_service.odometer_reading
            if km_since_service > 9000:  # Due soon (within 1000 km of 10k interval)
                upcoming_maintenance += 1
        elif vehicle.current_odometer > 9000:
            upcoming_maintenance += 1
    
    context = {
        'monthly_revenue': monthly_revenue,
        'fleet_profit_margin': round(fleet_profit_margin, 2),
        'active_vehicles': active_vehicles,
        'upcoming_maintenance': upcoming_maintenance,
        'company': company,
    }
    
    return render(request, 'dashboard.html', context)


@login_required
def vehicle_list(request):
    """
    Vehicle List with HTMX Pagination and Search
    """
    # Get company from logged-in user's profile
    try:
        company = request.user.profile.company
    except:
        company = Company.objects.first()  # Fallback for development
    
    # Get page number and search query from request
    page = int(request.GET.get('page', 1))
    search_query = request.GET.get('search', '').strip()
    per_page = 12
    offset = (page - 1) * per_page
    
    # Base queryset
    vehicles_qs = VehicleAsset.objects.filter(company=company).select_related('company')
    
    # Apply search filter
    if search_query:
        vehicles_qs = vehicles_qs.filter(
            Q(plate__icontains=search_query) |
            Q(make__icontains=search_query) |
            Q(model__icontains=search_query) |
            Q(vin__icontains=search_query)
        )
    
    vehicles = vehicles_qs[offset:offset + per_page]
    
    # Calculate health status for each vehicle
    vehicles_with_health = []
    for vehicle in vehicles:
        # Calculate days until next KTEO
        days_until_kteo = (vehicle.kteo_expiry - timezone.now().date()).days if vehicle.kteo_expiry else 0
        
        # Calculate days until insurance expiry
        days_until_insurance = (vehicle.insurance_expiry - timezone.now().date()).days if vehicle.insurance_expiry else 0
        
        # Health score (0-100)
        health_score = 100
        if days_until_kteo < 30:
            health_score -= 30
        if days_until_insurance < 30:
            health_score -= 30
        
        # Check last service
        last_service = ServiceLog.objects.filter(vehicle=vehicle).order_by('-date').first()
        if last_service:
            km_since_service = vehicle.current_odometer - last_service.odometer_reading
            if km_since_service > 10000:
                health_score -= 40
        
        health_score = max(0, health_score)
        
        vehicles_with_health.append({
            'vehicle': vehicle,
            'health_score': health_score,
            'days_until_kteo': days_until_kteo,
            'days_until_insurance': days_until_insurance,
        })
    
    # Check if there are more pages
    total_vehicles = vehicles_qs.count()
    has_more = offset + per_page < total_vehicles
    
    context = {
        'vehicles_with_health': vehicles_with_health,
        'page': page,
        'has_more': has_more,
    }
    
    # If HTMX request, return partial template
    if request.headers.get('HX-Request'):
        return render(request, 'partials/vehicle_cards.html', context)
    
    return render(request, 'vehicle_list.html', context)


@login_required
def order_list(request):
    """
    Transport Order List
    """
    # Get company from logged-in user's profile
    try:
        company = request.user.profile.company
    except:
        company = Company.objects.first()  # Fallback for development
    orders = TransportOrder.objects.filter(company=company).select_related(
        'assigned_vehicle', 'assigned_driver'
    ).order_by('-date')[:50]
    
    context = {
        'orders': orders,
    }
    
    return render(request, 'order_list.html', context)


@login_required
def order_detail(request, order_id):
    """
    Transport Order Detail with Leaflet Map
    """
    order = get_object_or_404(TransportOrder, id=order_id)
    
    # Calculate profitability if vehicle and duration are set
    profitability = None
    if order.assigned_vehicle and order.duration_hours:
        try:
            calculator = CostCalculator(
                vehicle=order.assigned_vehicle,
                distance_km=order.distance_km,
                duration_hours=order.duration_hours,
                tolls_cost=order.tolls_cost,
                ferry_cost=order.ferry_cost
            )
            profitability = calculator.calculate_trip_profitability(order.agreed_price)
        except Exception as e:
            profitability = {'error': str(e)}
    
    context = {
        'order': order,
        'profitability': profitability,
    }
    
    return render(request, 'order_detail.html', context)


@login_required
def finance_settings(request):
    """
    Financial Settings Page
    Configure Recurring Expenses and Vehicle Cost Profiles
    """
    # Get company from logged-in user's profile
    try:
        company = request.user.profile.company
    except:
        company = Company.objects.first()  # Fallback for development
    
    if not company:
        return redirect('/admin/core/company/add/')
    
    # Get all company expenses
    expenses = CompanyExpense.objects.filter(
        company=company,
        is_active=True
    ).select_related('category', 'category__family', 'cost_center').order_by('category__family__display_order', 'start_date')
    
    # Get all cost centers with allocated costs
    cost_centers_qs = CostCenter.objects.filter(company=company, is_active=True).order_by('name')
    active_center_count = cost_centers_qs.count()
    
    # Calculate allocated costs per cost center
    cost_centers_with_allocation = []
    for center in cost_centers_qs:
        direct_cost = Decimal('0.00')
        allocated_cost = Decimal('0.00')
        
        for exp in expenses:
            if exp.distribute_to_all_centers and active_center_count > 0:
                # Distribute equally across all active centers
                allocated_cost += exp.monthly_impact / Decimal(str(active_center_count))
            elif exp.cost_center and exp.cost_center.id == center.id:
                # Direct assignment to this center
                direct_cost += exp.monthly_impact
        
        cost_centers_with_allocation.append({
            'center': center,
            'direct_cost': direct_cost,
            'allocated_cost': allocated_cost,
            'total_cost': direct_cost + allocated_cost
        })
    
    cost_centers = cost_centers_with_allocation
    
    # Calculate totals using the new property methods
    total_annual = sum([exp.annual_impact for exp in expenses])
    
    # Get fleet size
    fleet_size = company.vehicles.filter(status='ACTIVE').count()
    
    # Calculate hourly rate: total_annual / (365 * 24) / max(fleet_size, 1)
    hours_per_year = 365 * 24
    hourly_rate = total_annual / Decimal(str(hours_per_year)) / Decimal(str(max(fleet_size, 1)))
    
    # Calculate monthly breakdown for current year
    from datetime import date
    current_year = timezone.now().year
    monthly_breakdown = []
    
    for month in range(1, 13):
        # Get first and last day of month
        if month == 12:
            start_of_month = date(current_year, month, 1)
            end_of_month = date(current_year + 1, 1, 1) - timedelta(days=1)
        else:
            start_of_month = date(current_year, month, 1)
            end_of_month = date(current_year, month + 1, 1) - timedelta(days=1)
        
        month_cost = Decimal('0.00')
        
        for exp in expenses:
            # Check if expense is active during this month
            is_active_in_month = (
                exp.start_date <= end_of_month and
                (exp.end_date is None or exp.end_date >= start_of_month)
            )
            
            if is_active_in_month:
                if exp.expense_type == 'ONE_OFF':
                    # One-off expenses only count in their start month
                    if exp.start_date.year == current_year and exp.start_date.month == month:
                        month_cost += exp.amount
                else:
                    # Recurring expenses use monthly_impact
                    month_cost += exp.monthly_impact
        
        monthly_breakdown.append({
            'month': month,
            'month_name': date(current_year, month, 1).strftime('%B'),
            'cost': month_cost
        })
    
    # Calculate average monthly cost
    total_monthly = sum([m['cost'] for m in monthly_breakdown]) / Decimal('12.0')
    
    # Get all vehicles for cost profile table
    vehicles = VehicleAsset.objects.filter(company=company).select_related('company')
    
    context = {
        'expenses': expenses,
        'cost_centers': cost_centers,
        'total_annual': total_annual,
        'total_monthly': total_monthly,
        'monthly_breakdown': monthly_breakdown,
        'hourly_rate': hourly_rate,
        'fleet_size': fleet_size,
        'vehicles': vehicles,
        'company': company,
    }
    
    return render(request, 'finance_settings.html', context)


@login_required
def order_create(request):
    """
    Create new Transport Order
    """
    # Get company from logged-in user's profile
    try:
        company = request.user.profile.company
    except:
        company = Company.objects.first()  # Fallback for development
    
    if request.method == 'POST':
        form = TransportOrderForm(request.POST)
        if form.is_valid():
            form.save()
            from django.shortcuts import redirect
            return redirect('web:order_list')
    else:
        form = TransportOrderForm(initial={'company': company, 'date': datetime.now().date()})
    
    context = {
        'form': form,
        'title': 'Νέα Εντολή Μεταφοράς',
    }
    
    return render(request, 'order_form.html', context)


@login_required
def fuel_create(request):
    """
    Create new Fuel Entry
    """
    # Get company from logged-in user's profile
    try:
        company = request.user.profile.company
    except:
        company = Company.objects.first()  # Fallback for development
    
    if request.method == 'POST':
        form = FuelEntryForm(request.POST)
        if form.is_valid():
            fuel_entry = form.save(commit=False)
            # Auto-calculate total_cost if not provided
            if not fuel_entry.total_cost:
                fuel_entry.total_cost = fuel_entry.liters * fuel_entry.cost_per_liter
            fuel_entry.save()
            from django.shortcuts import redirect
            return redirect('web:dashboard')
    else:
        form = FuelEntryForm(initial={'company': company, 'date': datetime.now().date()})
    
    context = {
        'form': form,
        'title': 'Καταχώρηση Καυσίμου',
    }
    
    return render(request, 'fuel_form.html', context)


@login_required
def expense_form(request):
    """
    Return Expense Form Modal (HTMX)
    """
    try:
        company = request.user.profile.company
    except:
        company = Company.objects.first()
    
    # Check if editing existing expense
    expense_id = request.GET.get('id')
    if expense_id:
        expense = get_object_or_404(CompanyExpense, id=expense_id, company=company)
        form = CompanyExpenseForm(instance=expense, company=company)
        title = 'Επεξεργασία Εξόδου'
    else:
        form = CompanyExpenseForm(company=company)
        title = 'Προσθήκη Εξόδου'
    
    context = {
        'form': form,
        'title': title,
    }
    
    return render(request, 'partials/expense_form_modal.html', context)


@login_required
def expense_create(request):
    """
    Create/Update Recurring Expense (HTMX Modal POST)
    """
    try:
        company = request.user.profile.company
    except:
        company = Company.objects.first()
    
    if request.method == 'POST':
        # Check if updating existing expense
        expense_id = request.POST.get('expense_id')
        if expense_id:
            expense = get_object_or_404(CompanyExpense, id=expense_id, company=company)
            form = CompanyExpenseForm(request.POST, instance=expense, company=company)
        else:
            form = CompanyExpenseForm(request.POST, company=company)
        
        if form.is_valid():
            expense = form.save(commit=False)
            expense.company = company
            expense.is_active = True
            expense.save()
            
            # Return updated expenses list
            return redirect('web:finance_settings')
        else:
            # Log form errors for debugging
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Form validation failed: {form.errors}")
            print(f"FORM ERRORS: {form.errors}")  # Console output for immediate debugging
            
            # Return to form with errors
            context = {
                'form': form,
                'title': 'Επεξεργασία Εξόδου' if expense_id else 'Προσθήκη Εξόδου',
            }
            return render(request, 'partials/expense_form_modal.html', context)
    
    return redirect('web:finance_settings')


@login_required
def expense_delete(request, expense_id):
    """
    Delete Recurring Expense (HTMX)
    """
    from django.http import HttpResponse
    
    try:
        company = request.user.profile.company
    except:
        company = Company.objects.first()
    
    expense = get_object_or_404(CompanyExpense, id=expense_id, company=company)
    expense.delete()
    
    # Return empty response for HTMX to remove the row
    return HttpResponse('', status=200)


@login_required
def cost_center_form(request):
    """
    Return Cost Center Form Modal (HTMX)
    """
    try:
        company = request.user.profile.company
    except:
        company = Company.objects.first()
    
    form = CostCenterForm()
    
    context = {
        'form': form,
        'title': 'Νέο Κέντρο Κόστους',
    }
    
    return render(request, 'partials/cost_center_form_modal.html', context)


@login_required
def cost_center_create(request):
    """
    Create new Cost Center (HTMX Modal POST)
    """
    from django.db import IntegrityError
    from django.contrib import messages
    
    try:
        company = request.user.profile.company
    except:
        company = Company.objects.first()
    
    if request.method == 'POST':
        form = CostCenterForm(request.POST)
        if form.is_valid():
            cost_center = form.save(commit=False)
            cost_center.company = company
            cost_center.is_active = True
            
            try:
                cost_center.save()
                messages.success(request, 'Το Κέντρο Κόστους δημιουργήθηκε επιτυχώς!')
            except IntegrityError:
                messages.error(request, f'Το Κέντρο Κόστους "{cost_center.name}" υπάρχει ήδη για αυτή την εταιρεία.')
            
            return redirect('web:finance_settings')
    
    return redirect('web:finance_settings')


@login_required
def cost_center_edit(request, cost_center_id):
    """
    Return Cost Center Edit Form Modal (HTMX)
    """
    try:
        company = request.user.profile.company
    except:
        company = Company.objects.first()
    
    cost_center = get_object_or_404(CostCenter, id=cost_center_id, company=company)
    form = CostCenterForm(instance=cost_center)
    
    context = {
        'form': form,
        'title': 'Επεξεργασία Κέντρου Κόστους',
        'cost_center_id': cost_center_id,
    }
    
    return render(request, 'partials/cost_center_form_modal.html', context)


@login_required
def cost_center_update(request, cost_center_id):
    """
    Update Cost Center (HTMX Modal POST)
    """
    from django.db import IntegrityError
    from django.contrib import messages
    
    try:
        company = request.user.profile.company
    except:
        company = Company.objects.first()
    
    cost_center = get_object_or_404(CostCenter, id=cost_center_id, company=company)
    
    if request.method == 'POST':
        form = CostCenterForm(request.POST, instance=cost_center)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, 'Το Κέντρο Κόστους ενημερώθηκε επιτυχώς!')
            except IntegrityError:
                messages.error(request, f'Το Κέντρο Κόστους "{cost_center.name}" υπάρχει ήδη για αυτή την εταιρεία.')
            
            return redirect('web:finance_settings')
    
    return redirect('web:finance_settings')


@login_required
def cost_center_delete(request, cost_center_id):
    """
    Delete Cost Center (HTMX)
    """
    from django.http import HttpResponse
    
    try:
        company = request.user.profile.company
    except:
        company = Company.objects.first()
    
    cost_center = get_object_or_404(CostCenter, id=cost_center_id, company=company)
    cost_center.delete()
    
    # Return empty response for HTMX to remove the row
    return HttpResponse('', status=200)
