# Cost & Revenue Architecture Audit — GreekFleet 360

**Date:** 2026-03-03  
**Purpose:** Complete mapping of cost/expense/revenue models and flows  
**Status:** Comprehensive analysis for future cost allocation redesign

---

## 1. COST & EXPENSE MODELS

### 1.1 ExpenseFamily
**Purpose:** Top-level grouping for expense categories (e.g., Buildings, Communication, HR, Taxes)

**Fields:**
- `name` - CharField(100, unique=True) - NOT NULL
- `icon` - CharField(50, default='folder') - NOT NULL
- `description` - TextField(blank=True) - NULLABLE
- `display_order` - IntegerField(default=0) - NOT NULL

**FK Relations:** None

**Constraints:** unique=True on `name`

**Used in:**
- Services: None directly
- Views: `web/views.py::finance_settings()` - groups categories by family
- Signals: None

---

### 1.2 ExpenseCategory
**Purpose:** Master data for expense categories; supports both system-wide defaults and tenant-specific custom categories

**Fields:**
- `family` - ForeignKey(ExpenseFamily, PROTECT) - NOT NULL
- `name` - CharField(100) - NOT NULL
- `description` - TextField(blank=True) - NULLABLE
- `is_system_default` - BooleanField(default=False) - NOT NULL
- `company` - ForeignKey(Company, CASCADE, null=True, blank=True) - NULLABLE

**FK Relations:**
- `family` → ExpenseFamily (PROTECT, related_name='categories')
- `company` → Company (CASCADE, related_name='custom_categories')

**Constraints:**
- unique_together: [['company', 'name']]
- System defaults: company=NULL
- Custom categories: company=<Company instance>

**Used in:**
- Services: None directly
- Views: `web/views.py::settings_hub()`, `category_create()`, `category_delete()`
- Forms: `web/forms.py::CompanyExpenseForm` - grouped choices by family
- Signals: None

---

### 1.3 CompanyExpense (alias: RecurringExpense)
**Purpose:** Company-level expenses with flexible allocation (direct to cost center or distributed)

**Fields:**
- `company` - ForeignKey(Company, CASCADE) - NOT NULL
- `category` - ForeignKey(ExpenseCategory, PROTECT) - NOT NULL
- `cost_center` - ForeignKey(CostCenter, SET_NULL, null=True, blank=True) - NULLABLE
- `employee` - ForeignKey(Employee, SET_NULL, null=True, blank=True) - NULLABLE
- `expense_type` - CharField(20, choices=['RECURRING', 'ONE_OFF'], default='RECURRING') - NOT NULL
- `periodicity` - CharField(20, choices=['MONTHLY', 'QUARTERLY', 'ANNUAL'], default='MONTHLY') - NOT NULL
- `amount` - DecimalField(10, 2, validators=[MinValueValidator(0.01)]) - NOT NULL
- `start_date` - DateField() - NOT NULL
- `end_date` - DateField(null=True, blank=True) - NULLABLE
- `is_amortized` - BooleanField(default=False) - NOT NULL
- `distribute_to_all_centers` - BooleanField(default=False) - NOT NULL
- `invoice_number` - CharField(50, blank=True) - NULLABLE
- `description` - TextField(blank=True) - NULLABLE
- `is_active` - BooleanField(default=True) - NOT NULL
- `created_at` - DateTimeField(auto_now_add=True) - NOT NULL
- `updated_at` - DateTimeField(auto_now=True) - NOT NULL

**FK Relations:**
- `company` → Company (CASCADE, related_name='expenses')
- `category` → ExpenseCategory (PROTECT, related_name='expenses')
- `cost_center` → CostCenter (SET_NULL, related_name='direct_expenses')
- `employee` → Employee (SET_NULL, related_name='expenses')

**Constraints:**
- unique_together: [['company', 'category', 'start_date']]

**Properties:**
- `monthly_impact` - Calculated monthly cost based on periodicity
- `annual_impact` - Calculated annual cost (monthly_impact * 12)

**Used in:**
- Services: None directly (legacy system)
- Views: `web/views.py::finance_settings()` - allocation calculation
- Forms: `web/forms.py::CompanyExpenseForm`
- Signals: None

