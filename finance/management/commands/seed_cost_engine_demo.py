"""
Management Command: Seed Cost Engine Demo Data
Creates repeatable demo dataset for Cost Engine testing
"""
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from decimal import Decimal
from datetime import date

from core.models import Company
from core.tenant_context import tenant_context
from operations.models import Vehicle
from finance.models import CostCenter, CostItem, CostPosting, TransportOrder
from finance.services.cost_engine.calculator import calculate_company_costs


class Command(BaseCommand):
    help = 'Seed demo data for Cost Engine testing'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--company-id',
            type=int,
            help='Company ID (default: first company)',
            default=None
        )
        parser.add_argument(
            '--period-start',
            type=str,
            help='Period start date YYYY-MM-DD (default: 2026-01-01)',
            default='2026-01-01'
        )
        parser.add_argument(
            '--period-end',
            type=str,
            help='Period end date YYYY-MM-DD (default: 2026-01-31)',
            default='2026-01-31'
        )
        parser.add_argument(
            '--vehicle-km',
            type=int,
            help='Vehicle kilometers for order (default: 500)',
            default=500
        )
        parser.add_argument(
            '--order-revenue',
            type=int,
            help='Order revenue (default: 2000)',
            default=2000
        )
        parser.add_argument(
            '--vehicle-cost',
            type=int,
            help='Vehicle cost posting amount (default: 1000)',
            default=1000
        )
        parser.add_argument(
            '--overhead-cost',
            type=int,
            help='Overhead cost posting amount (default: 300)',
            default=300
        )
    
    def handle(self, *args, **options):
        # Parse arguments
        company_id = options['company_id']
        period_start = date.fromisoformat(options['period_start'])
        period_end = date.fromisoformat(options['period_end'])
        vehicle_km = Decimal(str(options['vehicle_km']))
        order_revenue = Decimal(str(options['order_revenue']))
        vehicle_cost = Decimal(str(options['vehicle_cost']))
        overhead_cost = Decimal(str(options['overhead_cost']))
        
        # Get company
        if company_id:
            try:
                company = Company.objects.get(id=company_id)
            except Company.DoesNotExist:
                raise CommandError(f'Company with ID {company_id} not found')
        else:
            company = Company.objects.first()
            if not company:
                raise CommandError('No companies found in database')
        
        self.stdout.write(self.style.SUCCESS(f'Company: {company.name} (ID: {company.id})'))
        self.stdout.write(self.style.SUCCESS(f'Period: {period_start} to {period_end}'))
        
        # Create demo data inside tenant context
        with tenant_context(company):
            with transaction.atomic():
                # Step 1: Create or get Vehicle
                vehicle, created = Vehicle.objects.get_or_create(
                    company=company,
                    license_plate='DEMO-001',
                    defaults={
                        'make': 'Mercedes',
                        'model': 'Actros',
                        'vehicle_class': 'TRUCK',
                        'body_type': 'CURTAIN',
                        'fuel_type': 'DIESEL',
                        'manufacturing_year': 2020,
                        'purchase_value': Decimal('80000.00'),
                        'status': 'ACTIVE'
                    }
                )
                self.stdout.write(
                    self.style.SUCCESS(
                        f'{"Created" if created else "Found"} Vehicle: {vehicle.license_plate} (ID: {vehicle.id})'
                    )
                )
                
                # Step 2: Create CostCenter for Vehicle
                vehicle_cc, created = CostCenter.objects.get_or_create(
                    company=company,
                    name=f'CC-{vehicle.license_plate}',
                    defaults={
                        'type': 'VEHICLE',
                        'vehicle': vehicle,
                        'is_active': True
                    }
                )
                self.stdout.write(
                    self.style.SUCCESS(
                        f'{"Created" if created else "Found"} Vehicle Cost Center: {vehicle_cc.name} (ID: {vehicle_cc.id})'
                    )
                )
                
                # Step 3: Create CostCenter for Overhead
                overhead_cc, created = CostCenter.objects.get_or_create(
                    company=company,
                    name='Overhead-General',
                    defaults={
                        'type': 'OVERHEAD',
                        'is_active': True
                    }
                )
                self.stdout.write(
                    self.style.SUCCESS(
                        f'{"Created" if created else "Found"} Overhead Cost Center: {overhead_cc.name} (ID: {overhead_cc.id})'
                    )
                )
                
                # Step 4: Create CostItems
                vehicle_item, created = CostItem.objects.get_or_create(
                    company=company,
                    name='Vehicle Operating Cost',
                    defaults={
                        'category': 'FIXED',
                        'unit': 'MONTH',
                        'is_active': True
                    }
                )
                self.stdout.write(
                    self.style.SUCCESS(
                        f'{"Created" if created else "Found"} Vehicle CostItem (ID: {vehicle_item.id})'
                    )
                )
                
                overhead_item, created = CostItem.objects.get_or_create(
                    company=company,
                    name='General Overhead',
                    defaults={
                        'category': 'INDIRECT',
                        'unit': 'MONTH',
                        'is_active': True
                    }
                )
                self.stdout.write(
                    self.style.SUCCESS(
                        f'{"Created" if created else "Found"} Overhead CostItem (ID: {overhead_item.id})'
                    )
                )
                
                # Step 5: Create CostPostings
                # Delete existing postings for this period to avoid duplicates
                CostPosting.objects.filter(
                    company=company,
                    period_start=period_start,
                    period_end=period_end
                ).delete()
                
                vehicle_posting = CostPosting.objects.create(
                    company=company,
                    cost_center=vehicle_cc,
                    cost_item=vehicle_item,
                    amount=vehicle_cost,
                    period_start=period_start,
                    period_end=period_end,
                    notes='Demo vehicle cost posting'
                )
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Created Vehicle CostPosting: €{vehicle_cost} (ID: {vehicle_posting.id})'
                    )
                )
                
                overhead_posting = CostPosting.objects.create(
                    company=company,
                    cost_center=overhead_cc,
                    cost_item=overhead_item,
                    amount=overhead_cost,
                    period_start=period_start,
                    period_end=period_end,
                    notes='Demo overhead cost posting'
                )
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Created Overhead CostPosting: €{overhead_cost} (ID: {overhead_posting.id})'
                    )
                )
                
                # Step 6: Create TransportOrder
                # Delete existing demo orders to avoid duplicates
                TransportOrder.objects.filter(
                    company=company,
                    customer_name='Demo Customer'
                ).delete()
                
                order = TransportOrder.objects.create(
                    company=company,
                    customer_name='Demo Customer',
                    date=period_start,
                    origin='Athens',
                    destination='Thessaloniki',
                    distance_km=vehicle_km,
                    agreed_price=order_revenue,
                    assigned_vehicle=vehicle,
                    status='COMPLETED'
                )
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Created TransportOrder: {order.origin} → {order.destination}, '
                        f'{vehicle_km}km, €{order_revenue} (ID: {order.id})'
                    )
                )
                
                self.stdout.write('\n' + '='*60)
                self.stdout.write(self.style.SUCCESS('✓ Demo Data Seeded Successfully!'))
                self.stdout.write('='*60 + '\n')
                
                # Step 7: Run Cost Engine and display results
                self.stdout.write('Running Cost Engine calculation...\n')
                
                result = calculate_company_costs(company, period_start, period_end)
                
                # Display summary
                summary = result.get('summary', {})
                self.stdout.write(self.style.SUCCESS('SUMMARY:'))
                self.stdout.write(f'  Total Snapshots: {summary.get("total_snapshots", 0)}')
                self.stdout.write(f'  Total Breakdowns: {summary.get("total_breakdowns", 0)}')
                self.stdout.write(f'  Total Cost: €{summary.get("total_cost", 0):.2f}')
                self.stdout.write(f'  Total Revenue: €{summary.get("total_revenue", 0):.2f}')
                self.stdout.write(f'  Total Profit: €{summary.get("total_profit", 0):.2f}')
                self.stdout.write(f'  Average Margin: {summary.get("average_margin", 0):.2f}%\n')
                
                # Display sample snapshots
                snapshots = result.get('snapshots', [])
                self.stdout.write(self.style.SUCCESS('SAMPLE SNAPSHOTS:'))
                for snap in snapshots[:2]:
                    self.stdout.write(
                        f'  {snap.get("cost_center_name")} ({snap.get("cost_center_type")}): '
                        f'€{snap.get("rate", 0):.4f}/{snap.get("basis_unit")} '
                        f'[{snap.get("status")}]'
                    )
                
                # Display sample breakdowns
                breakdowns = result.get('breakdowns', [])
                if breakdowns:
                    self.stdout.write(self.style.SUCCESS('\nSAMPLE BREAKDOWN:'))
                    bd = breakdowns[0]
                    self.stdout.write(f'  Order ID: {bd.get("order_id")}')
                    self.stdout.write(f'  Total Cost: €{bd.get("total_cost", 0):.2f}')
                    self.stdout.write(f'  Revenue: €{bd.get("revenue", 0):.2f}')
                    self.stdout.write(f'  Profit: €{bd.get("profit", 0):.2f}')
                    self.stdout.write(f'  Margin: {bd.get("margin", 0):.2f}%')
                
                self.stdout.write('\n' + '='*60)
                self.stdout.write(
                    self.style.SUCCESS(
                        '✓ Access debug endpoint: http://127.0.0.1:8000/finance/debug/cost-engine/'
                    )
                )
                self.stdout.write('='*60)
