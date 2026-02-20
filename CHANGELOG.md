# CHANGELOG - GreekFleet 360

> 📋 **Roadmap:** For the current development roadmap and future phases, see [`docs/MASTER_SYSTEM_ARCHITECTURE.md` § 11](docs/MASTER_SYSTEM_ARCHITECTURE.md#11-roadmap).

---

## Version 3.0.0 — Cost Engine API + Documentation System (February 20, 2026)

### Phase 9: REST API Layer ✅
- ✅ DRF API endpoint: `GET /api/v1/cost-engine/run/` (Staff/Superuser, session auth)
- ✅ Schema v1.0 responses (`meta`, `snapshots`, `breakdowns`, `summary`)
- ✅ Optional filters: `only_nonzero`, `include_breakdowns`, `company_id`
- ✅ DEV-only debug endpoint: `GET /finance/debug/cost-engine/`
- ✅ 11 comprehensive API tests (auth, permissions, validation, isolation)
- ✅ Demo data seeder: `python manage.py seed_cost_engine_demo`

### Documentation System ✅
- ✅ `docs/GREEKFLEET360_SINGLE_SOURCE.md` — Single entry point
- ✅ `docs/MASTER_SYSTEM_ARCHITECTURE.md` — Full 15-section architecture reference
- ✅ `docs/DOCS_INDEX.md` — Truth table, doc inventory, migration checklist
- ✅ `docs/cost_engine_schema_v1.md` — API contract for Cost Engine v1.0
- ✅ `STRATEGIC_ARCHITECTURE_AUDIT.md` — Full architectural audit

---

## Version 2.0.0 — Cost Engine v1.0 (February 19, 2026)

### Phase 8: Cost Engine v1.0 ✅
- ✅ Multi-layer cost calculation service (`finance/services/cost_engine/`)
  - `calculator.py` — Public entry point: `calculate_company_costs()`
  - `queries.py` — Tenant-scoped data fetching
  - `aggregations.py` — Cost summation by CostCenter
  - `snapshots.py` — Rate calculation and order breakdowns
  - `persist.py` — Atomic persistence with replace-existing semantics
- ✅ Basis units: KM, HOUR, TRIP, REVENUE
- ✅ Status rules: `OK`, `MISSING_ACTIVITY`, `MISSING_RATE`
- ✅ Historical snapshots: `CostRateSnapshot`, `OrderCostBreakdown`
- ✅ Batch command: `python manage.py calculate_costs`
- ✅ Tenant isolation enforced with guardrails (`test_guardrails.py`)
- ✅ 45+ tests passing (tenant isolation, cost calculations, persistence)

---

## Version 1.0.0 — Initial Release (February 2026)

### Phase 8.5: UI/UX & SaaS Admin Polish (February 13, 2026)
- ✅ **Frontend Complete Rewrite**
  - Data-driven UI με HTMX table
  - KPI Cards με real-time calculations
- ✅ **SaaS Admin Panel Restructuring**
  - Group 1: SaaS Platform (Companies, Users, Profiles)
  - Group 2: Master Data / Templates (Expense Families, Categories)
  - Group 3: Tenant Data (View Only)
- ✅ **CSRF Protection** — HTMX delete buttons fixed

### Phase 7: Infrastructure & Monitoring ✅
- ✅ Email Configuration (SMTP)
- ✅ Error Logging System (rotating file handler, 10MB, 5 backups)
- ✅ django-unfold Admin theme
- ✅ Data seeding: `seed_finance_data`

### Phase 6: Authentication & Security ✅
- ✅ Custom login/logout views
- ✅ Role-based navigation
- ✅ CSRF protection
- ✅ Company-specific data filtering

### Phase 5: Finance Module v2 - Hierarchical Refactor ✅
- ✅ **ExpenseFamily** model (top-level grouping)
- ✅ **ExpenseCategory** με FK σε Family
- ✅ **CompanyExpense** (renamed from RecurringExpense)
  - `start_date`, `end_date` για date ranges
  - `is_amortized` για daily cost allocation
  - `invoice_number` για tracking
- ✅ Smart allocation: `get_daily_cost()`, `get_period_cost()`

### Phase 4: Web Frontend ✅
- ✅ Dashboard με KPI cards
- ✅ Vehicle list με HTMX pagination
- ✅ Order management interface
- ✅ Tailwind CSS, Alpine.js, Leaflet.js maps

### Phase 3: Finance Module v1 ✅
- ✅ TransportOrder model (revenue tracking)
- ✅ CostCenter, CostItem, CostPosting models
- ✅ Admin panel με Unfold theme

### Phase 2: Operations Module ✅
- ✅ FuelEntry tracking με consumption analytics
- ✅ ServiceLog με maintenance history
- ✅ KTEO & Insurance expiry monitoring
- ✅ Vehicle health scoring system

### Phase 1: Core Infrastructure ✅
- ✅ Django 5.0.2 project initialization
- ✅ Multi-tenant architecture με Company model
- ✅ Unified Vehicle model (`operations.Vehicle`)
- ✅ DriverProfile με license tracking
- ✅ PostgreSQL/SQLite database support

---

## Technical Stack

**Backend:**
- Django 5.0.2
- Python 3.12
- Django REST Framework 3.16.1
- django-unfold

**Frontend:**
- Tailwind CSS
- HTMX
- Alpine.js
- Chart.js
- Leaflet.js

**Database:**
- SQLite (development)
- PostgreSQL (production-ready)

**Deployment:**
- WAMP64 (development)
- Gunicorn + Nginx (production)

---

## Migration Notes

### Finance Module Refactor (v1 → v2)
**Breaking Changes:**
- `RecurringExpense` → `CompanyExpense`
- `frequency` field removed
- Required fields: `start_date` (mandatory), `end_date` (optional)

### Vehicle Model Refactor
**Breaking Changes:**
- `VehicleAsset` (polymorphic) → `operations.Vehicle` (unified)
- `django-polymorphic` dependency removed
- Admin URL: `core/vehicleasset/` → `operations/vehicle/`