---

### 1.4 CostCenter
**Purpose:** Cost allocation unit (vehicle-based, driver-based, or department-based)

**Fields:**
- `company` - ForeignKey(Company, CASCADE) - NOT NULL
- `name` - CharField(100) - NOT NULL
- `description` - TextField(blank=True) - NULLABLE
- `type` - CharField(20, choices=['VEHICLE', 'DRIVER', 'DEPARTMENT'], default='VEHICLE') - NOT NULL
- `vehicle` - ForeignKey(Vehicle, SET_NULL, null=True, blank=True) - NULLABLE
- `driver` - ForeignKey(Employee, SET_NULL, null=True, blank=True) - NULLABLE
- `is_active` - BooleanField(default=True) - NOT NULL
- `created_at` - DateTimeField(auto_now_add=True) - NOT NULL
- `updated_at` - DateTimeField(auto_now=True) - NOT NULL

**FK Relations:**
- `company` → Company (CASCADE, related_name='cost_centers')
- `vehicle` → operations.Vehicle (SET_NULL, related_name='cost_center')
- `driver` → core.Employee (SET_NULL, related_name='cost_center', limit_choices_to={'position__is_driver_role': True})

**Constraints:**
- unique_together: [['company', 'name']]

**Used in:**
- Services: `finance/services/cost_engine/aggregations.py` - aggregates postings by center
- Views: `web/views.py::finance_settings()` - allocation display
- Forms: `web/forms.py::CostCenterForm`
- Signals: `operations/signals.py::create_cost_center_for_vehicle` - auto-creates on Vehicle creation

---

### 1.5 CostItem
**Purpose:** Line items for cost postings (deprecated/legacy - not used in new cost engine)

**Fields:**
- `cost_center` - ForeignKey(CostCenter, CASCADE) - NOT NULL
- `category` - ForeignKey(ExpenseCategory, PROTECT) - NOT NULL
- `amount` - DecimalField(10, 2) - NOT NULL
- `date` - DateField() - NOT NULL
- `description` - TextField(blank=True) - NULLABLE
- `created_at` - DateTimeField(auto_now_add=True) - NOT NULL

**FK Relations:**
- `cost_center` → CostCenter (CASCADE, related_name='cost_items')
- `category` → ExpenseCategory (PROTECT, related_name='cost_items')

**Constraints:** None

**Used in:**
- Services: None (legacy)
- Views: None (legacy)
- Signals: None

**Status:** ⚠️ DEPRECATED - Not used in new cost engine

---

### 1.6 CostPosting
**Purpose:** Actual cost transactions linked to cost centers (legacy - not used in new cost engine)

**Fields:**
- `cost_center` - ForeignKey(CostCenter, CASCADE) - NOT NULL
- `category` - ForeignKey(ExpenseCategory, PROTECT) - NOT NULL
- `amount` - DecimalField(10, 2) - NOT NULL
- `date` - DateField() - NOT NULL
- `description` - TextField(blank=True) - NULLABLE
- `created_at` - DateTimeField(auto_now_add=True) - NOT NULL

**FK Relations:**
- `cost_center` → CostCenter (CASCADE, related_name='postings')
- `category` → ExpenseCategory (PROTECT, related_name='postings')

**Constraints:** None

**Used in:**
- Services: `finance/services/cost_engine/aggregations.py::aggregate_postings_by_cost_center()`
- Views: None directly
- Signals: None

**Status:** ⚠️ LEGACY - Used by old cost engine, being phased out

---

### 1.7 CostRateSnapshot
**Purpose:** Historical snapshot of calculated cost rates per cost center for a specific period

