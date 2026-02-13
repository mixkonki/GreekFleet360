"""
Management command to seed default ExpenseCategory and CostCenter data
for all companies that don't have them yet.
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from core.models import Company
from finance.models import ExpenseCategory, CostCenter


class Command(BaseCommand):
    help = 'Seeds default ExpenseCategory and CostCenter for all companies'

    def handle(self, *args, **options):
        companies = Company.objects.all()
        
        if not companies.exists():
            self.stdout.write(self.style.WARNING('No companies found in database.'))
            return
        
        # Default expense categories
        default_categories = [
            {'name': 'Ενοίκια Κτιρίων', 'description': 'Ενοίκια γραφείων και εγκαταστάσεων'},
            {'name': 'ΔΕΚΟ / Ενέργεια', 'description': 'Ηλεκτρικό ρεύμα, νερό, φυσικό αέριο'},
            {'name': 'Τηλεπικοινωνίες', 'description': 'Internet, τηλέφωνα, κινητή τηλεφωνία'},
            {'name': 'Αμοιβές Τρίτων', 'description': 'Λογιστής, δικηγόρος, σύμβουλοι'},
            {'name': 'Φόροι & Τέλη', 'description': 'Φόροι εταιρείας, τέλη κυκλοφορίας'},
            {'name': 'Ασφάλιστρα', 'description': 'Ασφάλειες εγκαταστάσεων και εξοπλισμού'},
        ]
        
        # Default cost centers
        default_cost_centers = [
            {'name': 'Κεντρικά Γραφεία', 'description': 'Διοικητικά γραφεία - HQ'},
            {'name': 'Εγκαταστάσεις / Parking', 'description': 'Χώροι στάθμευσης και συντήρησης'},
        ]
        
        total_categories_created = 0
        total_cost_centers_created = 0
        
        with transaction.atomic():
            # First, create system-wide ExpenseCategories (they don't belong to a company)
            self.stdout.write('\nChecking system-wide expense categories...')
            existing_system_categories = ExpenseCategory.objects.filter(is_system_default=True).count()
            
            if existing_system_categories == 0:
                self.stdout.write('  Creating default expense categories...')
                for cat_data in default_categories:
                    ExpenseCategory.objects.create(
                        name=cat_data['name'],
                        description=cat_data['description'],
                        is_system_default=True
                    )
                    total_categories_created += 1
                self.stdout.write(self.style.SUCCESS(f'  ✓ Created {len(default_categories)} system expense categories'))
            else:
                self.stdout.write(f'  ✓ Already has {existing_system_categories} system expense categories')
            
            # Now create CostCenters for each company
            for company in companies:
                self.stdout.write(f'\nProcessing company: {company.name}')
                
                # Check and create CostCenters
                existing_cost_centers = CostCenter.objects.filter(company=company).count()
                
                if existing_cost_centers == 0:
                    self.stdout.write(f'  Creating default cost centers...')
                    for cc_data in default_cost_centers:
                        CostCenter.objects.create(
                            company=company,
                            name=cc_data['name'],
                            description=cc_data['description'],
                            is_active=True
                        )
                        total_cost_centers_created += 1
                    self.stdout.write(self.style.SUCCESS(f'  ✓ Created {len(default_cost_centers)} cost centers'))
                else:
                    self.stdout.write(f'  ✓ Already has {existing_cost_centers} cost centers')
        
        # Summary
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS(f'✓ Seeding completed successfully!'))
        self.stdout.write(f'  Companies processed: {companies.count()}')
        self.stdout.write(f'  Expense categories created: {total_categories_created}')
        self.stdout.write(f'  Cost centers created: {total_cost_centers_created}')
        self.stdout.write('='*60 + '\n')
