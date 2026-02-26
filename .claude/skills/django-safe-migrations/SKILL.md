---
name: greekfleet-tenancy-guardrails
description: Enforces GreekFleet360 multi-tenant architecture and prevents tenant data leakage.
---

You are working inside the GreekFleet360 Django project.

This system is STRICTLY multi-tenant.

CORE TENANCY RULES:

1. request.company is the SINGLE source of tenant context.
2. Company must NEVER come from API payloads.
3. All queries MUST be tenant scoped.
4. Never use global querysets (.all()) on tenant models.
5. Always use TenantScopedModelViewSet or TenantScopedReadOnlyModelViewSet.
6. Orphan users MUST return 403.

QUERY PATTERNS:

Correct:
    Model.objects.filter(company=request.company)

Forbidden:
    Model.objects.all()
    serializer.save(company=request.data["company"])

SERIALIZERS:
- Company is injected server-side only.
- Foreign keys must be scoped to request.company.

TESTING RULES:
- Use force_login() instead of manual request mutation.
- Middleware pipeline must remain active.
- Always test cross-tenant isolation.

If a requested change risks tenant leakage:
STOP and propose a safer architecture.