**Fields:**
- `company` - ForeignKey(Company, CASCADE) - NOT NULL
- `cost_center` - ForeignKey(CostCenter, CASCADE) - NOT NULL
- `period_start` - DateField() - NOT NULL
- `period_end` - DateField() - NOT NULL
- `basis_unit` - CharField(20, choices=['KM', 'HOUR', 'TRIP', 'REVENUE']) - NOT NULL
- `total_cost` - DecimalField(12, 2) - NOT NULL
- `total_activity` - DecimalField(12, 2) - NOT NULL
- `rate_per_unit` - DecimalField(12, 4) - NOT NULL
- `status` - CharField(20, choices=['OK', 'MISSING_ACTIVITY', 'MISSING_RATE']) - NOT NULL
- `snapshot_date` - DateTimeField(auto_now_add=True) - NOT NULL

**FK Relations:**
- `company` → Company (CASCADE, related_name='cost_snapshots')
- `cost_center` → CostCenter (CASCADE, related_name='snapshots')

**Constraints:**
- unique_together: [['cost_center', 'period_start', 'period_end', 'basis_unit']]

**Used in:**
- Services: 
  - `finance/services/cost_engine/persistence.py::CostEnginePersistence.persist()` - creates snapshots
  - `finance/services/analytics/history.py::get_cost_history()` - reads snapshots
- Views: None directly (accessed via API)
- Signals: None

**Status:** ✅ ACTIVE - Core of new cost engine persistence

---

### 1.8 OrderCostBreakdown
**Purpose:** Detailed cost breakdown for individual transport orders

**Fields:**
- `company` - ForeignKey(Company, CASCADE) - NOT NULL
- `order` - ForeignKey(TransportOrder, CASCADE) - NOT NULL
- `snapshot_date` - DateTimeField() - NOT NULL
- `basis_unit` - CharField(20, choices=['KM', 'HOUR', 'TRIP', 'REVENUE']) - NOT NULL
- `distance_km` - DecimalField(10, 2, null=True, blank=True) - NULLABLE
- `duration_hours` - DecimalField(10, 2, null=True, blank=True) - NULLABLE
- `revenue` - DecimalField(10, 2, null=True, blank=True) - NULLABLE
- `fixed_cost` - DecimalField(10, 2) - NOT NULL
- `variable_cost` - DecimalField(10, 2) - NOT NULL
- `direct_costs` - DecimalField(10, 2) - NOT NULL
- `total_cost` - DecimalField(10, 2) - NOT NULL
- `profit` - DecimalField(10, 2) - NOT NULL
- `profit_margin` - DecimalField(5, 2) - NOT NULL

**FK Relations:**
- `company` → Company (CASCADE, related_name='order_breakdowns')
- `order` → TransportOrder (CASCADE, related_name='cost_breakdowns')

**Constraints:**
- unique_together: [['order', 'snapshot_date', 'basis_unit']]

**Used in:**
- Services: `finance/services/cost_engine/persistence.py::CostEnginePersistence.persist()` - creates breakdowns
- Views: None directly (accessed via API)
- Signals: None

**Status:** ✅ ACTIVE - Stores trip-level profitability

---

## 2. REVENUE MODELS

### 2.1 TransportOrder
**Purpose:** Primary revenue-generating entity - represents a transport job/trip

**Revenue Fields:**
- `agreed_price` - DecimalField(10, 2) - NOT NULL - **PRIMARY REVENUE FIELD**
- `distance_km` - DecimalField(10, 2, null=True, blank=True) - NULLABLE
- `duration_hours` - DecimalField(10, 2, null=True, blank=True) - NULLABLE
- `tolls_cost` - DecimalField(10, 2, default=0) - NOT NULL
- `ferry_cost` - DecimalField(10, 2, default=0) - NOT NULL

**FK Relations:**
- `company` → Company (CASCADE) - NOT NULL
- `assigned_vehicle` → operations.Vehicle (SET_NULL, null=True, blank=True) - NULLABLE
- `assigned_driver` → core.Employee (SET_NULL, null=True, blank=True) - NULLABLE

**Constraints:**
- No unique constraints (allows duplicate orders)

**Currency:** EUR (€) only - hardcoded, no multi-currency support

**Connection to Cost System:**
- Vehicle → CostCenter (via `assigned_vehicle.cost_center`)
- Driver → CostCenter (via driver-based cost centers)
- Used in: `finance/services/cost_engine/activity.py::aggregate_activity_by_cost_center()`

