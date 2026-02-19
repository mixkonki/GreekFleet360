"""
Management Command: Calculate Costs
Runs the Cost Engine for a specified period and saves results to database
"""
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from core.models import Company
from finance.services.cost_engine import calculate_company_costs
from finance.services.cost_engine.persist import CostEnginePersistence


class Command(BaseCommand):
    help = 'Calculate costs for a specified period and save to database'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--company',
            type=str,
            help='Company name or ID to calculate costs for (required)',
            required=True
        )
        
        parser.add_argument(
            '--period',
            type=str,
            help='Period in format YYYY-MM (e.g., 2026-01) or "current" for current month',
            default='current'
        )
        
        parser.add_argument(
            '--basis',
            type=str,
            choices=['KM', 'HOUR', 'TRIP', 'REVENUE'],
            help='Basis unit for cost allocation (default: KM)',
            default='KM'
        )
        
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Run calculations without saving to database'
        )
    
    def handle(self, *args, **options):
        company_identifier = options['company']
        period_str = options['period']
        basis_unit = options['basis']
        dry_run = options['dry_run']
        
        # Get company
        try:
            # Try to get by ID first
            if company_identifier.isdigit():
                company = Company.objects.get(id=int(company_identifier))
            else:
                # Try to get by name
                company = Company.objects.get(name__iexact=company_identifier)
        except Company.DoesNotExist:
            raise CommandError(f'Company "{company_identifier}" not found')
        
        self.stdout.write(self.style.SUCCESS(f'Company: {company.name}'))
        
        # Parse period
        if period_str.lower() == 'current':
            today = date.today()
            period_start = date(today.year, today.month, 1)
        else:
            try:
                period_date = datetime.strptime(period_str, '%Y-%m')
                period_start = date(period_date.year, period_date.month, 1)
            except ValueError:
                raise CommandError(
                    'Invalid period format. Use YYYY-MM (e.g., 2026-01) or "current"'
                )
        
        # Calculate period end (last day of month)
        period_end = period_start + relativedelta(months=1) - relativedelta(days=1)
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Period: {period_start.strftime("%Y-%m-%d")} to {period_end.strftime("%Y-%m-%d")}'
            )
        )
        self.stdout.write(self.style.SUCCESS(f'Basis Unit: {basis_unit}'))
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No data will be saved'))
        
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Starting Cost Engine Calculation...')
        self.stdout.write('='*60 + '\n')
        
        # Initialize calculator
        calculator = CostEngineCalculator(company, period_start, period_end)
        
        # Run calculations
        try:
            # Step 1: Calculate cost center rates
            self.stdout.write('Step 1: Calculating cost center rates...')
            cost_center_rates = calculator.calculate_cost_center_rates()
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'✓ Calculated rates for {len(cost_center_rates)} cost centers'
                )
            )
            
            # Display summary
            for cc_id, rates in cost_center_rates.items():
                self.stdout.write(
                    f'  - Cost Center ID {cc_id}: '
                    f'€{rates["total_cost"]:.2f} total cost, '
                    f'€{rates.get("rate_per_km", 0):.4f}/km'
                )
            
            # Step 2: Calculate order cost breakdowns
            self.stdout.write('\nStep 2: Calculating order cost breakdowns...')
            order_breakdowns = calculator.calculate_order_cost_breakdowns(
                cost_center_rates,
                basis_unit
            )
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'✓ Calculated breakdowns for {len(order_breakdowns)} orders'
                )
            )
            
            # Display summary
            total_revenue = sum(b['revenue'] for b in order_breakdowns.values())
            total_cost = sum(b['total_cost'] for b in order_breakdowns.values())
            total_profit = sum(b['profit'] for b in order_breakdowns.values())
            
            self.stdout.write(f'\n  Total Revenue: €{total_revenue:.2f}')
            self.stdout.write(f'  Total Cost: €{total_cost:.2f}')
            self.stdout.write(f'  Total Profit: €{total_profit:.2f}')
            
            if total_revenue > 0:
                avg_margin = (total_profit / total_revenue) * 100
                self.stdout.write(f'  Average Margin: {avg_margin:.2f}%')
            
            # Step 3: Save to database (if not dry run)
            if not dry_run:
                self.stdout.write('\nStep 3: Saving results to database...')
                
                persistence = CostEnginePersistence()
                
                # Save cost rate snapshots
                snapshots = persistence.save_cost_rate_snapshots(
                    company,
                    period_start,
                    period_end,
                    cost_center_rates
                )
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✓ Saved {len(snapshots)} cost rate snapshots'
                    )
                )
                
                # Save order cost breakdowns
                breakdowns = persistence.save_order_cost_breakdowns(
                    company,
                    period_start,
                    period_end,
                    order_breakdowns
                )
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✓ Saved {len(breakdowns)} order cost breakdowns'
                    )
                )
            
            self.stdout.write('\n' + '='*60)
            self.stdout.write(self.style.SUCCESS('✓ Cost Engine Calculation Complete!'))
            self.stdout.write('='*60)
            
        except Exception as e:
            self.stdout.write('\n' + '='*60)
            self.stdout.write(self.style.ERROR(f'✗ Error during calculation: {str(e)}'))
            self.stdout.write('='*60)
            raise CommandError(f'Calculation failed: {str(e)}')
