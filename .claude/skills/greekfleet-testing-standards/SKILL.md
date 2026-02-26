---
name: greekfleet-testing-standards
description: Enforces GreekFleet360 testing patterns (tenant safety, middleware pipeline, API vs UI regression tests).
---

You are writing tests for GreekFleet360 (Django + DRF). Follow these standards.

GENERAL PRINCIPLES
- Prefer integration tests that exercise the real middleware pipeline.
- Use APIClient + force_login for authenticated flows.
- Avoid RequestFactory/force_authenticate unless specifically testing a view method in isolation.

TENANCY TEST RULES
- Tenant context must flow via request.company (middleware).
- Tests must ensure:
  - Company A cannot see Company B data
  - Orphan authenticated user gets 403 with ORPHAN_COMPANY_MESSAGE
  - Cross-tenant foreign key injection is blocked (serializer validation)

WHAT TO TEST (minimum set for tenant-scoped endpoints)
1) list returns only tenant data
2) create succeeds within tenant
3) create fails cross-tenant FK
4) orphan GET/POST returns 403
5) unauthenticated returns 401/403 (as configured)

PATTERNS
- For API:
  - self.client.force_login(user)
  - response = self.client.get/post(...)
  - assert status, assert payload, assert DB state
- For model/business rules:
  - use TestCase and direct model creation
  - assert clean()/validation or custom validators

WHEN TO USE RequestFactory
- Only for pure unit tests where middleware is irrelevant.
- If using RequestFactory, you must explicitly document why.

RUN COMMAND
- Always run full suite before finalizing:
  python manage.py test

If any test bypasses tenancy pipeline, stop and propose an integration alternative.