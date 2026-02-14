"""
Management command to promote a user to staff status
Allows access to Django Admin panel with tenant isolation
"""
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = 'Promote a user to staff status (grants Admin panel access)'

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
            return
        
        # Promote to staff
        user.is_staff = True
        user.save()
        
        self.stdout.write(
            self.style.SUCCESS(
                f'✓ User "{username}" is now Staff and can access the Admin panel.\n'
                f'  Access URL: http://localhost:8000/admin/\n'
                f'  Note: User will only see data from their assigned company.'
            )
        )
