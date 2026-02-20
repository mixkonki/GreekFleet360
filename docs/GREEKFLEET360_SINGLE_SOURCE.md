# GreekFleet 360 — Single Source of Truth

**Version:** 1.0 | **Date:** 2026-02-20 | **Branch:** `cost-engine-pr9-1`

> **This is the entry point for the entire documentation system.**  
> Read this first. Follow the links for depth.

---

## 1. Executive Overview

- **GreekFleet 360** is a multi-tenant SaaS fleet management platform built for the Greek transport market.
- **Core promise:** "Not just tracking — Decision Support." The system calculates true cost and profitability, with a roadmap toward actionable recommendations.
- **Target users:** ΦΔΧ/ΦΙΧ trucks, buses, taxis, corporate fleets, delivery motorcycles.
- **Architecture:** Django 5.0+ monolith, shared-database multi-tenancy, API-first analytics layer (DRF).
- **Tenant isolation** is enforced at the ORM level via `CompanyScopedManager` and `tenant_context()`. This is non-negotiable.
- **Cost Engine v1.0** is operational: calculates cost rates per cost center and order profitability. Schema v1 is documented and stable.
- **API layer** (`/api/v1/cost-engine/run/`) exists locally but is **not yet committed to `origin/main`**. See Section 2.
- **56 tests pass** covering tenant isolation, cost calculations, API security, and guardrail enforcement.
- **Architectural maturity:** Level 3 (Defined). Processes documented, patterns enforced, tests comprehensive.
- **Production readiness:** Core engine and isolation are production-ready. API layer, deployment guide, and token auth are pending.
- **Decision Support** (smart recommendations, ML optimization) is a **vision only** — not implemented.
- **VehicleAsset (polymorphic)** is **deleted**. The current vehicle model is `operations.Vehicle` (unified). README/PROJECT_BRIEF are outdated on this point.
- **`finance/legacy_services.py`** is deprecated. Use `finance/services/cost_engine/` for all cost calculations.
- **Next action:** Commit the untracked API layer + docs to a new branch and open a PR to `main`.

---

## 2. Current Reality — Truth Table

> **Audit date:** 2026-02-20 | **Remote:** `origin/main` @ `8d5e9a3`

| Artifact | `origin/main` | Local working tree |
|---|---|---|
| Cost Engine service layer (`finance/services/cost_engine/`) | ✅ Merged | ✅ Present |
| Snapshot models (`CostRateSnapshot`, `OrderCostBreakdown`) | ✅ Merged | ✅ Present |
| Batch command (`calculate_costs`) | ✅ Merged | ✅ Present |
| Core tests (9 files in `tests/`) | ✅ Merged | ✅ Present |
| **DRF API layer** (`finance/api/v1/`) | ❌ **ABSENT** | ✅ Untracked |
| **API tests** (`tests/test_cost_engine_api.py`) | ❌ **ABSENT** | ✅ Untracked |
| **Debug endpoint** (`finance/views_debug.py`) | ❌ **ABSENT** | ✅ Untracked |
| **Seed command** (`seed_cost_engine_demo.py`) | ❌ **ABSENT** | ✅ Untracked |
| **All `docs/` files** | ❌ **ABSENT** | ✅ Untracked |
| **All `*_REPORT.md` files** | ❌ **ABSENT** | ✅ Untracked |
| `greekfleet/settings.py` (DRF config) | ✅ Present | ✅ Modified (uncommitted) |
| `greekfleet/urls.py` (API routes) | ✅ Present | ✅ Modified (uncommitted) |

