"""
Tenant Context Manager
Safe context management for background tasks and management commands
"""
from contextlib import contextmanager
from .mixins import set_current_company


@contextmanager
def tenant_context(company):
    """
    Context manager for safely setting tenant context
    
    Ensures proper cleanup even if exceptions occur.
    Use this in management commands and background tasks.
    
    Args:
        company: Company instance to set as current context
    
    Usage:
        from core.tenant_context import tenant_context
        
        with tenant_context(my_company):
            # All queries here are scoped to my_company
            expenses = CompanyExpense.objects.all()
        
        # Context is automatically cleared here
    
    Example (Management Command):
        class Command(BaseCommand):
            def handle(self, *args, **options):
                company = Company.objects.get(id=1)
                
                with tenant_context(company):
                    # Process company-specific data
                    process_expenses()
    """
    # Set company context
    set_current_company(company)
    
    try:
        # Yield control to the with block
        yield
    finally:
        # Always cleanup, even if exception occurs
        set_current_company(None)
