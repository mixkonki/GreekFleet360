"""
Subscription Middleware for GreekFleet 360
Blocks access for expired subscriptions with allowlist
"""
from django.utils.deprecation import MiddlewareMixin
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone


class SubscriptionGateMiddleware(MiddlewareMixin):
    """
    Middleware to block access when company subscription is expired
    
    Allowlist:
    - Login/logout/signup
    - Password reset flow
    - Subscription expired page itself
    - Settings pages (for ADMIN only, to allow renewal)
    """
    
    # Paths that are always accessible (auth + expired page)
    ALLOWLIST_PATHS = [
        '/accounts/login/',
        '/accounts/logout/',
        '/accounts/signup/',
        '/accounts/password-reset/',
        '/accounts/password-reset/done/',
        '/accounts/password-reset-confirm/',
        '/accounts/password-reset-complete/',
        '/billing/expired/',
        '/admin/',  # Django admin always accessible
    ]
    
    # Paths accessible only for ADMIN when expired
    ADMIN_ALLOWLIST_PATHS = [
        '/settings/',
        '/accounts/me/',
        '/accounts/password-change/',
    ]
    
    def process_request(self, request):
        """
        Check subscription status and block if expired
        
        Args:
            request: HttpRequest object
        
        Returns:
            None if allowed, HttpResponse redirect if blocked
        """
        # Skip if user not authenticated
        if not request.user.is_authenticated:
            return None
        
        # Skip if no company attached
        if not hasattr(request, 'company') or request.company is None:
            return None
        
        # Check if subscription is expired
        company = request.company
        is_expired = self._is_subscription_expired(company)
        
        if not is_expired:
            return None
        
        # Subscription is expired - check allowlist
        path = request.path
        
        # Always allow these paths
        if any(path.startswith(allowed) for allowed in self.ALLOWLIST_PATHS):
            return None
        
        # Check if user is ADMIN for admin-only allowlist
        try:
            user_role = request.user.profile.role
            if user_role == 'ADMIN':
                if any(path.startswith(allowed) for allowed in self.ADMIN_ALLOWLIST_PATHS):
                    return None
        except AttributeError:
            pass
        
        # Block access - redirect to expired page
        return redirect(reverse('billing:expired'))
    
    def _is_subscription_expired(self, company):
        """
        Determine if company subscription is expired
        
        Args:
            company: Company instance
        
        Returns:
            bool: True if expired, False otherwise
        """
        # Check status field
        if company.subscription_status == 'EXPIRED':
            return True
        
        # Check expiry date
        if company.subscription_expires_at:
            now = timezone.now()
            if now > company.subscription_expires_at:
                return True
        
        return False
