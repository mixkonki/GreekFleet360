---
name: greekfleet-ui-regression-checklist
description: Prevents UI regressions in GreekFleet360 by enforcing a checklist whenever models/forms/templates/views change.
---

You are working on GreekFleet360 (Django). The UI is server-rendered and tightly coupled to forms/templates/views.

Whenever you modify ANY of the following:
- Django models (add/remove/rename fields, FK changes)
- Forms (ModelForm fields/querysets)
- Templates (rendered fields/columns)
- Views (querysets/select_related/prefetch)

You MUST run this checklist and update all impacted layers.

CHECKLIST (must complete):

A) Model changes
- Confirm migrations exist and apply cleanly.
- If removing/renaming a field: search for references across repo.
  - templates
  - forms
  - views
  - admin
  - tests

B) Forms (web/forms.py)
- Update ModelForm fields list/exclude.
- Update any queryset scoping for FK dropdowns.
- Ensure conditional fields (e.g. driver-only credentials) do not block non-driver save.

C) Templates
- Update all templates that display or edit the changed field:
  - finance settings page: web/templates/finance_settings.html
  - employee modal: web/templates/partials/employee_form_modal.html
  - order pages: templates rendering TransportOrder
- Remove columns/labels for removed fields.
- Ensure pages still render when optional values are null.

D) Views (web/views.py)
- Update select_related/prefetch_related to match new relations.
- Remove outdated select_related fields.
- Ensure querysets remain company-scoped (do not introduce tenant leakage).

E) Routing / UI behavior
- Verify that key pages load:
  - /finance/settings/ (all tabs: expenses, cost centers, personnel)
  - Transport order list
  - Transport order detail ("No driver assigned" scenario)

F) Tests
- Update existing tests that referenced old fields/relations.
- Add regression tests for the modified workflow if it affects business logic.
- Run:
  - python manage.py test
  and ensure full suite is green.

COMMANDS (expected usage)
- Use ripgrep to find breakages:
  rg "assigned_vehicle" .
  rg "assigned_driver" .
- Use Django checks:
  python manage.py check
- Run full suite:
  python manage.py test

If any checklist item is incomplete, do not finalize changes.
Stop and list the missing updates.