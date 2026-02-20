# MASTER SYSTEM ARCHITECTURE - GreekFleet 360

**Document Version:** 1.0  
**Last Updated:** 2026-02-20  
**Status:** Authoritative Reference  
**Audience:** Developers, Architects, Product Managers, Future Maintainers

---

## Table of Contents

1. [Executive Overview](#1-executive-overview)
2. [Platform Vision & Positioning](#2-platform-vision--positioning)
3. [Current State](#3-current-state)
4. [System Architecture](#4-system-architecture)
5. [Multi-Tenant Isolation Model](#5-multi-tenant-isolation-model)
6. [Cost Engine v1](#6-cost-engine-v1)
7. [API Layer](#7-api-layer)
8. [Persistence & Analytics Strategy](#8-persistence--analytics-strategy)
9. [Testing & Guardrails Strategy](#9-testing--guardrails-strategy)
10. [Risks & Mitigations](#10-risks--mitigations)
11. [Roadmap](#11-roadmap)
12. [Decision Support Vision](#12-decision-support-vision)
13. [Deployment Guide](#13-deployment-guide)
14. [Integration Guide](#14-integration-guide)
15. [Appendices](#15-appendices)

---

## 1. Executive Overview

### 1.1 System Vision

**GreekFleet 360** is a multi-tenant SaaS platform for holistic fleet and mobility management, designed specifically for the Greek transport market. The system provides:

- **Fleet Management**: Vehicle tracking, compliance monitoring, maintenance scheduling
- **Financial Intelligence**: True cost calculation, profitability analysis, break-even tracking
- **Decision Support**: Actionable recommendations for cost optimization (future vision)

**Core Promise:** "Not just tracking, but Decision Support"

### 1.2 Target Market

1. **Heavy Transport**: ΦΔΧ/ΦΙΧ trucks (public/private freight)
2. **Passenger Transport**: Buses (public/private), tourism coaches, minivans
3. **Taxi Fleets**: Including double-shift operations (Syntairia)
4. **Corporate Fleets**: Sales cars, technician vans, pool vehicles
5. **Micromobility**: Motorcycles, scooters (delivery/courier)

### 1.3 Business Positioning

**"Asset Agnostic Fleet Intelligence for the Greek Market"**

- Localized for Greek regulations (KTEO, Teli, Troxaia, ΠΕΙ/CPC)
- Multi-modal support (heavy transport → micromobility)
- SaaS model with strict tenant isolation
- API-first architecture for future integrations

### 1.4 Architectural Maturity

**Current Level:** 3 - Defined

- ✅ Documented architecture and processes
- ✅ Consistent patterns enforced via guardrails
- ✅ Comprehensive test coverage (56 tests passing)
- ✅ Schema versioning for API evolution

**Path to Level 4:** Add performance monitoring, define SLAs, track accuracy metrics

### 1.5 Technology Stack

**Backend:**
- Python 3.12
- Django 5.0+
- Django REST Framework 3.16.1
- PostgreSQL (production) / SQLite (development)

**Frontend:**
- HTMX (dynamic updates without SPA complexity)
- Alpine.js (reactive components)
- Tailwind CSS (utility-first styling)
- Leaflet.js (mapping)

**Admin:**
- Django Unfold theme
- Custom multi-tenant admin configuration

---

## 2. Platform Vision & Positioning

### 2.1 Problem Statement

Greek transport companies lack integrated tools that combine:
- Fleet management (vehicles, drivers, compliance)
- Financial intelligence (true profitability, not just expense tracking)
- Decision support (actionable recommendations, not just reports)

Existing solutions are either:
- **Too generic**: International platforms that don't understand Greek regulations
- **Too fragmented**: Separate tools for fleet, finance, compliance
- **Too expensive**: Enterprise-only pricing models

### 2.2 Solution Approach

**Integrated Platform** that provides:

1. **Operational Data Capture**
   - Fuel entries, service logs, incident reports
   - Automatic odometer updates via signals
   - Compliance tracking (KTEO, insurance, driver licenses)

2. **Financial Intelligence**
   - Cost Engine calculates true cost per km/hour/trip
   - Overhead allocation across fleet
   - Order profitability analysis
   - Break-even tracking

3. **Decision Support** (Vision - see Section 12)
   - Rule-based recommendations (Phase 1)
   - ML-powered optimization (Phase 2+)
   - Predictive maintenance alerts
   - Fuel optimization routing

### 2.3 Greek Market Focus

**Regulatory Compliance:**
- KTEO (Technical Inspection) tracking
- Teli (Circulation Tax) management
- Troxaia (Traffic Police) fine tracking
- ΠΕΙ/CPC (Driver CPC) certification
- Tachograph calibration (trucks)
- ADR certification (hazardous materials)

**Localization:**
- Greek language UI
- Greek date formats (DD/MM/YYYY)
- Greek number formats (1.234,56 €)
- Greek business practices (double-shift taxis, Syntairia)

### 2.4 Competitive Positioning

**Differentiators:**
1. **Greek-first design**: Not a translation, but built for Greek market
2. **Multi-modal**: Trucks to scooters in one platform
3. **API-first**: Enables integrations and custom dashboards
4. **Cost intelligence**: True profitability, not just expense tracking
5. **SaaS pricing**: Accessible to SMEs, not just enterprises

---

## 3. Current State

### 3.1 What is Operational Today

✅ **Multi-Tenant Infrastructure**
- Company model as tenant root
- Strict data isolation via scoped managers
- Tenant context enforcement with guardrails

✅ **Core Domain**
- Company management
- Employee and DriverProfile models
- Unified Vehicle model (operations.Vehicle)

✅ **Operations Domain**
- Vehicle tracking (unified model, not polymorphic)
- Fuel entry with auto-odometer updates
- Service logs with invoice attachments
- Incident reports (accidents, fines, breakdowns)

✅ **Finance Domain**
- Hierarchical expense structure (Family → Category → Expense)
- Cost centers (VEHICLE, OVERHEAD types)
- Cost items and postings
- Transport orders with revenue tracking
- **Cost Engine v1.0** (operational, tested, documented)

✅ **API Layer**
- REST API endpoint: `/api/v1/cost-engine/run/`
- Session authentication
- Staff/Superuser permissions
- Schema v1.0 responses
- Comprehensive security controls

✅ **Web Interface**
- Dashboard with live KPIs
- Vehicle list with HTMX pagination
- Order management with Leaflet maps
- Financial settings page
- HTMX-driven modals for data entry

✅ **Authentication**
- Signup/login/logout
- UserProfile linking User → Company
- Role-based access control foundation

✅ **Testing**
- 56 comprehensive tests passing
- Tenant isolation tests
- API security tests
- Cost calculation tests
- Guardrail violation tests

### 3.2 What is NOT Operational

❌ **Decision Support Engine**
- No recommendation engine
- No ML models
- No optimization algorithms
- Vision only (see Section 12)

❌ **Advanced Analytics**
- No time-series analysis
- No trend detection
- No forecasting
- No budget vs actual tracking

❌ **Integrations**
- No fuel card parsers
- No GPS/telematics integration
- No government API connections (MyData, TaxisNet)
- No webhook receivers

❌ **Mobile App**
- No PWA implementation
- No driver mobile interface
- Web UI only

❌ **Advanced Reporting**
- No PDF generation
- No Excel exports
- No custom dashboards per role

### 3.3 Production Readiness

**Ready for Production:**
- ✅ Multi-tenant isolation enforced
- ✅ Cost Engine v1.0 operational
- ✅ API layer secured
- ✅ Comprehensive test coverage
- ✅ Error logging configured

**Needs Before Production:**
- ⚠️ Deployment guide (see Section 13)
- ⚠️ Performance monitoring (APM)
- ⚠️ Backup strategy
- ⚠️ SSL/HTTPS configuration
- ⚠️ Token authentication for API (JWT/OAuth)

---

## 4. System Architecture

### 4.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Web Layer                             │
│  (HTMX + Alpine.js + Tailwind CSS + Leaflet.js)            │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      API Layer (DRF)                         │
│  - Authentication (Session/Token)                            │
│  - Permissions (Staff/Superuser)                             │
│  - Schema Versioning (v1.0)                                  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Service Layer                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Cost Engine  │  │ Operations   │  │ Compliance   │      │
│  │ (Finance)    │  │ Services     │  │ Services     │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Domain Layer (Models)                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │  Core    │  │Operations│  │ Finance  │  │ Accounts │   │
│  │ (Tenant) │  │(Vehicles)│  │ (Costs)  │  │  (Auth)  │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              Data Layer (PostgreSQL + PostGIS)               │
│  - Shared database with tenant isolation                     │
│  - Scoped managers enforce company filtering                 │
└─────────────────────────────────────────────────────────────┘
```

### 4.2 Domain Boundaries (Bounded Contexts)

#### 4.2.1 Core Domain (`core/`)

**Responsibility:** Tenant infrastructure and shared entities

**Models:**
- `Company` - Tenant root, multi-tenant anchor
- `Employee` - Human resources
- `DriverProfile` - Driver-specific data (licenses, CPC, medical exams)

**Infrastructure:**
- `tenant_context.py` - Context manager for tenant isolation
- `mixins.py` - CompanyScopedManager, CompanyScopedModel
- `middleware.py` - Sets request.company from user session

**Key Patterns:**
- All models inherit from `CompanyScopedModel`
- All managers inherit from `CompanyScopedManager`
- Tenant context enforced via guardrails

#### 4.2.2 Operations Domain (`operations/`)

**Responsibility:** Operational data capture and vehicle management

**Models:**
- `Vehicle` - Unified vehicle model (replaces polymorphic VehicleAsset)
- `FuelEntry` - Fuel purchases with consumption tracking
- `ServiceLog` - Maintenance records with invoice attachments
- `IncidentReport` - Accidents, fines, breakdowns

**Key Features:**
- Auto-odometer updates via Django signals
- Health scoring system
- Compliance tracking (KTEO, insurance expiry)

**Design Decision:** Unified Vehicle model (not polymorphic) for:
- Simpler queries
- Better performance
- Easier maintenance
- Type-specific fields stored as nullable columns

#### 4.2.3 Finance Domain (`finance/`)

**Responsibility:** Financial intelligence and cost calculations

**Master Data (Shared across tenants):**
- `ExpenseFamily` - Top-level expense grouping
- `ExpenseCategory` - Expense categories within families

**Tenant Data:**
- `CostCenter` - Cost allocation units (VEHICLE, OVERHEAD types)
- `CostItem` - Cost line items
- `CostPosting` - Actual cost transactions
- `CompanyExpense` - Recurring/one-off expenses
- `TransportOrder` - Revenue-generating orders

**Analytics Models:**
- `CostRateSnapshot` - Historical cost rates per cost center
- `OrderCostBreakdown` - Historical order profitability

**Cost Engine Service:**
- `calculator.py` - Main orchestrator
- `queries.py` - Data fetching
- `aggregations.py` - Cost summation
- `snapshots.py` - Rate calculation, breakdown building
- `persist.py` - Database persistence

#### 4.2.4 Web Domain (`web/`)

**Responsibility:** Frontend views, forms, templates

**Key Features:**
- HTMX-driven UI (no page reloads)
- Alpine.js for reactive components
- Tailwind CSS styling
- Leaflet.js maps for route visualization

**Views:**
- Dashboard with live KPIs
- Vehicle list with infinite scroll
- Order management with maps
- Financial settings page

#### 4.2.5 Accounts Domain (`accounts/`)

**Responsibility:** Authentication and user management

**Models:**
- `UserProfile` - Links Django User to Company

**Views:**
- Signup (creates User + Company + Profile)
- Login/Logout
- Password reset (planned)

### 4.3 Data Flow

#### 4.3.1 Cost Calculation Flow

```
1. User Request
   └─> API Endpoint: /api/v1/cost-engine/run/
       └─> Authentication & Permission Check
           └─> Tenant Context Established
               └─> Cost Engine Calculator
                   ├─> Queries: Fetch CostPostings, TransportOrders
                   ├─> Aggregations: Sum costs by CostCenter
                   ├─> Snapshots: Calculate rates, build breakdowns
                   └─> Persist: Save to CostRateSnapshot, OrderCostBreakdown
                       └─> Return: Schema v1 JSON response
```

#### 4.3.2 Operational Data Flow

```
1. Fuel Entry Created
   └─> Signal: post_save
       └─> Update Vehicle.odometer
           └─> Calculate consumption (L/100km)
               └─> Update Vehicle.average_fuel_consumption

2. Service Log Created
   └─> Signal: post_save
       └─> Update Vehicle.last_service_date
           └─> Calculate next service due
```

### 4.4 Technology Decisions

#### 4.4.1 Why Django?

**Rationale:**
- Mature ORM with excellent multi-tenant support
- Built-in admin interface (rapid development)
- Strong security defaults (CSRF, SQL injection protection)
- Large ecosystem (DRF, Celery, etc.)
- Python 3.12 compatibility

**Trade-offs:**
- Monolithic architecture (vs microservices)
- Synchronous by default (async support limited)
- ORM overhead (vs raw SQL)

#### 4.4.2 Why HTMX (not React/Vue)?

**Rationale:**
- Simpler mental model (server-side rendering)
- No build step, no npm dependencies
- Progressive enhancement (works without JS)
- Smaller payload (no large JS bundles)
- Faster development for CRUD interfaces

**Trade-offs:**
- Less suitable for complex SPAs
- Limited offline capabilities
- Requires server round-trips

#### 4.4.3 Why Shared Database (not Schema-per-Tenant)?

**Rationale:**
- Cost-effective for SaaS (single database instance)
- Simpler backup/restore
- Easier migrations
- Sufficient for current scale

**Trade-offs:**
- Requires strict ORM discipline
- Risk of cross-tenant queries (mitigated by guardrails)
- Harder to scale individual tenants

---


## 5. Multi-Tenant Isolation Model

> **Non-negotiable.** Tenant isolation is enforced at every layer. Violations are caught by automated tests.

### 5.1 Model

**Shared Database, Scoped Queries** — all companies share one database. Isolation is enforced by the ORM, not by schema separation.

**Rationale:** Cost-effective for SaaS, simpler migrations, sufficient for current scale. Trade-off: requires strict ORM discipline.

### 5.2 Implementation

#### Tenant Root
`core.Company` is the tenant anchor. Every data model has a `company` FK.

#### CompanyScopedManager (`core/mixins.py`)
```python
class CompanyScopedManager(models.Manager):
    def get_queryset(self):
        company = get_current_company()  # from thread-local
        if company is None:
            return super().get_queryset().none()  # safe default
        return super().get_queryset().filter(company=company)
```
- Returns empty queryset (not all data) when no tenant context is set.
- All tenant models use this as their default manager (`objects`).

#### tenant_context (`core/tenant_context.py`)
```python
with tenant_context(company):
    # All ORM queries inside here are scoped to `company`
    result = calculate_company_costs(company, start, end)
```
- Sets a thread-local variable that `CompanyScopedManager` reads.
- **Required** for all service-layer operations.

#### Middleware (`core/middleware.py`)
- Sets `request.company` from the authenticated user's `UserProfile.company`.
- Web views use `request.company` to establish context.

### 5.3 Guardrails

#### The Bypass Manager (`all_objects`)
`CompanyScopedModel` exposes `Model.all_objects` — an unscoped manager that bypasses tenant filtering.

**Allowed locations:**
- `admin.py` — admin needs cross-tenant visibility
- `tests/` — tests create data for multiple tenants
- `migrations/` — schema operations only
- `core/mixins.py` — manager definition itself

**FORBIDDEN in:**
- `finance/services/` — service layer must be tenant-pure
- `web/views.py` — views must respect tenant context
- Any new service or view code

#### Automated Enforcement
`tests/test_guardrails.py` scans all Python files for the pattern `r'\.all_objects\.'` (real usage, not comments). This test must always pass.

#### Fail-Fast in DEBUG
`_require_tenant_context()` in `persist.py` raises `RuntimeError` in DEBUG mode if called outside `tenant_context`. Prevents silent empty-queryset bugs during development.

### 5.4 Forbidden Patterns

```python
# ❌ FORBIDDEN — bypasses tenant isolation
CostCenter.all_objects.filter(type='VEHICLE')

# ❌ FORBIDDEN — raw SQL without company filter
cursor.execute("SELECT * FROM finance_costcenter")

# ❌ FORBIDDEN — service code outside tenant_context
calculator = CostEngineCalculator(company, start, end)
result = calculator.calculate()  # no tenant_context wrapper

# ✅ CORRECT
with tenant_context(company):
    result = calculate_company_costs(company, start, end)
```

### 5.5 Security Properties

- **Data isolation:** A user can never see another company's data through normal ORM queries.
- **Belt & suspenders:** Scoped manager + explicit `company=company` filters in service code.
- **No cross-tenant leakage:** Verified by `tests/test_tenant_isolation.py` and `tests/test_admin_isolation.py`.

---

## 6. Cost Engine v1

> **Status:** ✅ Operational. Schema v1.0 stable. See `docs/cost_engine_schema_v1.md` for full contract.

### 6.1 Purpose

Calculate, for a given company and date range:
1. **Cost rates** per cost center (€/km, €/hour, €/trip, % of revenue)
2. **Order profitability** (revenue − vehicle cost − overhead = profit + margin)
3. **Summary statistics** (aggregated across all orders)

### 6.2 Architecture

```
calculate_company_costs(company, period_start, period_end)
    │  ← Public entry point. Always call inside tenant_context.
    │
    ├─> queries.py
    │     fetch_cost_postings()       ← CostPosting records for period
    │     fetch_transport_orders()    ← TransportOrder records for period
    │     get_order_activity()        ← km, revenue, km_by_vehicle
    │
    ├─> aggregations.py
    │     aggregate_postings_by_cost_center()  ← sum costs per CostCenter.id
    │
    ├─> snapshots.py
    │     build_cost_center_snapshot()  ← rate = total_cost / total_units
    │     build_order_breakdown()       ← vehicle_alloc + overhead_alloc
    │     format_calculation_summary()  ← aggregate stats
    │
    └─> persist.py (optional, called separately)
          save_cost_rate_snapshots()      ← atomic upsert to CostRateSnapshot
          save_order_cost_breakdowns()    ← atomic upsert to OrderCostBreakdown
```

### 6.3 Key Models

| Model | Purpose |
|---|---|
| `CostCenter` | Cost allocation unit. Types: `VEHICLE`, `OVERHEAD`. |
| `CostItem` | Named cost line item (e.g., "Fuel", "Insurance"). |
| `CostPosting` | Actual cost transaction: amount + period + CostCenter + CostItem. |
| `TransportOrder` | Revenue-generating order with distance, revenue, assigned vehicle. |
| `CostRateSnapshot` | Persisted historical rate per CostCenter per period. |
| `OrderCostBreakdown` | Persisted historical profitability per order per period. |

### 6.4 Basis Units

| Unit | Description | Used For |
|---|---|---|
| `KM` | Kilometers driven | Vehicle cost centers |
| `HOUR` | Hours operated | Time-based cost centers |
| `TRIP` | Number of trips | Per-trip cost centers |
| `REVENUE` | Revenue generated | Overhead cost centers |

### 6.5 Status Rules

| Status | Condition |
|---|---|
| `OK` | Normal calculation with activity data |
| `MISSING_ACTIVITY` | `total_units == 0` for KM, HOUR, or TRIP basis units |
| `MISSING_RATE` | Order breakdown cannot find a rate for the assigned vehicle's cost center |

### 6.6 Decimal Precision Rules

- All monetary values use Python `Decimal` (never `float`) internally.
- `_to_decimal()` helper normalizes all inputs safely.
- DRF serializes Decimals as JSON numbers (`COERCE_DECIMAL_TO_STRING: False`).
- This prevents rounding errors in profitability calculations.

### 6.7 Persistence Semantics

- **Replace-existing:** `save_cost_rate_snapshots()` deletes existing snapshots for the same company+period before inserting new ones.
- **Atomic:** All persistence operations use `transaction.atomic()`.
- **Idempotent:** Running the same calculation twice produces the same result (no duplicates).

### 6.8 Audit Summary

> See `STRATEGIC_ARCHITECTURE_AUDIT.md` for full details.

- ✅ Multi-tenant architecture properly implemented
- ✅ Cost Engine v1.0 operational and tested
- ✅ API-first approach enables future flexibility
- ✅ Domain-driven design with clear bounded contexts
- ✅ Guardrails enforced (tests prevent violations)
- ✅ Schema versioning (v1.0 documented)
- ⚠️ Documentation lag (VehicleAsset references in README/PROJECT_BRIEF)
- ⚠️ Dual cost systems (legacy_services.py vs new Cost Engine)
- ⚠️ Vision-reality gap (Decision Support not yet implemented)
- ⚠️ No token authentication (session only)
- ⚠️ No async task queue (synchronous calculations only)
- ⚠️ No deployment guide
- ⚠️ API layer not yet committed to main
- ⚠️ No time-series analytics
- ⚠️ No budget vs actual tracking

---

## 7. API Layer (DRF)

> **Status:** ✅ Implemented locally. ❌ Not yet committed to `origin/main`.

### 7.1 Design Philosophy

- **API-First:** Cost Engine analytics exposed via REST API, decoupled from presentation.
- **Schema-Versioned:** All responses include `schema_version` for backward-compatible evolution.
- **Tenant-Isolated:** All API calls run inside `tenant_context(company)`.
- **JSON-Only:** No browsable API (`JSONRenderer` only).

### 7.2 Endpoints

#### Production: `GET /api/v1/cost-engine/run/`

| Property | Value |
|---|---|
| Authentication | Session (cookie) |
| Permission | `IsAuthenticated` + `IsAdminUser` (Staff or Superuser) |
| Renderer | JSON only |

**Query Parameters:**

| Parameter | Required | Type | Description |
|---|---|---|---|
| `period_start` | ✅ | YYYY-MM-DD | Period start date |
| `period_end` | ✅ | YYYY-MM-DD | Period end date |
| `company_id` | No | integer | Superuser only; defaults to user's company |
| `only_nonzero` | No | 0/1 | Filter snapshots with cost/rate > 0 |
| `include_breakdowns` | No | 0/1 | Include order breakdowns (default: 1) |

**Error Responses:**
- `400` — Missing/invalid parameters or date range
- `403` — Unauthenticated or insufficient permissions
- `404` — Company not found

#### Debug: `GET /finance/debug/cost-engine/`

- No authentication required
- Returns 404 when `DEBUG=False` (production-safe)
- Uses first company in DB, hardcoded period 2026-01-01 to 2026-01-31
- For development inspection only

### 7.3 Authentication Strategy

**Current:** Session authentication (cookie-based). Suitable for web UI.

**Needed for production integrations:** Token authentication (JWT or DRF Token).
- Add `rest_framework.authtoken` or `djangorestframework-simplejwt`
- Keep session auth for web UI
- Use token auth for mobile apps and external integrations

### 7.4 Schema Versioning Strategy

- Current: `schema_version: 1` in all responses
- Future v2: Add new fields without removing v1 fields (backward compatible)
- Breaking changes: Increment to v2, maintain v1 endpoint for deprecation period
- Clients should check `schema_version` before parsing

### 7.5 Test Coverage

11 tests in `tests/test_cost_engine_api.py`:
- Unauthenticated request → 403
- Non-staff user → 403
- Missing period parameters → 400
- Invalid date format → 400
- Invalid date range → 400
- Invalid company_id → 404
- Non-superuser cannot specify company_id
- Staff user can access endpoint
- Superuser can specify company_id
- `only_nonzero` filter works
- `include_breakdowns` parameter works

---

## 8. Persistence & Analytics Strategy

### 8.1 Two-Tier Data Model

**Tier 1: Transactional Data** (source of truth)
- `CostPosting` — actual cost transactions
- `TransportOrder` — revenue-generating orders
- `FuelEntry`, `ServiceLog` — operational data
- Real-time, mutable, always current

**Tier 2: Analytical Snapshots** (calculated results)
- `CostRateSnapshot` — historical cost rates per cost center per period
- `OrderCostBreakdown` — historical order profitability per period
- Immutable once calculated, replaced on recalculation
- Enables trend analysis without recalculation

### 8.2 Persistence Service (`persist.py`)

```python
from finance.services.cost_engine.persist import CostEnginePersistence

with tenant_context(company):
    persistence = CostEnginePersistence()
    persistence.save_cost_rate_snapshots(company, start, end, result["snapshots"])
    persistence.save_order_cost_breakdowns(company, start, end, result["breakdowns"])
```

**Key behaviors:**
- **Dual-format input:** Accepts both dict (from tests) and list (from calculator)
- **Replace-existing:** Deletes old snapshots for same company+period before inserting
- **Atomic:** Wrapped in `transaction.atomic()`
- **Retrieval:** `get_cost_rate_snapshot()`, `get_all_cost_rate_snapshots()` for historical reads

### 8.3 Historical Tracking Philosophy

- Snapshots are **point-in-time records** of what was calculated and when.
- They support audit trails: "What was the cost rate for Vehicle X in January 2026?"
- They enable trend analysis: compare rates across periods without recalculation.
- They are **not** the source of truth — transactional data is.

### 8.4 Future Analytics Expansion

**Phase 2 (planned):**
- `GET /api/v1/cost-engine/history/` — read persisted snapshots
- Period-over-period comparison
- Trend detection (cost rate increasing/decreasing)

**Phase 3 (planned):**
- Async calculation via Celery
- Scheduled batch runs
- Large dataset handling

---

## 9. Testing & Guardrails Strategy

### 9.1 Test Suite Overview

**Total:** 56 tests passing (as of 2026-02-20)

| Test File | Coverage Area | Count |
|---|---|---|
| `tests/test_tenant_isolation.py` | Cross-tenant data isolation | ~8 |
| `tests/test_admin_isolation.py` | Admin panel tenant isolation | ~6 |
| `tests/test_view_isolation.py` | View-level tenant isolation | ~6 |
| `tests/test_company_autoset.py` | Auto-assignment of company | ~4 |
| `tests/test_guardrails.py` | Bypass manager detection | ~3 |
| `tests/test_cost_engine.py` | Cost Engine integration | ~8 |
| `tests/test_cost_engine_calculation.py` | Calculation logic | ~8 |
| `tests/test_cost_engine_persistence.py` | Persistence layer | 8 |
| `tests/test_cost_engine_api.py` | API security + behavior | 11 |

### 9.2 Tenant-Safe Test Patterns

```python
class MyTestCase(TestCase):
    def setUp(self):
        # Create two companies to test isolation
        self.company_a = Company.objects.create(name="Company A")
        self.company_b = Company.objects.create(name="Company B")
        
        # Create data inside tenant_context
        with tenant_context(self.company_a):
            self.cost_center = CostCenter.objects.create(
                name="Test CC", company=self.company_a
            )
    
    def test_isolation(self):
        # Verify company_b cannot see company_a's data
        with tenant_context(self.company_b):
            self.assertEqual(CostCenter.objects.count(), 0)
```

**Rules for tenant-safe tests:**
- Always create test data inside `tenant_context()`
- Always assert inside `tenant_context()` for scoped reads
- Use `Model.all_objects` only when you explicitly need cross-tenant data
- Test both positive (can see own data) and negative (cannot see other's data) cases

### 9.3 Guardrail Enforcement

`tests/test_guardrails.py` scans all `.py` files for `r'\.all_objects\.'`:
- Skips comment lines (starting with `#`)
- Skips allowed locations (admin.py, tests/, migrations/, core/mixins.py)
- Fails the test if any violation is found in service/view code

**This test must always pass.** If it fails, a developer has introduced a tenant isolation violation.

### 9.4 Running Tests

```bash
# Full test suite
python manage.py test

# Specific test file
python manage.py test tests.test_cost_engine_api

# With verbosity
python manage.py test --verbosity=2
```

---

## 10. Risks & Mitigations

| Risk | Severity | Status | Mitigation |
|---|---|---|---|
| API layer not committed to main | 🔴 HIGH | Open | Create `docs-and-api-layer` branch, open PR |
| Documentation lag (VehicleAsset refs) | 🟡 MEDIUM | Open | Update README.md, mark PROJECT_BRIEF as archived |
| Dual cost systems (legacy vs new) | 🟡 MEDIUM | Open | Add deprecation notice to `legacy_services.py` |
| No token authentication | 🟡 MEDIUM | Open | Add JWT/DRF Token before mobile/integration work |
| Synchronous calculations (timeout risk) | 🟢 LOW | Mitigated | Batch command exists; Celery planned for Phase 3 |
| Vision-reality gap (Decision Support) | 🟡 MEDIUM | Acknowledged | Phased roadmap; rule-based first, ML later |
| No deployment guide | 🟡 MEDIUM | Open | See Section 13 (minimal guide) |
| No performance monitoring | 🟢 LOW | Open | Add Sentry/APM before production |

---

## 11. Roadmap

### Phase 0 — Documentation Consolidation ✅ COMPLETE (2026-02-20)
- `docs/MASTER_SYSTEM_ARCHITECTURE.md` created
- `docs/DOCS_INDEX.md` created (truth table + migration checklist)
- `docs/GREEKFLEET360_SINGLE_SOURCE.md` created (entry point)

### Phase 1 — Stabilize + Deployment Readiness
**Goal:** Get everything committed and production-deployable.
- [ ] Commit API layer + docs to `main` (branch: `docs-and-api-layer`)
- [ ] Update README.md (remove VehicleAsset, add API docs)
- [ ] Add JWT/Token authentication for API
- [ ] Write deployment runbook (Gunicorn + Nginx + PostgreSQL)
- [ ] Set up CI/CD pipeline (GitHub Actions)
- [ ] Add deprecation notice to `legacy_services.py`

### Phase 2 — Snapshot-Read Analytics Endpoints
**Goal:** Expose historical data via API.
- [ ] `GET /api/v1/cost-engine/history/` — read persisted snapshots
- [ ] Period-over-period comparison endpoint
- [ ] Budget model + Budget vs Actual tracking
- [ ] Date range picker in web UI

### Phase 3 — Async Execution
**Goal:** Handle large datasets without timeouts.
- [ ] Celery + Redis integration
- [ ] Background cost calculation tasks
- [ ] Scheduled batch runs (cron)
- [ ] Task status endpoint (`GET /api/v1/tasks/{id}/`)

### Phase 4 — Decision Support MVP (Rule-Based)
**Goal:** First actionable recommendations.
- [ ] Threshold alerts: consumption spike > 15% → alert
- [ ] Maintenance prediction: "Service B due in 14 days"
- [ ] Cost-saving detection: identify loss-making vehicles
- [ ] Alert model + notification system

### Phase 5 — Advanced Analytics
**Goal:** Time-series and forecasting.
- [ ] Trend detection (cost rate increasing/decreasing over periods)
- [ ] Seasonality analysis
- [ ] Forecasting (next period cost estimate)
- [ ] What-if simulations (scenario planning)

### Phase 6+ — Integrations & Mobile
**Goal:** Connect to external systems.
- Fuel card CSV parsers (Coral, BP, EKO, Avin)
- GPS/Telematics webhook receiver (Teltonika, Geotab)
- MyData / TaxisNet government API
- Mobile PWA for drivers (expense capture, check-ins)

---

## 12. Decision Support Vision

> **Current status:** Vision only. No implementation exists.

### 12.1 What "Decision Support" Means

The system should not just report costs — it should tell the user **what to do**:

- *"Vehicle X fuel consumption increased 15% this month. Check injectors."*
- *"Detour 2km to EKO station to save €12 on this trip."*
- *"Buying Michelin Class A tires saves €300 in fuel over 50,000km."*
- *"Service B is due in 14 days based on current daily km. Book now."*

### 12.2 Rule-Based MVP (Phase 4)

Start with deterministic rules before ML:

| Rule | Data Required | Output |
|---|---|---|
| Consumption spike | FuelEntry history (L/100km trend) | Alert if >15% increase |
| Maintenance due | Vehicle.odometer + ServiceLog.last_km | Alert if within 500km of interval |
| Loss-making vehicle | OrderCostBreakdown.margin | Alert if margin < 0% for 3+ consecutive periods |
| Idle vehicle | TransportOrder count per vehicle | Alert if no orders in 30 days |

### 12.3 Data Requirements for ML (Phase 5+)

- Minimum 12 months of cost data per vehicle
- Consistent fuel entry recording (full-tank method)
- GPS/telematics data for route optimization
- External fuel price data (per station, per day)

### 12.4 Success Metrics

- Rule-based: Alert accuracy > 90% (no false positives)
- Maintenance prediction: Predict within ±3 days
- Fuel optimization: Measurable savings vs baseline

---

## 13. Deployment Guide

> **Minimal practical guide.** Full runbook to be created in Phase 1.

### 13.1 Environment Variables

```bash
# Required
SECRET_KEY=<strong-random-key>
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
DATABASE_URL=postgresql://user:pass@localhost:5432/greekfleet360

# Email (for error notifications)
EMAIL_HOST=smtp.yourprovider.com
EMAIL_PORT=587
EMAIL_HOST_USER=info@yourdomain.com
EMAIL_HOST_PASSWORD=<password>
DEFAULT_FROM_EMAIL=info@yourdomain.com
ADMIN_EMAIL=admin@yourdomain.com

# Optional
ENGINE_VERSION=1.0.0
```

### 13.2 Production Stack

```
Internet → Nginx (SSL termination, static files)
         → Gunicorn (WSGI, 4 workers)
         → Django application
         → PostgreSQL (primary database)
         → Redis (future: Celery broker)
```

### 13.3 Quick Start (Development)

```bash
# 1. Clone and setup
git clone https://github.com/mixkonki/GreekFleet360.git
cd GreekFleet360
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -r requirements.txt

# 2. Configure
copy .env.example .env
# Edit .env with your settings

# 3. Database
python manage.py migrate
python manage.py createsuperuser

# 4. Seed demo data (optional)
python manage.py seed_finance_data
python manage.py seed_cost_engine_demo

# 5. Run
python manage.py runserver
```

### 13.4 Key Management Commands

```bash
# Calculate costs for a period
python manage.py calculate_costs --period-start 2026-01-01 --period-end 2026-01-31

# Dry run (no database writes)
python manage.py calculate_costs --dry-run

# Promote user to staff
python manage.py promote_user <username>
```

---

## 14. Integration Guide

> **Status:** No integrations implemented. This section documents planned integration points.

### 14.1 Planned Integrations

| Integration | Type | Status | Priority |
|---|---|---|---|
| Fuel cards (Coral, BP, EKO, Avin) | CSV import | Planned | High |
| GPS/Telematics (Teltonika, Geotab) | Webhook receiver | Planned | High |
| MyData (AADE) | REST API | Planned | Medium |
| TaxisNet | REST API | Planned | Low |
| Mobile PWA | Internal API | Planned | Medium |

### 14.2 Webhook Architecture (Planned)

```
External GPS Provider
    → POST /api/v1/webhooks/telematics/
        → Validate signature
        → Parse payload
        → Create FuelEntry / update Vehicle.odometer
        → Trigger cost recalculation (async)
```

### 14.3 Fuel Card CSV Import (Planned)

```python
# Planned interface
from finance.importers.fuel_cards import CoralCSVImporter

importer = CoralCSVImporter(company=company)
with open('coral_export.csv') as f:
    result = importer.import_file(f)
# result: {created: 45, skipped: 3, errors: []}
```

### 14.4 API Authentication for External Systems

Current session auth is not suitable for external integrations. Before any integration work:
1. Add `djangorestframework-simplejwt` to requirements
2. Add token endpoint: `POST /api/v1/auth/token/`
3. Document token refresh flow
4. Add per-integration API keys with scoped permissions

---

## 15. Appendices

### 15.1 Glossary

| Term | Definition |
|---|---|
| **Tenant** | A `Company` instance. All data is scoped to a tenant. |
| **Cost Engine** | `finance/services/cost_engine/` — calculates cost rates and order profitability. |
| **Cost Center** | Unit of cost allocation. Types: `VEHICLE` (per-vehicle costs) or `OVERHEAD` (shared costs). |
| **CostPosting** | Actual cost transaction: amount + period + CostCenter + CostItem. |
| **CostRateSnapshot** | Persisted historical cost rate for a CostCenter for a period. |
| **OrderCostBreakdown** | Persisted historical profitability for a TransportOrder for a period. |
| **tenant_context** | Python context manager that sets the active company for scoped queries. |
| **CompanyScopedManager** | Django manager that auto-filters by current tenant. Default manager for all tenant models. |
| **all_objects** | Bypass manager — returns unscoped queryset. **FORBIDDEN** in service/view code. |
| **Schema v1** | Current API response format: `{meta, snapshots, breakdowns, summary}`. |
| **MISSING_ACTIVITY** | Snapshot status when `total_units == 0` for KM/HOUR/TRIP basis. |
| **MISSING_RATE** | Breakdown status when no rate found for assigned vehicle's cost center. |
| **VehicleAsset** | **DELETED** — old polymorphic vehicle model. Removed in `core/migrations/0006`. |
| **operations.Vehicle** | Current unified vehicle model. Replaces VehicleAsset. |
| **legacy_services.py** | **DEPRECATED** — old CostCalculator. Use `finance/services/cost_engine/` instead. |
| **ΦΔΧ** | Φορτηγό Δημόσιας Χρήσης — Public freight truck. |
| **ΦΙΧ** | Φορτηγό Ιδιωτικής Χρήσης — Private freight truck. |
| **KTEO** | Κέντρο Τεχνικού Ελέγχου Οχημάτων — Vehicle technical inspection center. |
| **ΠΕΙ/CPC** | Πιστοποιητικό Επαγγελματικής Ικανότητας — Driver Certificate of Professional Competence. |

### 15.2 Key Invariants (Non-Negotiables)

1. **All service-layer code runs inside `tenant_context(company)`.**
2. **No `all_objects` usage in service or view code.** Enforced by `test_guardrails.py`.
3. **All monetary values use `Decimal`, never `float`.**
4. **Cost Engine results conform to Schema v1.** `schema_version` must be `1`.
5. **Snapshots use replace-existing semantics.** No duplicate historical records.
6. **`calculate_company_costs()` is the only public entry point** for cost calculations.
7. **`legacy_services.py` is deprecated.** No new code goes there.
8. **`operations.Vehicle` is the vehicle model.** `VehicleAsset` is deleted.
9. **All tests must pass before merging to main.** `python manage.py test` must return OK.
10. **DEBUG endpoint returns 404 in production.** Never expose unauthenticated endpoints.

### 15.3 File Structure Reference

```
TransCost/
├── core/                    # Tenant infrastructure
│   ├── models.py            # Company, Employee, DriverProfile
│   ├── mixins.py            # CompanyScopedManager, CompanyScopedModel
│   ├── tenant_context.py    # tenant_context() context manager
│   └── middleware.py        # Sets request.company
├── operations/              # Operational data
│   ├── models.py            # Vehicle (unified), FuelEntry, ServiceLog
│   └── signals.py           # Auto-odometer updates
├── finance/                 # Financial intelligence
│   ├── models.py            # CostCenter, CostItem, CostPosting, TransportOrder, etc.
│   ├── services/cost_engine/
│   │   ├── calculator.py    # Public entry point
│   │   ├── queries.py       # Data fetching
│   │   ├── aggregations.py  # Cost summation
│   │   ├── snapshots.py     # Rate calculation
│   │   └── persist.py       # Database persistence
│   ├── api/v1/
│   │   ├── views.py         # CostEngineRunView (DRF)
│   │   └── urls.py          # API URL routing
│   └── legacy_services.py   # DEPRECATED
├── web/                     # Frontend
│   ├── views.py             # HTMX views
│   └── templates/           # HTML templates
├── accounts/                # Authentication
│   └── models.py            # UserProfile (User → Company)
├── tests/                   # All tests
│   ├── test_tenant_isolation.py
│   ├── test_guardrails.py
│   ├── test_cost_engine*.py
│   └── test_cost_engine_api.py
└── docs/                    # Documentation
    ├── GREEKFLEET360_SINGLE_SOURCE.md  ← START HERE
    ├── MASTER_SYSTEM_ARCHITECTURE.md  ← This file
    ├── DOCS_INDEX.md
    └── cost_engine_schema_v1.md
```

---

*GreekFleet 360 — Master System Architecture*  
*Document Version: 1.0 | Last Updated: 2026-02-20*  
*Status: Authoritative Reference*
