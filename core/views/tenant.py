"""
Tenant-Safe View Mixins
Enforce multi-tenant isolation at the view layer
"""
from django.core.exceptions import PermissionDenied
from django.contrib.auth.mixins import LoginRequiredMixin


class TenantRequiredMixin(LoginRequiredMixin):
    """
    Mixin to ensure request has a valid company context
    
    Raises PermissionDenied (403) if request.company is not set.
    This prevents unauthenticated or company-less users from accessing tenant data.
    
    Usage:
        class MyView(TenantRequiredMixin, ListView):
            model = MyModel
    """
    
    def dispatch(self, request, *args, **kwargs):
        """
        Check that request has a company before processing
        """
        # First check if user is authenticated (via LoginRequiredMixin)
        response = super().dispatch(request, *args, **kwargs)
        
        # If we got a redirect (user not logged in), return it
        if response.status_code == 302:
            return response
        
        # Check if company is set
        if not hasattr(request, 'company') or request.company is None:
            raise PermissionDenied("No company context available. Please contact administrator.")
        
        return response


class TenantQuerysetMixin:
    """
    Mixin to automatically filter querysets by current company
    
    Uses the model's CompanyScopedManager (objects) which automatically
    filters by the current company from thread-local storage.
    
    For DetailView, this ensures 404 if user tries to access another company's record.
    
    Usage:
        class MyListView(TenantQuerysetMixin, ListView):
            model = MyModel
        
        class MyDetailView(TenantQuerysetMixin, DetailView):
            model = MyModel
    """
    
    def get_queryset(self):
        """
        Return queryset filtered by current company
        
        Uses model.objects which is CompanyScopedManager - automatically
        filters by company from thread-local storage set by middleware.
        
        Returns:
            QuerySet: Filtered by current company
        """
        return self.model.objects.all()


class TenantFormMixin:
    """
    Mixin to auto-assign company to new objects in forms
    
    Prevents users from manually setting company field.
    Automatically assigns request.company to new objects.
    
    Usage:
        class MyCreateView(TenantFormMixin, CreateView):
            model = MyModel
            fields = ['field1', 'field2']  # Don't include 'company'
    """
    
    def form_valid(self, form):
        """
        Auto-assign company to new objects
        
        Args:
            form: ModelForm instance
        
        Returns:
            HttpResponse: Result of super().form_valid()
        """
        # Auto-set company for new objects
        if not form.instance.pk and hasattr(self.request, 'company'):
            form.instance.company = self.request.company
        
        return super().form_valid(form)
