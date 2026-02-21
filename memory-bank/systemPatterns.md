# System Patterns — GreekFleet 360

## Αρχιτεκτονική Επισκόπηση

```
Web Layer (HTMX + Alpine.js + Tailwind)
    ↓
API Layer (DRF + JWT)
    ↓
Service Layer (Cost Engine, Analytics)
    ↓
Domain Layer (Models: core / operations / finance / accounts)
    ↓
Data Layer (SQLite dev / PostgreSQL prod)
```

## Domain Boundaries (Bounded Contexts)

### `core/` — Tenant Infrastructure
- **Company**: Tenant root. Κάθε data model έχει `company` FK.
- **Employee**: Προσωπικό (μισθός, εισφορές, ώρες/έτος)
- **DriverProfile**: Οδηγοί (άδεια, ΠΕΙ, ιατρική κάρτα, Σησάμι)
- **EmployeePosition**: Θέσεις εργασίας
- `mixins.py` → `CompanyScopedManager`, `CompanyScopedModel`
- `tenant_context.py` → `tenant_context()` context manager
- `middleware.py` → Sets `request.company` from UserProfile

### `operations/` — Operational Data
- **Vehicle**: Unified model (αντικατέστησε polymorphic VehicleAsset)
  - VehicleClass, BodyType, FuelType, EmissionClass, Status
  - Αυτόματη απόσβεση 16% ετησίως (acquisition_date + purchase_value)
  - Properties: `current_accounting_value`, `annual_depreciation`, `fixed_cost_per_hour`
- **FuelEntry**: Καταγραφή καυσίμου (full-tank method για κατανάλωση)
- **ServiceLog**: Συντήρηση/επισκευές
- **IncidentReport**: Ατυχήματα, κλήσεις, βλάβες
- `signals.py` → Auto-odometer updates

### `finance/` — Financial Intelligence
**Master Data (cross-tenant):**
- **ExpenseFamily**: Top-level grouping (Buildings, HR, Communication...)
- **ExpenseCategory**: Κατηγορίες εξόδων (system defaults + tenant custom)

**Tenant Data:**
- **CostCenter**: Κέντρα κόστους (VEHICLE, DRIVER, OVERHEAD, ROUTE, OTHER)
  - Σύνδεση με Vehicle ή DriverProfile για αυτόματη κατανομή
- **CompanyExpense**: Έξοδα εταιρείας (RECURRING/ONE_OFF, amortization)
  - Properties: `monthly_impact`, `annual_impact`, `get_daily_cost()`, `get_period_cost()`
- **TransportOrder**: Εντολές μεταφοράς (revenue side)
- **CostItem**: Τύποι κόστους (FIXED/VARIABLE/INDIRECT)
- **CostPosting**: Πραγματικές συναλλαγές κόστους

**Analytics Models:**
- **CostRateSnapshot**: Ιστορικές τιμές κόστους ανά CostCenter/period
- **OrderCostBreakdown**: Ιστορική κερδοφορία ανά TransportOrder/period

**Cost Engine Service** (`finance/services/cost_engine/`):
- `calculator.py` → `calculate_company_costs()` — Public entry point
- `queries.py` → Tenant-scoped data fetching
- `aggregations.py` → Cost summation by CostCenter
- `snapshots.py` → Rate calculation, order breakdowns
- `persist.py` → Atomic persistence (replace-existing semantics)

**Analytics Service** (`finance/services/analytics/`):
- `kpis.py` → `get_company_summary()`, `get_cost_structure()`, `get_trend()`
- `history.py` → `get_cost_engine_history()`

**API** (`finance/api/v1/`):
- `views.py` → `CostEngineRunView`, `CostEngineHistoryView`
- `kpi_views.py` → `KPISummaryView`, `KPICostStructureView`, `KPITrendView`
- `auth_views.py` → `LogoutView` (JWT blacklist)
- `auth_urls.py` → token/, refresh/, logout/
- `permissions.py` → `AnalyticsPermission` (RBAC scaffold)

### `web/` — Frontend
- `views.py` → HTMX views (dashboard, vehicles, orders, finance, fleet, settings)
- `forms.py` → TailwindFormMixin + all forms
- `urls.py` → URL routing
- `templates/` → HTML templates

### `accounts/` — Authentication
- **UserProfile**: Links User → Company (role: ADMIN/MANAGER/ACCOUNTANT/VIEWER)
- `views.py` → login, logout, signup (creates User + Company + UserProfile)

## Multi-Tenant Isolation Pattern

