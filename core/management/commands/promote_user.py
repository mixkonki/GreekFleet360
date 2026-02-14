"""
Management command to promote a user to Company Admin
Sets is_staff=True, REMOVES superuser status, and assigns full edit permissions
"""
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType


class Command(BaseCommand):
    help = 'Promote a user to Company Admin (Staff + Full Edit Permissions, NO Superuser)'

    def add_arguments(self, parser):
        parser.add_argument(
            'username',
            type=str,
            help='Username of the user to promote'
        )

    def handle(self, *args, **options):
        username = options['username']
        
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise CommandError(f'User "{username}" does not exist')
        
        # STRICT RBAC: Remove superuser status
        if user.is_superuser:
            user.is_superuser = False
            user.save()
            self.stdout.write(
                self.style.WARNING(f'⚠ Removed superuser status from "{username}" (enforcing RBAC)')
            )
        
        # Set staff status
        if not user.is_staff:
            user.is_staff = True
            user.save()
            self.stdout.write(
                self.style.SUCCESS(f'✓ Set is_staff=True for user "{username}"')
            )
        else:
            self.stdout.write(
                self.style.WARNING(f'User "{username}" is already a staff member')
            )
        
        # Create or get "Company Admin" group
        group, created = Group.objects.get_or_create(name='Company Admin')
        
        if created:
            self.stdout.write(self.style.SUCCESS('✓ Created "Company Admin" group'))
            
            # Define tenant-scoped models that need full permissions
            tenant_models = [
                ('core', 'employee'),
                ('core', 'driverprofile'),
                ('core', 'vehicleasset'),  # Old vehicle model (polymorphic)
                ('operations', 'fuelentry'),
                ('operations', 'servicelog'),
                ('operations', 'incidentreport'),
                ('operations', 'vehicle'),  # New vehicle model (accounting)
                ('finance', 'costcenter'),
                ('finance', 'companyexpense'),
                ('finance', 'transportorder'),
            ]
            
            # Add permissions to group
            permissions_added = 0
            for app_label, model_name in tenant_models:
                try:
                    content_type = ContentType.objects.get(
                        app_label=app_label,
                        model=model_name
                    )
                    
                    # Get all permissions for this model (add, change, delete, view)
                    perms = Permission.objects.filter(content_type=content_type)
                    for perm in perms:
                        group.permissions.add(perm)
                        permissions_added += 1
                        self.stdout.write(f'  + {perm.codename}')
                except ContentType.DoesNotExist:
                    self.stdout.write(
                        self.style.WARNING(f'  ⚠ Model {app_label}.{model_name} not found')
                    )
            
            self.stdout.write(
                self.style.SUCCESS(f'✓ Added {permissions_added} permissions to group')
            )
        else:
            self.stdout.write(self.style.SUCCESS('✓ "Company Admin" group already exists'))
        
        # Add user to group
        if group not in user.groups.all():
            user.groups.add(group)
            self.stdout.write(
                self.style.SUCCESS(f'✓ Added user "{username}" to "Company Admin" group')
            )
        else:
            self.stdout.write(
                self.style.WARNING(f'User "{username}" is already in "Company Admin" group')
            )
        
        # Final summary
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write(self.style.SUCCESS(f'User "{username}" is now a Company Admin!'))
        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write(f'  Status: is_staff=True, is_superuser=False (RBAC enforced)')
        self.stdout.write(f'  Group: Company Admin')
        self.stdout.write(f'  Access URL: http://localhost:8000/admin/')
        self.stdout.write(f'  Permissions: Full CRUD on 10 tenant-scoped models')
        self.stdout.write(f'  Data Scope: Only their assigned company')
        self.stdout.write(f'  Vehicle Models: Both VehicleAsset (old) and Vehicle (new)')
        self.stdout.write('')
