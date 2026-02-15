"""
Core Middleware for GreekFleet 360
Tenant Isolation and Request Context
"""
from django.utils.deprecation import MiddlewareMixin
from .mixins import set_current_company


class CurrentCompanyMiddleware(MiddlewareMixin):
    """
    Middleware to attach the current user's company to the request object
    
    This enables automatic tenant isolation throughout the application.
    After this middleware runs, views can access request.company
    
    Thread-local cleanup is performed in process_response and process_exception
    to prevent context leakage between requests.
    """
    
    def process_request(self, request):
        """
        Attach company to request and set in thread-local storage
        
        Tries multiple lookup paths:
        1. user.profile.company
        2. user.userprofile.company
        3. user.driver_profile.company
        
        Args:
            request: HttpRequest object
        """
        company = None
        
        if request.user.is_authenticated:
            # Try multiple profile lookup paths
            for profile_attr in ['profile', 'userprofile', 'driver_profile']:
                try:
                    profile = getattr(request.user, profile_attr, None)
                    if profile and hasattr(profile, 'company'):
                        company = profile.company
                        break
                except AttributeError:
                    continue
        
        # Attach to request and thread-local
        request.company = company
        set_current_company(company)
    
    def process_response(self, request, response):
        """
        Clear thread-local company context after response
        
        Args:
            request: HttpRequest object
            response: HttpResponse object
        
        Returns:
            HttpResponse object
        """
        set_current_company(None)
        return response
    
    def process_exception(self, request, exception):
        """
        Clear thread-local company context on exception
        
        Args:
            request: HttpRequest object
            exception: Exception object
        
        Returns:
            None (allows exception to propagate)
        """
        set_current_company(None)
        return None