**Action required:** Create branch `docs-and-api-layer`, commit all untracked files + modified files, open PR → `main`.  
See full checklist: [`docs/DOCS_INDEX.md` § 4](./DOCS_INDEX.md#4-migration-checklist-align-repo--docs)

---

## 3. Authoritative Documents

| Document | Path | What it is for | When to read it |
|---|---|---|---|
| **Single Source** (this file) | `docs/GREEKFLEET360_SINGLE_SOURCE.md` | Entry point, orientation, quick reference | Always first |
| **Master Architecture** | `docs/MASTER_SYSTEM_ARCHITECTURE.md` | Full architecture narrative: domains, patterns, roadmap, deployment | Deep dives |
| **Docs Index** | `docs/DOCS_INDEX.md` | Truth table, doc inventory, migration checklist | Navigation |
| **Cost Engine Schema** | `docs/cost_engine_schema_v1.md` | API contract: fields, status rules, examples | Implementing against the API |
| **Strategic Audit** | `STRATEGIC_ARCHITECTURE_AUDIT.md` | Full audit: risks, gaps, strategic recommendations | Architecture decisions |

**Outdated (do not use as reference for current state):**

| Document | Issue |
|---|---|
| `README.md` | References deleted `VehicleAsset`, `django-polymorphic`, old admin URLs |
| `PROJECT_BRIEF.md` | Describes polymorphic model (gone), vision features as if planned |
| `CHANGELOG.md` | Roadmap phases 8-11 are stale; superseded by master doc |

---

## 4. Key Architectural Non-Negotiables

These rules are enforced by tests and must never be violated:

### 4.1 Tenant Isolation
- Every model that holds company data **must** use `CompanyScopedManager` (from `core/mixins.py`).
- All service-layer operations **must** run inside `with tenant_context(company):`.
- The bypass manager (`Model.all_objects`) is **FORBIDDEN** in `finance/services/`, `web/views.py`, and any service code.
- Allowed locations for `all_objects`: `admin.py`, `tests/`, `migrations/`, `core/mixins.py`.

### 4.2 Guardrails
- `tests/test_guardrails.py` scans the codebase for real bypass manager usage (`r'\.all_objects\.'`).
- This test **must always pass**. If it fails, a service-layer violation exists.
- Fail-fast behavior in DEBUG mode: `_require_tenant_context()` raises `RuntimeError` if context is missing.

### 4.3 Cost Engine Schema v1
- All Cost Engine results **must** conform to Schema v1: `{meta, snapshots, breakdowns, summary}`.
- `schema_version` field in `meta` must be `1` (integer).
- Monetary values use `Decimal` (never `float`) internally. DRF serializes them as JSON numbers (`COERCE_DECIMAL_TO_STRING: False`).
- `MISSING_ACTIVITY` status is set deterministically when `total_units == 0` for KM/HOUR/TRIP basis units.
- Snapshots use **replace-existing semantics** — no duplicate historical records.

### 4.4 Service Layer Purity
- `finance/legacy_services.py` is **deprecated**. Do not add new code there.
- All new cost calculations go through `finance/services/cost_engine/calculator.py`.
- The calculator is the **only** public entry point: `calculate_company_costs(company, period_start, period_end)`.

---

## 5. Cost Engine v1 — One-Page Summary

**What it does:** Given a company and a date range, it calculates:
1. **Cost rates** per cost center (€/km, €/hour, €/trip, or % of revenue)
2. **Order profitability** (revenue − vehicle cost − overhead = profit + margin %)
3. **Summary statistics** (total revenue, cost, profit, average margin)

**Architecture (5 layers):**
```
calculate_company_costs()   ← public entry point (calculator.py)
    └─> queries.py          ← fetch CostPostings + TransportOrders (scoped)
    └─> aggregations.py     ← sum costs by CostCenter
    └─> snapshots.py        ← build rate snapshots + order breakdowns
    └─> persist.py          ← save CostRateSnapshot + OrderCostBreakdown (atomic)
```

**Basis units:** `KM` | `HOUR` | `TRIP` | `REVENUE`

**Status values:** `OK` | `MISSING_ACTIVITY` | `MISSING_RATE`

**Full API contract:** → [`docs/cost_engine_schema_v1.md`](./cost_engine_schema_v1.md)

**Batch execution:**
```bash
python manage.py calculate_costs --period-start 2026-01-01 --period-end 2026-01-31
python manage.py calculate_costs --dry-run  # preview without saving
```

**Demo data:**
```bash
python manage.py seed_cost_engine_demo  # creates demo vehicle, cost centers, order
```

---

## 6. API Layer Summary

> ⚠️ **Status:** Implemented locally, **not yet committed to `origin/main`**.

### Production Endpoint

| Property | Value |
|---|---|
| URL | `GET /api/v1/cost-engine/run/` |
| Auth | Session (cookie-based) |
| Permission | Staff or Superuser only |
| Schema | v1.0 |

**Required parameters:** `period_start` (YYYY-MM-DD), `period_end` (YYYY-MM-DD)  
**Optional parameters:** `company_id` (superuser only), `only_nonzero=1`, `include_breakdowns=0`

**Error codes:** `400` bad params | `403` unauthorized | `404` company not found

### Debug Endpoint (DEV only)

| Property | Value |
|---|---|
| URL | `GET /finance/debug/cost-engine/` |
| Auth | None |
| Availability | `DEBUG=True` only (returns 404 in production) |

### Tests
- **11 API tests** in `tests/test_cost_engine_api.py` (local only, not yet committed)
- Covers: unauthenticated → 403, non-staff → 403, invalid dates → 400, company isolation, filters
- Full test suite: **56 tests passing**

**Full API documentation:** → [`API_COST_ENGINE_REPORT.md`](../API_COST_ENGINE_REPORT.md)

---

## 7. Roadmap Snapshot

### Phase 0 — Documentation Consolidation ✅ DONE (2026-02-20)
- Master architecture document created
- Docs index with truth table created
- Single source of truth entry point created

### Phase 1 — Stabilize + Deployment Readiness (Next Sprint)
- [ ] Commit API layer + docs to `main` (branch: `docs-and-api-layer`)
- [ ] Update README.md (remove VehicleAsset references)
- [ ] Add JWT/Token authentication for API
- [ ] Write deployment guide (Gunicorn + Nginx + PostgreSQL)
- [ ] Set up CI/CD pipeline

### Phase 2 — Snapshot-Read Analytics Endpoints (Next Month)
- [ ] `GET /api/v1/cost-engine/history/` — read persisted snapshots
- [ ] Period-over-period comparison endpoint
- [ ] Budget vs Actual tracking model

### Phase 3 — Async Execution (Next Quarter)
- [ ] Celery integration for background cost calculations
- [ ] Scheduled batch runs (cron-based)
- [ ] Large dataset handling without request timeouts

### Phase 4 — Decision Support MVP (Rule-Based)
- [ ] Threshold-based alerts (consumption spike > 15%)
- [ ] Maintenance prediction ("Service B due in 14 days")
- [ ] Cost-saving opportunity detection (tire strategy, fuel routing)

### Phase 5+ — ML & Integrations (Long-Term Vision)
- Fuel card CSV parsers (Coral, BP, EKO, Avin)
- GPS/Telematics webhook receiver (Teltonika, Geotab)
- MyData / TaxisNet government API integration
- ML-based forecasting and optimization
- Mobile PWA for drivers

**Full roadmap with dependencies:** → [`docs/MASTER_SYSTEM_ARCHITECTURE.md` § 11](./MASTER_SYSTEM_ARCHITECTURE.md#11-roadmap)

---

## 8. Historical Session Logs

These reports document specific implementation sessions. They are **read-only archives** — do not update them.

| Report | What it documents |
|---|---|
| [`API_COST_ENGINE_REPORT.md`](../API_COST_ENGINE_REPORT.md) | DRF API layer creation: views, urls, tests, security |
| [`DEBUG_ENDPOINT_REPORT.md`](../DEBUG_ENDPOINT_REPORT.md) | Debug endpoint creation and verification |
| [`GUARDRAIL_STABILIZATION_REPORT.md`](../GUARDRAIL_STABILIZATION_REPORT.md) | Guardrail regex improvement (false positive fix) |
| [`PERSISTENCE_FIX_REPORT.md`](../PERSISTENCE_FIX_REPORT.md) | Persistence layer tenant isolation fix |
| [`SEED_COST_ENGINE_DEMO_REPORT.md`](../SEED_COST_ENGINE_DEMO_REPORT.md) | Demo dataset creation and verification |

---

## Doc Drift Fixes

The following outdated references were found in existing documents and corrected in this documentation system:

| Outdated Reference | Found In | Current Reality |
|---|---|---|
| `VehicleAsset` (polymorphic parent model) | `README.md`, `PROJECT_BRIEF.md`, `CHANGELOG.md` | Deleted in `core/migrations/0006`. Use `operations.Vehicle`. |
| `django-polymorphic` in tech stack | `README.md` | Removed. No polymorphic inheritance in current codebase. |
| `Truck`, `Bus`, `PassengerCar`, `Moto` child models | `README.md`, `PROJECT_BRIEF.md` | Replaced by single `Vehicle` model with `vehicle_type` field. |
| `core/vehicleasset/add/` admin URL | `README.md` | Now `operations/vehicle/add/`. |
| `CostCalculator` (legacy service) | `README.md` Phase 3 description | Deprecated. Use `calculate_company_costs()` from `finance/services/cost_engine/calculator.py`. |
| `finance/services.py` (old path) | Various | Replaced by `finance/services/cost_engine/` package. |
| Phase 8-11 roadmap in `CHANGELOG.md` | `CHANGELOG.md` | Superseded by phased roadmap in this document and `MASTER_SYSTEM_ARCHITECTURE.md`. |

---

*GreekFleet 360 — Single Source of Truth*  
*Maintained by: Lead Architect | Last updated: 2026-02-20*
