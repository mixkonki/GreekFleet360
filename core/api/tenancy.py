"""
Tenant helpers & base ViewSets for GreekFleet360
"""
from __future__ import annotations

from rest_framework import viewsets
from rest_framework.exceptions import PermissionDenied

from core.tenant_context import tenant_context


ORPHAN_COMPANY_MESSAGE = (
    'Ο λογαριασμός σας δεν έχει συσχετισμένη εταιρεία. Επικοινωνήστε με τον διαχειριστή.'
)


class TenantRequiredMixin:
    orphan_message: str = ORPHAN_COMPANY_MESSAGE

    def get_company(self):
        return getattr(self.request, "company", None)

    def require_company(self):
        company = self.get_company()
        if not company:
            raise PermissionDenied(self.orphan_message)
        return company


class TenantScopedReadOnlyModelViewSet(
    TenantRequiredMixin,
    viewsets.ReadOnlyModelViewSet,
):
    """
    Tenant-scoped READ ONLY endpoints.
    """

    def get_queryset_base(self):
        return super().get_queryset()

    def get_queryset(self):
        company = self.require_company()
        base_qs = self.get_queryset_base()

        with tenant_context(company):
            return base_qs.filter(company=company)


class TenantScopedModelViewSet(
    TenantRequiredMixin,
    viewsets.ModelViewSet,
):
    """
    Tenant-scoped WRITE endpoints.
    """

    def get_queryset_base(self):
        return super().get_queryset()

    def get_queryset(self):
        company = self.require_company()
        base_qs = self.get_queryset_base()

        with tenant_context(company):
            return base_qs.filter(company=company)

    def create(self, request, *args, **kwargs):
        self.require_company()
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        company = self.require_company()
        with tenant_context(company):
            serializer.save(company=company)
