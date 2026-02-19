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


class CompanyScopedQuerySet(models.QuerySet):
    """
    Custom QuerySet that auto-assigns company on create operations
    
    Automatically sets company field when creating objects if:
    1. tenant_context is active (get_current_company() returns a company)
    2. company field is not explicitly provided
    """
    
    def create(self, **kwargs):
        """
        Override create to auto-assign company
        
        Args:
            **kwargs: Model field values
        
        Returns:
            Created model instance
        """
        current_company = get_current_company()
        
        # Auto-assign company if context is active and company not provided
        if current_company and 'company' not in kwargs:
            kwargs['company'] = current_company
        
        return super().create(**kwargs)
    
    def bulk_create(self, objs, **kwargs):
        """
        Override bulk_create to auto-assign company
        
        Args:
            objs: List of model instances
            **kwargs: Additional arguments
        
        Returns:
            List of created instances
        """
        current_company = get_current_company()
        
        # Auto-assign company to objects that don't have it set
        if current_company:
            for obj in objs:
                # Check if company_id is not set (safer than accessing company FK)
                if not obj.company_id:
                    obj.company = current_company
        
        return super().bulk_create(objs, **kwargs)
    
    def get_or_create(self, defaults=None, **kwargs):
        """
        Override get_or_create to auto-assign company
        
        Args:
            defaults: Default values for create
            **kwargs: Lookup parameters
        
        Returns:
            Tuple of (object, created)
        """
        current_company = get_current_company()
        
        # Auto-assign company if context is active and company not in lookup
        if current_company and 'company' not in kwargs:
            kwargs['company'] = current_company
        
        return super().get_or_create(defaults=defaults, **kwargs)
    
    def update_or_create(self, defaults=None, **kwargs):
        """
        Override update_or_create to auto-assign company
        
        Args:
            defaults: Default values for create/update
            **kwargs: Lookup parameters
        
        Returns:
            Tuple of (object, created)
        """
        current_company = get_current_company()
        
        # Auto-assign company if context is active and company not in lookup
        if current_company and 'company' not in kwargs:
            kwargs['company'] = current_company
        
        return super().update_or_create(defaults=defaults, **kwargs)


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
            CompanyScopedQuerySet filtered by company, or empty queryset if no context
        """
        queryset = CompanyScopedQuerySet(self.model, using=self._db)
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
