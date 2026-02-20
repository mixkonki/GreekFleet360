# DOCS INDEX - GreekFleet 360

**Generated:** 2026-02-20  
**Purpose:** Single-source index of all documentation in the repository.  
**Maintained by:** Lead Architect / Tech Lead

---

## 1. Truth Table: Local vs Public main (origin/main)

> **Audit Date:** 2026-02-20  
> **Local branch:** `cost-engine-pr9-1`  
> **Remote main commit:** `8d5e9a3` (Merge PR #10)

| Artifact | Public `origin/main` | Local Working Tree | Notes |
|---|---|---|---|
| `finance/services/cost_engine/` (all 5 modules) | ✅ PRESENT | ✅ PRESENT | Core Cost Engine — committed & merged |
| `finance/management/commands/calculate_costs.py` | ✅ PRESENT | ✅ PRESENT | Batch command — committed & merged |
| `tests/test_cost_engine.py` | ✅ PRESENT | ✅ PRESENT | Committed & merged |
| `tests/test_cost_engine_calculation.py` | ✅ PRESENT | ✅ PRESENT | Committed & merged |
| `tests/test_cost_engine_persistence.py` | ✅ PRESENT | ✅ PRESENT | Committed & merged |
| `tests/test_guardrails.py` | ✅ PRESENT | ✅ PRESENT | Committed & merged |
| `finance/migrations/0012_ordercostbreakdown_costratesnapshot_and_more.py` | ✅ PRESENT | ✅ PRESENT | Committed & merged |
| `finance/api/v1/views.py` | ❌ ABSENT | ✅ PRESENT (untracked) | **Local only — never committed** |
| `finance/api/v1/urls.py` | ❌ ABSENT | ✅ PRESENT (untracked) | **Local only — never committed** |
| `finance/api/__init__.py` | ❌ ABSENT | ✅ PRESENT (untracked) | **Local only — never committed** |
| `finance/views_debug.py` | ❌ ABSENT | ✅ PRESENT (untracked) | **Local only — never committed** |
| `finance/urls.py` | ❌ ABSENT | ✅ PRESENT (untracked) | **Local only — never committed** |
| `tests/test_cost_engine_api.py` | ❌ ABSENT | ✅ PRESENT (untracked) | **Local only — never committed** |
| `finance/management/commands/seed_cost_engine_demo.py` | ❌ ABSENT | ✅ PRESENT (untracked) | **Local only — never committed** |
| `docs/cost_engine_schema_v1.md` | ❌ ABSENT | ✅ PRESENT (untracked) | **Local only — never committed** |
| `docs/MASTER_SYSTEM_ARCHITECTURE.md` | ❌ ABSENT | ✅ PRESENT (untracked) | **Local only — never committed** |
| `docs/DOCS_INDEX.md` (this file) | ❌ ABSENT | ✅ PRESENT (untracked) | **Local only — never committed** |
| `STRATEGIC_ARCHITECTURE_AUDIT.md` | ❌ ABSENT | ✅ PRESENT (untracked) | **Local only — never committed** |
| `API_COST_ENGINE_REPORT.md` | ❌ ABSENT | ✅ PRESENT (untracked) | **Local only — never committed** |
| `DEBUG_ENDPOINT_REPORT.md` | ❌ ABSENT | ✅ PRESENT (untracked) | **Local only — never committed** |
| `GUARDRAIL_STABILIZATION_REPORT.md` | ❌ ABSENT | ✅ PRESENT (untracked) | **Local only — never committed** |
| `PERSISTENCE_FIX_REPORT.md` | ❌ ABSENT | ✅ PRESENT (untracked) | **Local only — never committed** |
| `SEED_COST_ENGINE_DEMO_REPORT.md` | ❌ ABSENT | ✅ PRESENT (untracked) | **Local only — never committed** |
| `greekfleet/settings.py` | ✅ PRESENT | ✅ PRESENT (modified) | DRF config added locally, not committed |
| `greekfleet/urls.py` | ✅ PRESENT | ✅ PRESENT (modified) | API routes added locally, not committed |

**Key Finding:** The DRF API layer (`finance/api/`), debug endpoint, API tests, seed command, and all documentation files exist **only in the local working tree**. They have never been committed to any branch. The public `origin/main` contains the Cost Engine service layer but **no API exposure**.

---

## 2. Documentation Inventory

### 2.1 Authoritative Documents (Source of Truth)

| Document | Path | Purpose | Owner Domain | Freshness | Reading Order |
|---|---|---|---|---|---|
| **Master Architecture** | `docs/MASTER_SYSTEM_ARCHITECTURE.md` | Single authoritative reference for system architecture, strategy, and roadmap | All | ✅ Up-to-date | 1st |
| **Docs Index** | `docs/DOCS_INDEX.md` | Index of all docs, truth table, migration checklist | All | ✅ Up-to-date | 2nd |
| **Cost Engine Schema** | `docs/cost_engine_schema_v1.md` | API contract for Cost Engine v1.0 responses | Finance | ✅ Up-to-date | 3rd |
| **Strategic Audit** | `STRATEGIC_ARCHITECTURE_AUDIT.md` | Full architectural audit with risks, gaps, recommendations | All | ✅ Up-to-date | 4th |

### 2.2 Operational Reports (Historical Reference)

| Document | Path | Purpose | Owner Domain | Freshness | Reading Order |
|---|---|---|---|---|---|
| **API Report** | `API_COST_ENGINE_REPORT.md` | Documents DRF API implementation session | Finance/API | ✅ Up-to-date | 5th |
| **Debug Endpoint Report** | `DEBUG_ENDPOINT_REPORT.md` | Documents debug endpoint creation | Finance | ✅ Up-to-date | 6th |
| **Guardrail Report** | `GUARDRAIL_STABILIZATION_REPORT.md` | Documents guardrail regex improvement | Core | ✅ Up-to-date | 7th |
| **Persistence Fix Report** | `PERSISTENCE_FIX_REPORT.md` | Documents persistence layer fixes | Finance | ✅ Up-to-date | 8th |
| **Seed Demo Report** | `SEED_COST_ENGINE_DEMO_REPORT.md` | Documents demo data seeding | Finance | ✅ Up-to-date | 9th |

### 2.3 Outdated / Needs Update

| Document | Path | Purpose | Owner Domain | Freshness | Issue |
|---|---|---|---|---|---|
| **README** | `README.md` | Project overview and setup guide | All | ⚠️ Possibly outdated | References `VehicleAsset` (deleted), `django-polymorphic` (removed), old URL structure |
| **Project Brief** | `PROJECT_BRIEF.md` | Original vision and scope | All | ⚠️ Possibly outdated | Describes polymorphic vehicle model (now unified), vision-only features presented as planned |
| **Changelog** | `CHANGELOG.md` | Version history and roadmap | All | ⚠️ Possibly outdated | Roadmap phases (8-11) are unordered and lack dependencies; Phase 8.5 is the last real entry |

---

## 3. Single-Source-of-Truth Documentation Plan

### 3.1 Document Hierarchy

```
MASTER_SYSTEM_ARCHITECTURE.md  ← PRIMARY REFERENCE (this is the truth)
├── docs/cost_engine_schema_v1.md  ← API contract (referenced by master)
├── STRATEGIC_ARCHITECTURE_AUDIT.md  ← Full audit (referenced by master)
├── docs/DOCS_INDEX.md  ← Navigation index (this file)
└── *_REPORT.md files  ← Historical session logs (read-only archive)

README.md  ← NEEDS UPDATE (onboarding only, not architecture)
PROJECT_BRIEF.md  ← ARCHIVE (original vision, superseded by master doc)
CHANGELOG.md  ← NEEDS UPDATE (add new phases, remove stale roadmap)
```

### 3.2 What Each Document Should Contain

| Document | Should Contain | Should NOT Contain |
|---|---|---|
| `MASTER_SYSTEM_ARCHITECTURE.md` | Architecture, strategy, current state, roadmap, deployment, integrations | Raw session logs, full audit text |
| `docs/cost_engine_schema_v1.md` | API contract, field definitions, status rules, examples | Business strategy, roadmap |
| `STRATEGIC_ARCHITECTURE_AUDIT.md` | Full audit findings, risks, recommendations | Duplicated architecture narrative |
| `README.md` | Setup instructions, quick start, URL list | Architecture decisions, roadmap |
| `CHANGELOG.md` | Version history, completed phases | Future roadmap (move to master doc) |
| `PROJECT_BRIEF.md` | Original vision (archive) | Current state (it's outdated) |

### 3.3 Outdated References to Fix

| Document | Outdated Reference | Current Reality | Action |
|---|---|---|---|
| `README.md` | `VehicleAsset` (polymorphic parent) | `operations.Vehicle` (unified model) | Update README |
| `README.md` | `django-polymorphic` in tech stack | Removed in core migration 0006 | Update README |
| `README.md` | `core/vehicleasset/add/` admin URL | `operations/vehicle/add/` | Update README |
| `README.md` | Truck, Bus, PassengerCar, Moto child models | Single `Vehicle` model with type field | Update README |
| `PROJECT_BRIEF.md` | "The Polymorphic Model" section | Unified Vehicle model | Mark as archived |
| `CHANGELOG.md` | Phase 8-11 roadmap (unordered) | Superseded by master doc roadmap | Remove from CHANGELOG, keep in master |

---

## 4. Migration Checklist: Align Repo + Docs

### 4.1 Immediate Actions (Before Next Commit)

- [ ] **Commit untracked files** to a new branch `docs-and-api-layer`:
  - `finance/api/` (DRF API layer)
  - `finance/views_debug.py`
  - `finance/urls.py`
  - `tests/test_cost_engine_api.py`
  - `finance/management/commands/seed_cost_engine_demo.py`
  - `docs/` (all documentation)
  - `*_REPORT.md` files
  - `STRATEGIC_ARCHITECTURE_AUDIT.md`
  - Modified `greekfleet/settings.py` (DRF config)
  - Modified `greekfleet/urls.py` (API routes)

- [ ] **Open PR** from `docs-and-api-layer` → `main`

- [ ] **Update README.md**:
  - Replace `VehicleAsset` → `operations.Vehicle`
  - Remove `django-polymorphic` from tech stack
  - Update admin URLs
  - Add API endpoint documentation

### 4.2 Short-Term (Next Sprint)

- [ ] **Update CHANGELOG.md**:
  - Add Phase 8: Cost Engine v1.0 (completed)
  - Add Phase 9: API Layer (completed locally)
  - Remove stale roadmap phases (move to master doc)

- [ ] **Mark PROJECT_BRIEF.md as archived**:
  - Add header: `> ⚠️ ARCHIVED: This document reflects the original vision. See MASTER_SYSTEM_ARCHITECTURE.md for current state.`

- [ ] **Complete MASTER_SYSTEM_ARCHITECTURE.md**:
  - Sections 5-15 still need to be written
  - See table of contents in the document

### 4.3 Medium-Term (Before Production)

- [ ] **Add token authentication** (JWT/DRF Token) for API
- [ ] **Create deployment runbook** (Gunicorn + Nginx + PostgreSQL)
- [ ] **Set up CI/CD** with test runner
- [ ] **Add performance monitoring** (Sentry or similar)

---

## 5. Recommended Reading Order for New Developers

1. **`docs/MASTER_SYSTEM_ARCHITECTURE.md`** — Start here. Understand the system.
2. **`docs/DOCS_INDEX.md`** — Understand the documentation landscape (this file).
3. **`docs/cost_engine_schema_v1.md`** — Understand the API contract.
4. **`README.md`** — Set up your local environment.
5. **`STRATEGIC_ARCHITECTURE_AUDIT.md`** — Deep dive into architectural decisions and risks.
6. **`CHANGELOG.md`** — Understand what was built and when.
7. **`*_REPORT.md` files** — Historical context for specific implementation sessions.

---

## 6. Glossary of Key Terms

| Term | Definition |
|---|---|
| **Tenant** | A `Company` instance. All data is scoped to a tenant. |
| **Cost Engine** | The service layer (`finance/services/cost_engine/`) that calculates cost rates and order profitability. |
| **Cost Center** | A unit of cost allocation (VEHICLE or OVERHEAD type). |
| **CostPosting** | An actual cost transaction linked to a CostCenter and CostItem. |
| **CostRateSnapshot** | A persisted historical record of calculated cost rates for a period. |
| **OrderCostBreakdown** | A persisted historical record of order profitability for a period. |
| **tenant_context** | A Python context manager that sets the active company for scoped queries. |
| **CompanyScopedManager** | A Django manager that automatically filters by the current tenant. |
| **all_objects** | The bypass manager — **FORBIDDEN** in service layer code. |
| **Schema v1** | The current API response format for Cost Engine results. |
| **MISSING_ACTIVITY** | Status when a cost center has zero units (km/hours/trips) for the period. |
| **MISSING_RATE** | Status when an order breakdown cannot calculate a rate. |
| **VehicleAsset** | **DEPRECATED** — The old polymorphic vehicle model. Deleted in `core/migrations/0006`. |
| **operations.Vehicle** | The current unified vehicle model. Replaces VehicleAsset. |
| **legacy_services.py** | **DEPRECATED** — The old CostCalculator. Superseded by the Cost Engine service layer. |

---

*This document is maintained as part of the GreekFleet 360 documentation system.*  
*Last updated: 2026-02-20 by Senior Architect.*