**Used in:**
- Services: Cost engine activity aggregation, profitability calculation
- Views: `web/views.py::order_list()`, `order_detail()`, `dashboard_home()`
- Signals: None

---

## 3. COST ALLOCATION SERVICES

### 3.1 calculate_company_costs()
**Location:** `finance/services/cost_engine/calculator.py`

**Purpose:** Main orchestrator for cost calculation pipeline

**Inputs:**
- `company`: Company instance
- `period_start`: date
- `period_end`: date

**Outputs:** Dict with schema v1:
```python
{
    "meta": {...},
    "snapshots": [...],  # CostCenter rates
    "breakdowns": [...], # Order profitability
    "summary": {...}
}
```

**Writes to DB:** NO (read-only)

**Idempotent:** YES

**Models Touched:** CostCenter, CostPosting, TransportOrder (read-only)

---

### 3.2 aggregate_postings_by_cost_center()
**Location:** `finance/services/cost_engine/aggregations.py`

**Purpose:** Sum all CostPosting amounts per cost center for a period

**Inputs:**
- `company`: Company
- `period_start`: date
- `period_end`: date

**Outputs:** `{cost_center_id: Decimal(total_amount)}`

**Writes to DB:** NO

**Idempotent:** YES

**Models Touched:** CostPosting (read-only)

---

### 3.3 aggregate_activity_by_cost_center()
**Location:** `finance/services/cost_engine/activity.py`

**Purpose:** Aggregate TransportOrder activity (km, hours, trips, revenue) per cost center

**Inputs:**
- `company`: Company
- `period_start`: date
- `period_end`: date
- `basis_unit`: 'KM' | 'HOUR' | 'TRIP' | 'REVENUE'

**Outputs:** `{cost_center_id: Decimal(total_activity)}`

**Writes to DB:** NO

**Idempotent:** YES

**Models Touched:** TransportOrder, Vehicle (read-only)

**Logic:**
- Groups orders by `assigned_vehicle.cost_center`
- Sums based on basis_unit (distance_km, duration_hours, count, agreed_price)

---

### 3.4 calculate_rates()
**Location:** `finance/services/cost_engine/rates.py`

**Purpose:** Calculate cost per unit (€/km, €/hour, €/trip, €/€revenue) for each cost center

**Inputs:**
- `cost_totals`: dict from aggregate_postings_by_cost_center()
- `activity_totals`: dict from aggregate_activity_by_cost_center()
- `basis_unit`: str

**Outputs:** List of dicts:
```python
[{
    "cost_center_id": int,
    "total_cost": Decimal,
    "total_activity": Decimal,
    "rate_per_unit": Decimal,
    "status": "OK" | "MISSING_ACTIVITY" | "MISSING_RATE"
}]
```

**Writes to DB:** NO

**Idempotent:** YES

**Models Touched:** None (pure calculation)

---

### 3.5 calculate_order_costs()
**Location:** `finance/services/cost_engine/profitability.py`

**Purpose:** Calculate cost breakdown and profitability for each TransportOrder

**Inputs:**
- `company`: Company
- `period_start`: date
- `period_end`: date
- `rates`: list from calculate_rates()
- `basis_unit`: str

**Outputs:** List of dicts:
```python
[{
    "order_id": int,
    "distance_km": Decimal,
    "duration_hours": Decimal,
    "revenue": Decimal,
    "fixed_cost": Decimal,
    "variable_cost": Decimal,
    "direct_costs": Decimal,
    "total_cost": Decimal,
    "profit": Decimal,
    "profit_margin": Decimal
}]
```

**Writes to DB:** NO

**Idempotent:** YES

**Models Touched:** TransportOrder (read-only)

---

### 3.6 CostEnginePersistence
**Location:** `finance/services/cost_engine/persistence.py`

**Purpose:** Persist cost calculation results to database (snapshots + breakdowns)

**Methods:**
- `persist(calculation_result, company, period_start, period_end, basis_unit)`

**Inputs:** Output from `calculate_company_costs()`

**Outputs:** None (writes to DB)

