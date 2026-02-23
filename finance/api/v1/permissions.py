"""
Analytics Permission Classes
Provides RBAC scaffold for analytics endpoints.

Current behavior: allow staff/admin (matches existing behavior).
Future: extend with role-based permissions (Owner, Finance, Dispatcher).
"""
from rest_framework.permissions import BasePermission


class AnalyticsPermission(BasePermission):
    """
    Permission class for analytics endpoints.

    Current rules:
    - User must be authenticated
    - User must be staff or superuser

    Future RBAC hooks (TODO):
    - Owner: full access to own company analytics
    - Finance: read-only access to cost/revenue analytics
    - Dispatcher: read-only access to operational KPIs only
    - Driver: no access to analytics

    Usage:
        class MyView(APIView):
            permission_classes = [AnalyticsPermission]
    """

    def has_permission(self, request, view):
        # Must be authenticated
        if not request.user or not request.user.is_authenticated:
            return False

        # Must be staff or superuser
        # TODO: extend with role-based checks when UserProfile.role is implemented
        # Example future logic:
        #   if hasattr(request.user, 'profile') and request.user.profile.role in ('OWNER', 'FINANCE'):
        #       return True
        return bool(request.user.is_staff or request.user.is_superuser)

    def has_object_permission(self, request, view, obj):
        # Object-level: ensure object belongs to user's company
        # This is enforced at the ORM level via tenant_context, but we add
        # an explicit check here as a belt-and-suspenders guard.
        if request.user.is_superuser:
            return True

        # For non-superusers, check company ownership
        company = getattr(request, 'company', None)
        if company is None and hasattr(request.user, 'company'):
            company = request.user.company

        if company is None:
            return False

        obj_company = getattr(obj, 'company', None) or getattr(obj, 'company_id', None)
        if obj_company is None:
            return True  # No company field — allow

        if hasattr(obj_company, 'id'):
            return obj_company.id == company.id
        return obj_company == company.id
