# CHANGELOG - GreekFleet 360

## Version 1.0.0 - Initial Release (February 2026)

### Phase 1: Core Infrastructure
- ✅ Django 5.0.2 project initialization
- ✅ Multi-tenant architecture με Company model
- ✅ Polymorphic VehicleAsset system (Truck, Van, Trailer)
- ✅ DriverProfile με license tracking
- ✅ PostgreSQL/SQLite database support

### Phase 2: Operations Module
- ✅ FuelEntry tracking με consumption analytics
- ✅ ServiceLog με maintenance history
- ✅ KTEO & Insurance expiry monitoring
- ✅ Vehicle health scoring system

### Phase 3: Finance Module v1
- ✅ TransportOrder model (revenue tracking)
- ✅ CostCalculator service (trip profitability)
- ✅ RecurringExpense με frequency-based costing
- ✅ Admin panel με Unfold theme

### Phase 4: Web Frontend
- ✅ Dashboard με KPI cards
- ✅ Vehicle list με HTMX pagination
- ✅ Order management interface
- ✅ Tailwind CSS styling
- ✅ Alpine.js για interactivity
- ✅ Leaflet.js maps integration

### Phase 5: Finance Module v2 - Hierarchical Refactor
- ✅ **ExpenseFamily** model (top-level grouping)
- ✅ **ExpenseCategory** με FK σε Family
- ✅ **CompanyExpense** (renamed from RecurringExpense)
  - Αφαιρέθηκε το απλοϊκό `frequency` field
  - Προστέθηκαν `start_date`, `end_date` για date ranges
  - Προστέθηκε `is_amortized` για daily cost allocation
  - Προστέθηκε `invoice_number` για tracking
- ✅ Smart allocation methods: `get_daily_cost()`, `get_period_cost()`
- ✅ HTMX modals για expense management
- ✅ Tabs UI (Entry vs Reports)

### Phase 6: Authentication & Security
- ✅ Custom login/logout views
- ✅ Role-based navigation (Admin Panel για superusers μόνο)
- ✅ CSRF protection
- ✅ Company-specific data filtering

### Phase 7: Infrastructure & Monitoring
- ✅ **Email Configuration**
  - SMTP: smtp.thessdrive.gr
  - From: info@thessdrive.gr
  - Admin notifications enabled
- ✅ **Error Logging System**
  - Rotating file handler (10MB, 5 backups)
  - logs/system_errors.log
  - Email notifications σε admins (όταν DEBUG=False)
- ✅ **django-unfold** Admin theme
- ✅ Data seeding commands
  - `seed_finance_data`: Default categories & cost centers

---

### Phase 8.5: UI/UX & SaaS Admin Polish (February 13, 2026)
- ✅ **Frontend Complete Rewrite**
  - Διαγράφηκαν όλα τα hardcoded input fields
  - Data-driven UI με HTMX table
  - Columns: Οικογένεια (με icon) | Κατηγορία | Κέντρο Κόστους | Ποσό | Διάρκεια | Ενέργειες
  - KPI Cards με real-time calculations
- ✅ **SaaS Admin Panel Restructuring**
  - **Group 1: SaaS Platform** (Companies, Users, Profiles)
  - **Group 2: Master Data / Templates** (Expense Families, Categories)
  - **Group 3: Tenant Data (View Only)** (Cost Centers, Expenses, Orders, Vehicles, etc.)
  - Ξεκάθαρος διαχωρισμός: Superadmin διαχειρίζεται templates, όχι tenant data
- ✅ **Form Enhancements**
  - Category dropdown με optgroup (grouped by Family)
  - Cost Center filtering ανά company
  - Tailwind CSS styling
- ✅ **CSRF Protection**
  - HTMX delete buttons με `hx-headers='{"X-CSRFToken": "{{ csrf_token }}"}'`
  - Διόρθωση 403 Forbidden errors

---

## Upcoming Features (Roadmap)

### Phase 8: Advanced Finance
- [ ] Date range picker για period-based reporting
- [ ] ExpenseService με smart allocation logic
- [ ] Budget vs Actual tracking
- [ ] Multi-currency support

### Phase 9: Email Verification
- [ ] Signup email verification
- [ ] Password reset via email
- [ ] Welcome emails

### Phase 10: Internationalization
- [ ] i18n setup (Greek/English)
- [ ] Translation files
- [ ] django-rosetta integration

### Phase 11: Advanced Reporting
- [ ] PDF invoice generation
- [ ] Excel exports
- [ ] Custom dashboards per role

---

## Technical Stack

**Backend:**
- Django 5.0.2
- Python 3.12
- django-polymorphic
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

**Migration Strategy:**
1. Created ExpenseFamily with nullable FK
2. Migrated data
3. Created default "Γενικά Έξοδα" family
4. Assigned all categories to default family
5. Made FK non-nullable

**Data Preservation:**
- All existing expenses preserved
- Backward compatibility alias maintained