**Writes to DB:** YES
- Creates/updates `CostRateSnapshot` records
- Creates/updates `OrderCostBreakdown` records

**Idempotent:** YES (uses update_or_create with unique_together constraints)

**Models Touched:**
- CostRateSnapshot (write)
- OrderCostBreakdown (write)

---

### 3.7 get_cost_history()
**Location:** `finance/services/analytics/history.py`

**Purpose:** Read-only service to query persisted cost snapshots

**Inputs:**
- `company`: Company
- `period_start`: date
- `period_end`: date
- `filters`: dict (cost_center_id, basis_unit, only_nonzero, include_breakdowns, limit)

**Outputs:** Dict with snapshots and optional breakdowns

**Writes to DB:** NO

**Idempotent:** YES

**Models Touched:** CostRateSnapshot, OrderCostBreakdown (read-only)

---

### 3.8 KPI Services
**Location:** `finance/services/analytics/kpis.py`

**Methods:**
- `get_company_summary()` - Aggregate KPIs from snapshots
- `get_cost_structure()` - Cost distribution by cost center
- `get_trend()` - Time-series buckets (month/week)

**Writes to DB:** NO

**Idempotent:** YES

**Models Touched:** CostRateSnapshot (read-only)

---

## 4. REVENUE STRUCTURE

### 4.1 TransportOrder (Primary Revenue Model)
**Location:** `finance/models.py`

**Revenue Field:** `agreed_price` - DecimalField(10, 2) - **PRIMARY REVENUE**

**Currency:** EUR (€) only - no multi-currency support

**Relations:**
- `company` → Company (CASCADE) - Tenant isolation
- `assigned_vehicle` → operations.Vehicle (SET_NULL, nullable)
- `assigned_driver` → core.Employee (SET_NULL, nullable)

**Connection to Cost System:**
- Vehicle → CostCenter (via `assigned_vehicle.cost_center`)
- Driver → CostCenter (via driver-based cost centers)
- Activity aggregation: `aggregate_activity_by_cost_center()` groups orders by vehicle's cost center

**Status Workflow:**
- PENDING → IN_PROGRESS → COMPLETED → INVOICED → CANCELLED

**Revenue Recognition:**
- Dashboard counts: status IN ['COMPLETED', 'INVOICED']
- Cost engine: includes all orders in period (regardless of status)

---

## 5. CURRENT COST FLOW

### 5.1 Expense Flow
```
CompanyExpense (user input)
    ↓
    ├─ Direct Assignment → CostCenter (via cost_center FK)
    │   └─ Aggregated in finance_settings view
    │
    └─ Distributed → ALL Active CostCenters (via distribute_to_all_centers=True)
        └─ Split equally: expense.monthly_impact / active_center_count
```

**NOT USED BY COST ENGINE** - This is UI-only allocation for display purposes

---

### 5.2 Cost Engine Flow (New System)
```
1. CostPosting (legacy data)
    ↓
2. aggregate_postings_by_cost_center() → {center_id: total_cost}
    ↓
3. aggregate_activity_by_cost_center() → {center_id: total_activity}
    ↓
4. calculate_rates() → [{center_id, rate_per_unit, status}]
    ↓
5. calculate_order_costs() → [{order_id, profit, profit_margin}]
    ↓
6. CostEnginePersistence.persist() → Writes to:
    - CostRateSnapshot (per cost center)
    - OrderCostBreakdown (per order)
```

---

### 5.3 Revenue Flow
```
TransportOrder (user creates order)
    ↓
    ├─ agreed_price = REVENUE
    ├─ assigned_vehicle → links to CostCenter
    ├─ distance_km, duration_hours → activity metrics
    └─ tolls_cost, ferry_cost → direct costs
    ↓
Cost Engine:
    - Groups orders by vehicle.cost_center
    - Calculates profit = revenue - total_cost
    - Calculates profit_margin = (profit / revenue) * 100
    ↓
OrderCostBreakdown (persisted profitability)
```

---

## 6. MANAGEMENT COMMANDS & TRIGGERS

### 6.1 calculate_costs Command
**Location:** `finance/management/commands/calculate_costs.py`

