"""
Management command to promote a user to Company Admin
Sets is_staff=True and assigns full edit permissions for tenant-scoped models
"""
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType


class Command(BaseCommand):
    help = 'Promote a user to Company Admin (Staff + Full Edit Permissions)'

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
        
        # Check if already staff
        if user.is_staff:
            self.stdout.write(
                self.style.WARNING(f'User "{username}" is already a staff member')
            )
        else:
            # Promote to staff
            user.is_staff = True
            user.save()
            self.stdout.write(
                self.style.SUCCESS(f'✓ Set is_staff=True for user "{username}"')
            )
        
        # Create or get "Company Admin" group
        group, created = Group.objects.get_or_create(name='Company Admin')
        
        if created:
            self.stdout.write(self.style.SUCCESS('✓ Created "Company Admin" group'))
            
            # Define tenant-scoped models that need full permissions
            tenant_models = [
                ('core', 'employee'),
                ('core', 'driverprofile'),
                ('operations', 'fuelentry'),
                ('operations', 'servicelog'),
                ('operations', 'incidentreport'),
                ('operations', 'vehicle'),
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
                except ContentType.DoesNotExist:
                    self.stdout.write(
                        self.style.WARNING(f'  Model {app_label}.{model_name} not found')
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
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS(f'User "{username}" is now a Company Admin!'))
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(f'  Access URL: http://localhost:8000/admin/')
        self.stdout.write(f'  Permissions: Full CRUD on tenant-scoped models')
        self.stdout.write(f'  Data Scope: Only their assigned company')
        self.stdout.write('')
