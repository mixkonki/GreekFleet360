---
name: greekfleet-domain-knowledge
description: GreekFleet360 domain rules for fleet operations, personnel, transport orders, and cost intelligence. Use to avoid wrong modeling decisions.
---

You are coding inside the GreekFleet360 project (multi-tenant SaaS for fleet management & cost intelligence).

DOMAIN INVARIANTS (must not break):

TENANCY
- Every business entity is company-scoped (tenant key).
- request.company is the runtime tenant context (injected by middleware).
- Never accept company from client payloads.

PEOPLE / ROLES
- A real person should be modeled once.
- Driver is NOT a separate entity; driver is an Employee with a driver role (position.is_driver_role == True).
- Driver credentials (license, tachograph card, ADR) belong to Employee, but are required/validated only if the employee is a driver role.

VEHICLE ↔ DRIVER RELATIONSHIP
- Employee should NOT have a persistent assigned_vehicle field.
- Driver ↔ vehicle association occurs through a Transport Order / route assignment (TransportOrder).
- Vehicles can be reassigned across trips; do not store static driver-vehicle binding on Employee.

TRANSPORT ORDERS (ROUTES / TRIPS)
- TransportOrder is the unit of planning and assignment:
  - assigned_vehicle
  - assigned_driver (Employee, only drivers, only active)
- When assigned_driver is set:
  - enforce: employee.position.is_driver_role == True
  - enforce: employee.is_active == True
  - enforce: driver credentials valid (non-expired) when applicable

COMPLIANCE (prevent wrong dispatching)
- Do not allow scheduling a driver if required credentials are missing/expired:
  - Driver license expiry
  - Tachograph card expiry
  - ADR category and expiry (if ADR required by trip/vehicle/cargo in future)
- Validation should be deterministic; AI may explain, not decide.

COST INTELLIGENCE (mental model)
- Operational entries (FuelEntry, Maintenance, etc.) feed deterministic cost calculations.
- AI features should EXPLAIN and assist, not invent final costs.

UI / WORKFLOW EXPECTATIONS
- Finance → Settings → Personnel is for employee master data (no vehicle binding).
- Transport Orders UI should show "No driver assigned" when null and allow selecting only valid drivers.

WHEN IMPLEMENTING CHANGES
- Prefer incremental migrations.
- Update: model + forms + templates + views + tests together.
- Add tests for: cross-tenant safety, role constraints, inactive users, and credential expiry rules.

If requested work contradicts any invariant, stop and propose a safer alternative.
LEGACY NOTE
- DriverProfile is legacy/transitionary. Do not expand its usage. Prefer Employee with driver role, and migrate references away from DriverProfile.