**Trigger:** Manual execution
```bash
python manage.py calculate_costs --company "Company Name" --period 2026-03
```

**Options:**
- `--company`: Company name or ID (required)
- `--period`: YYYY-MM or "current" (default: current month)
- `--basis`: KM/HOUR/TRIP/REVENUE (default: KM)
- `--dry-run`: Calculate without saving

**Process:**
1. Calls `calculate_company_costs()`
2. If not dry-run: calls `CostEnginePersistence.persist()`

---

### 6.2 Auto-Creation Signals

**Signal:** `create_cost_center_for_vehicle`  
**Location:** `operations/signals.py`  
**Trigger:** `post_save` on `operations.Vehicle` (created=True)

**Action:**
```python
CostCenter.objects.get_or_create(
    company=vehicle.company,
    name=f"Vehicle {vehicle.license_plate}",
    defaults={
        'type': 'VEHICLE',
        'vehicle': vehicle,
        'is_active': True
    }
)
```

**Status:** ✅ ACTIVE - Auto-creates cost center for every new vehicle

---

## 7. RECONCILIATION & AGGREGATION

### 7.1 Total Company Cost
**Current Implementation:** None directly

**Available Queries:**
```python
# Option 1: Sum all CompanyExpense annual_impact
total_annual = sum([exp.annual_impact for exp in CompanyExpense.objects.filter(company=company, is_active=True)])

# Option 2: Sum all CostRateSnapshot total_cost for a period
total_cost = CostRateSnapshot.objects.filter(
    company=company,
    period_start=start,
    period_end=end,
    basis_unit='KM'
).aggregate(Sum('total_cost'))['total_cost__sum']

# Option 3: Sum all CostPosting amounts for a period
total_cost = CostPosting.objects.filter(
    cost_center__company=company,
    date__range=[start, end]
).aggregate(Sum('amount'))['amount__sum']
```

**Issue:** No single source of truth for "total company cost"

---

### 7.2 Monthly Closing Logic
**Current Implementation:** None

**What Exists:**
- `web/views.py::finance_settings()` calculates monthly breakdown for display
- No formal "close month" process
- No period locking
- No audit trail for cost changes

---

### 7.3 Reconciliation
**Current Implementation:** None

**Missing:**
- No validation that `Sum(CompanyExpense) == Sum(CostPosting)`
- No check that `Sum(CostRateSnapshot.total_cost) == Sum(CostPosting)`
- No reconciliation report

---

## 8. DATA RISKS & WEAKNESSES

### 8.1 Double Counting Risks

**Risk 1: CompanyExpense vs CostPosting**
- `CompanyExpense` is user-facing expense management
- `CostPosting` is used by cost engine
- **NO LINK** between them - they are separate systems!
- **Risk:** User enters expense in CompanyExpense, but it's not in CostPosting → cost engine misses it

**Risk 2: Distributed Expenses**
- `distribute_to_all_centers=True` splits cost across centers
- If a new cost center is added mid-period, allocation changes retroactively
- **Risk:** Historical allocations are not locked

**Risk 3: Order Activity**
- Orders grouped by `assigned_vehicle.cost_center`
- If vehicle changes cost center mid-period, activity attribution changes
- **Risk:** No period locking for vehicle-center assignments

---

### 8.2 Tenant Isolation Risks

**✅ SAFE:**
- All models have `company` FK with CASCADE
- All queries filter by `company`
- Middleware enforces `request.company`

**⚠️ POTENTIAL ISSUES:**
- `ExpenseCategory` with `company=NULL` (system defaults) - shared across tenants (by design)
- No row-level security in database (relies on application-level filtering)

---

### 8.3 Missing Constraints

**CompanyExpense:**
- No check that `end_date >= start_date`
- No check that `cost_center.company == company` (enforced in form, not model)

**CostCenter:**
- No check that `vehicle.company == company` (enforced in form, not model)
- No check that `driver.company == company` (enforced in form, not model)

**TransportOrder:**
- No check that `assigned_vehicle.company == company` (enforced in form, not model)
- No check that `assigned_driver.company == company` (enforced in form, not model)