### CompanyScopedManager
```python
# Κάθε tenant model έχει:
objects = CompanyScopedManager()    # Scoped (default)
all_objects = models.Manager()      # Unscoped (FORBIDDEN σε services/views)
```

### tenant_context
```python
# ΥΠΟΧΡΕΩΤΙΚΟ για όλες τις service calls:
with tenant_context(company):
    result = calculate_company_costs(company, start, end)
```

### Guardrails
- `tests/test_guardrails.py` σκανάρει όλα τα .py files για `\.all_objects\.`
- Επιτρεπόμενα: admin.py, tests/, migrations/, core/mixins.py
- ΑΠΑΓΟΡΕΥΜΕΝΑ: finance/services/, web/views.py, οποιοδήποτε νέο service/view

## API Patterns

### Authentication
- JWT (Bearer token) για API clients
- Session (cookie) για web UI
- Και τα δύο υποστηρίζονται ταυτόχρονα

### Endpoints
```
POST /api/v1/auth/token/          → Obtain access + refresh tokens
POST /api/v1/auth/refresh/        → Refresh access token
POST /api/v1/auth/logout/         → Blacklist refresh token

GET  /api/v1/cost-engine/run/     → Runtime cost calculation
GET  /api/v1/cost-engine/history/ → Persisted analytics
GET  /api/v1/kpis/company/summary/       → KPI summary
GET  /api/v1/kpis/company/cost-structure/ → Cost distribution
GET  /api/v1/kpis/company/trend/         → Time-series trend

GET  /finance/debug/cost-engine/  → DEV ONLY (404 σε production)
```

### Schema Versioning
- Όλα τα responses περιέχουν `schema_version: 1`
- Format: `{meta, snapshots, breakdowns, summary}`

## Form Patterns

### TailwindFormMixin
- Εφαρμόζει Tailwind CSS classes αυτόματα σε όλα τα fields
- Χρησιμοποιείται από όλες τις forms

### Company-Scoped Forms
- `CompanyExpenseForm(company=company)` → φιλτράρει cost_centers, employees
- `EmployeeForm(company=company)` → φιλτράρει vehicles
- `VehicleForm(company=company)` → company-aware

## Template Patterns

### HTMX Modals
- GET request → επιστρέφει partial template (modal form)
- POST request → επεξεργασία + redirect ή error modal
- DELETE → `HttpResponse('', status=200)` για HTMX row removal

### Partials
- `partials/expense_form_modal.html`
- `partials/cost_center_form_modal.html`
- `partials/employee_form_modal.html`
- `partials/vehicle_cards.html` (HTMX pagination)

## Cost Engine Patterns

### Basis Units
- `KM` → Χιλιόμετρα (vehicle cost centers)
- `HOUR` → Ώρες (time-based)
- `TRIP` → Δρομολόγια (per-trip)
- `REVENUE` → Έσοδα (overhead allocation)

### Status Rules
- `OK` → Κανονικός υπολογισμός
- `MISSING_ACTIVITY` → total_units == 0
- `MISSING_RATE` → Δεν βρέθηκε rate για το vehicle's cost center

### Persistence Semantics
- Replace-existing: Διαγράφει παλιά snapshots πριν εισάγει νέα
- Atomic: `transaction.atomic()`
- Idempotent: Ίδιο αποτέλεσμα αν τρέξει δύο φορές

## Decimal Precision Rule
```python
# ΠΑΝΤΑ Decimal, ΠΟΤΕ float:
from decimal import Decimal
amount = Decimal('0.00')
rate = Decimal('0.000000')
```

## Vehicle Model Key Properties
```python
vehicle.current_accounting_value  # Λογιστική αξία (16% ετήσια απόσβεση)
vehicle.annual_depreciation       # Ετήσια απόσβεση
vehicle.fixed_cost_per_hour       # Σταθερό κόστος/ώρα
vehicle.payload_capacity_kg       # Ωφέλιμο φορτίο (gross - unladen)
vehicle.cargo_volume_m3           # Όγκος χώρου φορτίου
```

## Deprecated / Removed
- `VehicleAsset` (polymorphic) → **ΔΙΑΓΡΑΦΗΚΕ** (core/migrations/0006)
- `RecurringExpense` → alias για `CompanyExpense` (backward compat)
- `legacy_services.py` → **DEPRECATED** (CostCalculator, FreightCostEngine)
- `finance/services.py` → **ΔΕΝ ΥΠΑΡΧΕΙ** (αντικαταστάθηκε από services/)
