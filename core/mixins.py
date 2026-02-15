"""
Core Model Mixins for GreekFleet 360
Tenant Isolation and Scoped Querysets
"""
from django.db import models
import threading

# Thread-local storage for current company context
_thread_locals = threading.local()


def set_current_company(company):
    """
    Set the current company in thread-local storage
    
    Args:
        company: Company instance
    """
    _thread_locals.company = company


def get_current_company():
    """
    Get the current company from thread-local storage
    
    Returns:
        Company instance or None
    """
    return getattr(_thread_locals, 'company', None)


class CompanyScopedManager(models.Manager):
    """
    Custom Manager that automatically filters querysets by company
    
    This ensures tenant isolation at the ORM level.
    Only returns objects belonging to the current user's company.
    
    SAFE DEFAULT: Returns empty queryset if no company context
    (prevents accidental cross-tenant data exposure)
    """
    
    def get_queryset(self):
        """
        Override get_queryset to filter by current company
        
        Returns:
            QuerySet filtered by company, or empty queryset if no context
        """
        queryset = super().get_queryset()
        current_company = get_current_company()
        
        if current_company:
            # Filter by current company
            return queryset.filter(company=current_company)
        
        # SAFE DEFAULT: Return empty queryset if no company context
        # This prevents accidental data leakage in unauthenticated requests
        # Use Model.all_objects for admin/system access
        return queryset.none()


class CompanyScopedModel(models.Model):
    """
    Abstract base model for tenant-scoped models
    
    Automatically includes:
    - ForeignKey to Company
    - CompanyScopedManager for automatic filtering (objects)
    - Unfiltered manager for admin/system access (all_objects)
    - Metadata fields (created_at, updated_at)
    """
    
    company = models.ForeignKey(
        'core.Company',
        on_delete=models.CASCADE,
        related_name='%(class)s_set',
        verbose_name="Εταιρεία"
    )
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Δημιουργήθηκε")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Ενημερώθηκε")
    
    # Scoped manager (default) - auto-filters by company
    objects = CompanyScopedManager()
    
    # Unfiltered manager - for admin and system operations
    all_objects = models.Manager()
    
    class Meta:
        abstract = True
        ordering = ['-created_at']