**CostRateSnapshot:**
- No check that `cost_center.company == company` (enforced in service, not model)

---

## 9. MISSING LINKS

### 9.1 CompanyExpense → CostPosting
**Status:** NO LINK

**Current State:**
- `CompanyExpense` is UI-facing expense management
- `CostPosting` is used by cost engine
- They are **separate systems**

**Impact:**
- Cost engine doesn't see CompanyExpense data
- CompanyExpense is display-only (not used in calculations)

**Needed:**
- Sync mechanism or migration to use CompanyExpense as source of truth

---

### 9.2 Vehicle Fixed Costs → CostPosting
**Status:** NO AUTOMATIC SYNC

**Current State:**
- `operations.Vehicle` has cost-related fields (purchase_value, available_hours_per_year)
- These are used to calculate `fixed_cost_per_hour` property
- But this is NOT automatically posted to CostPosting

**Impact:**
- Vehicle depreciation/fixed costs not in cost engine unless manually posted

---

### 9.3 Employee Costs → CostPosting
**Status:** NO AUTOMATIC SYNC

**Current State:**
- `core.Employee` has salary fields (monthly_gross_salary, employer_contributions_rate)
- Property `total_annual_cost` calculates full cost
- But this is NOT automatically posted to CostPosting

**Impact:**
- Driver salaries not in cost engine unless manually posted

---

## 10. ARCHITECTURAL OBSERVATIONS

### 10.1 Dual Cost Systems
**Observation:** Two parallel cost tracking systems exist:

**System A: CompanyExpense (UI-facing)**
- User-friendly expense management
- Flexible allocation (direct or distributed)
- Used in `finance_settings` view for display
- NOT used by cost engine

**System B: CostPosting (Engine-facing)**
- Legacy transaction-based system
- Used by cost engine for calculations
- NOT exposed in UI

**Implication:** Data entry disconnect - users enter CompanyExpense but cost engine reads CostPosting

---

### 10.2 Activity Attribution
**Observation:** Orders attributed to cost centers via `assigned_vehicle.cost_center`

**Strengths:**
- Simple, direct relationship
- Works well for vehicle-centric operations

**Weaknesses:**
- If vehicle changes cost center, historical attribution changes
- No period locking
- Driver-based cost centers not automatically linked to orders

---

### 10.3 Rate Calculation Basis
**Observation:** Supports 4 basis units (KM, HOUR, TRIP, REVENUE)

**Strengths:**
- Flexible for different business models
- Allows comparison across basis units

**Weaknesses:**
- No guidance on which basis to use
- No validation that basis matches company.transport_type
- REVENUE basis creates circular dependency (cost per € of revenue)

---

### 10.4 Snapshot Persistence
**Observation:** CostRateSnapshot and OrderCostBreakdown store historical calculations

**Strengths:**
- Immutable audit trail
- Fast historical queries
- No need to recalculate

**Weaknesses:**
- No versioning (if calculation logic changes, old snapshots are incompatible)
- No schema_version in OrderCostBreakdown (only in CostRateSnapshot meta)
- No cleanup/archival strategy

---

### 10.5 Profitability Calculation
**Observation:** Two profitability calculation paths exist:

**Path A: Legacy (web/views.py)**
```python
from finance.legacy_services import CostCalculator
calculator = CostCalculator(vehicle, distance, duration, tolls, ferry)
result = calculator.calculate_trip_profitability(agreed_price)
```

**Path B: New Cost Engine**
```python
from finance.services.cost_engine import calculate_company_costs
result = calculate_company_costs(company, start, end)
# Returns breakdowns with profit/profit_margin per order
```

**Implication:** Inconsistency - dashboard uses legacy, API uses new engine

---

## 11. CURRENT COST FLOW DIAGRAM

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER INPUT LAYER                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  CompanyExpense                    TransportOrder                │
│  (UI expense mgmt)                 (revenue + activity)          │
│         │                                  │                     │
│         │                                  │                     │
│         ↓                                  ↓                     │
│  ┌──────────────┐                 ┌──────────────┐              │
│  │ CostCenter   │←────────────────│ Vehicle      │              │
│  │ (allocation  │                 │ (activity    │              │
│  │  unit)       │                 │  source)     │              │
│  └──────────────┘                 └──────────────┘              │
│         │                                  │                     │
└─────────┼──────────────────────────────────┼─────────────────────┘
          │                                  │
          │                                  │
