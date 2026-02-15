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
    """
    
    def process_request(self, request):
        """
        Attach company to request and set in thread-local storage
        
        Args:
            request: HttpRequest object
        """
        if request.user.is_authenticated:
            try:
                # Get company from user's profile
                company = request.user.profile.company
                request.company = company
                # Set in thread-local for ORM-level filtering
                set_current_company(company)
            except AttributeError:
                # User has no profile or profile has no company
                request.company = None
                set_current_company(None)
        else:
            request.company = None
            set_current_company(None)