┌─────────┼──────────────────────────────────┼─────────────────────┐
│         │         CALCULATION LAYER        │                     │
├─────────┼──────────────────────────────────┼─────────────────────┤
│         │                                  │                     │
│         ↓                                  ↓                     │
│  ┌──────────────┐                 ┌──────────────┐              │
│  │ CostPosting  │                 │ Activity     │              │
│  │ (legacy      │                 │ Aggregation  │              │
│  │  source)     │                 │ (km/hours)   │              │
│  └──────────────┘                 └──────────────┘              │
│         │                                  │                     │
│         └──────────┬───────────────────────┘                     │
│                    ↓                                             │
│           ┌─────────────────┐                                    │
│           │ calculate_rates │                                    │
│           │ (€/km, €/hour)  │                                    │
│           └─────────────────┘                                    │
│                    │                                             │
│                    ↓                                             │
│           ┌─────────────────┐                                    │
│           │ calculate_order │                                    │
│           │ _costs()        │                                    │
│           │ (profit/margin) │                                    │
│           └─────────────────┘                                    │
│                    │                                             │
└────────────────────┼─────────────────────────────────────────────┘
                     │
                     │
┌────────────────────┼─────────────────────────────────────────────┐
│                    │      PERSISTENCE LAYER                      │
├────────────────────┼─────────────────────────────────────────────┤
│                    ↓                                             │
│         ┌──────────────────────┐                                 │
│         │ CostRateSnapshot     │                                 │
│         │ (per cost center)    │                                 │
│         └──────────────────────┘                                 │
│                    │                                             │
│                    ↓                                             │
│         ┌──────────────────────┐                                 │
│         │ OrderCostBreakdown   │                                 │
│         │ (per order)          │                                 │
│         └──────────────────────┘                                 │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## 12. KEY FINDINGS

### 12.1 Disconnected Systems
- **CompanyExpense** (UI) and **CostPosting** (Engine) are NOT linked
- Users enter expenses in CompanyExpense but cost engine reads CostPosting
- **Impact:** Manual data entry required in both systems OR cost engine misses expenses

### 12.2 No Automatic Cost Posting
- Vehicle fixed costs (depreciation, insurance) are NOT auto-posted
- Employee salaries are NOT auto-posted
- Fuel entries are NOT auto-posted to CostPosting
- **Impact:** Cost engine only sees manually created CostPosting records

### 12.3 Legacy vs New Profitability
- Dashboard uses `legacy_services.CostCalculator` (deprecated)
- API uses new cost engine
- **Impact:** Inconsistent profitability calculations

### 12.4 No Period Locking
- Cost center assignments can change retroactively
- Expense allocations recalculate if centers added/removed
- **Impact:** Historical data is mutable

### 12.5 No Reconciliation
- No validation that expenses sum correctly
- No check that all orders have cost breakdowns
- No monthly closing process
- **Impact:** Data integrity not guaranteed

---

## 13. NEXT STEPS (Recommendations)

### Priority 1: Unify Cost Systems
- Decide: CompanyExpense OR CostPosting as single source of truth
- Build sync mechanism or migration path
- Deprecate the unused system

### Priority 2: Auto-Posting
- Create signals to auto-post:
  - Vehicle fixed costs → CostPosting
  - Employee salaries → CostPosting
  - Fuel entries → CostPosting
- Ensure idempotency

### Priority 3: Period Locking
- Add `is_locked` field to periods
- Prevent changes to locked periods
- Lock on month close

### Priority 4: Reconciliation
- Build reconciliation report
- Add validation checks
- Create monthly closing workflow

### Priority 5: Deprecate Legacy
- Replace `legacy_services.CostCalculator` in dashboard
- Use new cost engine everywhere
- Remove legacy code

---

**End of Audit**
