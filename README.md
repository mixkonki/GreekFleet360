# GreekFleet 360 - Holistic Fleet & Mobility Management System

> 📚 **Documentation:** Start here → [`docs/GREEKFLEET360_SINGLE_SOURCE.md`](docs/GREEKFLEET360_SINGLE_SOURCE.md)  
> Full architecture reference: [`docs/MASTER_SYSTEM_ARCHITECTURE.md`](docs/MASTER_SYSTEM_ARCHITECTURE.md)

---

## 🚀 Επισκόπηση Έργου

Το **GreekFleet 360** είναι ένα ολοκληρωμένο **SaaS Fleet Management & Transport Management System** σχεδιασμένο ειδικά για την ελληνική αγορά. Παρέχει πλήρη διαχείριση στόλου, οικονομική ανάλυση, και decision support για εταιρείες μεταφορών.

### Βασικά Χαρακτηριστικά
- **Multi-Tenant SaaS Architecture**: Πολλαπλές εταιρείες με πλήρη απομόνωση δεδομένων
- **Unified Vehicle Model**: Ενιαίο μοντέλο οχήματος (`operations.Vehicle`) για όλους τους τύπους
- **Cost Engine v1.0**: True Break-Even & Profitability Analysis ανά κέντρο κόστους
- **REST API**: `/api/v1/cost-engine/run/` για analytics (DRF, schema v1)
- **Operations Tracking**: Καύσιμα, Συντηρήσεις, Συμβάντα
- **Modern Web UI**: HTMX + Tailwind CSS + Leaflet Maps
- **Authentication**: Πλήρες signup/login system

## 🛠️ Tech Stack

- **Backend**: Python 3.12, Django 5.0+, Django REST Framework 3.16.1
- **Database**: PostgreSQL (SQLite για development)
- **Frontend**: HTMX, Alpine.js, Tailwind CSS
- **Maps**: Leaflet.js με Nominatim & OSRM APIs
- **Admin**: Django Unfold theme

## 📦 Εγκατάσταση

### Προαπαιτούμενα
- Python 3.12
- pip

### Βήματα Εγκατάστασης

1. **Clone το repository**
```bash
git clone https://github.com/mixkonki/GreekFleet360.git
cd GreekFleet360
```

2. **Εγκατάσταση dependencies**
```bash
py -3.12 -m pip install -r requirements.txt
```

3. **Δημιουργία .env αρχείου**
```bash
copy .env.example .env
```

4. **Εκτέλεση migrations**
```bash
py -3.12 manage.py migrate
```

5. **Δημιουργία superuser**
```bash
py -3.12 manage.py createsuperuser
```

6. **Εκκίνηση development server**
```bash
py -3.12 manage.py runserver
```

7. **Πρόσβαση στο Admin Panel**
```
http://localhost:8000/admin/
```

## 📊 Δομή Βάσης Δεδομένων

### Core Models

#### Company (Εταιρεία)
- Multi-tenant model για απομόνωση δεδομένων
- Υποστήριξη διαφορετικών τύπων επιχειρήσεων (Μεταφορές, Ταξί, Τουριστικά, κλπ)

#### Vehicle (Όχημα) — `operations.Vehicle`
- Ενιαίο μοντέλο για όλους τους τύπους οχημάτων (φορτηγά, λεωφορεία, ταξί, επιβατικά, μοτοσυκλέτες)
- Κοινά πεδία: πινακίδα, VIN, ασφάλεια, ΚΤΕΟ, τύπος οχήματος
- Τύποι: `TRUCK`, `BUS`, `TAXI`, `CAR`, `MOTO`

#### DriverProfile (Προφίλ Οδηγού)
- Κατηγορίες άδειας (B, C, D, E, A)
- ΠΕΙ (CPC) certification
- Ιατρικές εξετάσεις
- Σύστημα βαθμών (Σησάμι)

## 🎯 Ολοκληρωμένες Φάσεις

### Phase 1: Data Foundation ✅
- ✅ Multi-tenant Company model
- ✅ Unified Vehicle model (`operations.Vehicle`)
- ✅ DriverProfile με άδειες, ΠΕΙ, ιατρικές
- ✅ Django Admin configuration

### Phase 2: Operations & Cost Ingestion ✅
- ✅ FuelEntry με auto-odometer update
- ✅ ServiceLog με invoice attachments
- ✅ IncidentReport (ατυχήματα, κλήσεις, βλάβες)
- ✅ Django Signals για automation

### Phase 3: Financial Core ✅
- ✅ Hierarchical expense structure (ExpenseFamily → ExpenseCategory → CompanyExpense)
- ✅ TransportOrder model (revenue tracking)
- ✅ CostCenter, CostItem, CostPosting models

### Phase 4: Web Frontend ✅
- ✅ Modern web UI με sidebar navigation
- ✅ Dashboard με 4 live KPIs
- ✅ Vehicle list με HTMX infinite scroll & health bars
- ✅ Order list με styled table
- ✅ **Order detail με Leaflet maps** (Nominatim + OSRM routing)

### Phase 5: Data Entry & Financial Configuration ✅
- ✅ Tailwind-styled forms
- ✅ Financial Settings page
- ✅ Order creation form
- ✅ Fuel entry form με auto-calculation (Alpine.js)

### Phase 6: Authentication & SaaS Onboarding ✅
- ✅ UserProfile model (User → Company link)
- ✅ **SaaS Signup**: Creates User + Company + Profile
- ✅ Login/Logout με modern UI
- ✅ @login_required protection
- ✅ Company-based data filtering (security)

### Phase 7: Localization & Polish ✅
- ✅ Greek language configuration
- ✅ Date formats (DD/MM/YYYY)
- ✅ Number formatting (1.234,56 €)
- ✅ Admin site header customization

### Phase 8: Cost Engine v1.0 ✅
- ✅ Multi-layer cost calculation service (`finance/services/cost_engine/`)
- ✅ Cost rates per cost center (KM, HOUR, TRIP, REVENUE basis)
- ✅ Order profitability analysis
- ✅ Historical snapshots (`CostRateSnapshot`, `OrderCostBreakdown`)
- ✅ Batch command: `python manage.py calculate_costs`
- ✅ Tenant isolation enforced with guardrails

### Phase 9: REST API Layer ✅
- ✅ DRF API endpoint: `GET /api/v1/cost-engine/run/`
- ✅ Session authentication, Staff/Superuser permissions
- ✅ Schema v1.0 responses
- ✅ 11 comprehensive API tests

## 🌐 API

### Cost Engine API

**Endpoint:** `GET /api/v1/cost-engine/run/`  
**Auth:** Session (Staff or Superuser only)  
**Schema:** v1.0 — see [`docs/cost_engine_schema_v1.md`](docs/cost_engine_schema_v1.md)

```bash
curl -X GET "http://localhost:8000/api/v1/cost-engine/run/?period_start=2026-01-01&period_end=2026-01-31" \
  -H "Cookie: sessionid=<your_session_id>"
```

**Parameters:** `period_start`, `period_end` (required) | `company_id`, `only_nonzero`, `include_breakdowns` (optional)

## 📝 Σημειώσεις Ανάπτυξης

### Python Version
Το project χρησιμοποιεί **Python 3.12**.

### Database
- **Development**: SQLite (default)
- **Production**: PostgreSQL (συνιστάται)

### Environment Variables
Δείτε το `.env.example` για τις απαιτούμενες μεταβλητές περιβάλλοντος.

## 📄 License

Proprietary - All rights reserved

## 👥 Contributors

- Senior Django Architect & Business Intelligence Lead

## 🚀 Γρήγορη Εκκίνηση (Quick Start)

### 1. Εγγραφή (Sign Up)
```
http://localhost:8000/accounts/signup/
```

### 2. Ρύθμιση Οικονομικών
```
http://localhost:8000/finance/settings/
```

### 3. Προσθήκη Οχημάτων
```
http://localhost:8000/admin/operations/vehicle/add/
```

### 4. Καταχώρηση Δεδομένων
- **Καύσιμα**: http://localhost:8000/fuel/create/
- **Εντολές**: http://localhost:8000/orders/create/
- **Συντηρήσεις**: Admin Panel

### 5. Cost Engine
```bash
python manage.py calculate_costs --period-start 2026-01-01 --period-end 2026-01-31
```

## 🔐 Security Features

- ✅ Multi-tenant data isolation (CompanyScopedManager + tenant_context)
- ✅ Login required για όλες τις σελίδες
- ✅ Company-based filtering (users see only their data)
- ✅ CSRF protection
- ✅ Password validation
- ✅ API: Staff/Superuser only

## 🗺️ Project Structure

```
TransCost/
├── core/               # Company, Employee, DriverProfile, tenant infrastructure
├── operations/         # Vehicle (unified), FuelEntry, ServiceLog, IncidentReport
├── finance/            # CostEngine, TransportOrder, Expenses, REST API
│   ├── services/cost_engine/  # calculator, queries, aggregations, snapshots, persist
│   └── api/v1/        # DRF views + urls
├── web/                # Frontend views & templates
├── accounts/           # Authentication & UserProfile
├── tests/              # All tests (56 passing)
├── docs/               # Architecture documentation
│   ├── GREEKFLEET360_SINGLE_SOURCE.md  ← Start here
│   ├── MASTER_SYSTEM_ARCHITECTURE.md
│   ├── DOCS_INDEX.md
│   └── cost_engine_schema_v1.md
├── greekfleet/         # Django settings
└── requirements.txt
```

## 🌐 URLs

- **Dashboard**: http://localhost:8000/
- **Στόλος**: http://localhost:8000/vehicles/
- **Εντολές**: http://localhost:8000/orders/
- **Οικονομικά**: http://localhost:8000/finance/settings/
- **API**: http://localhost:8000/api/v1/cost-engine/run/
- **Admin**: http://localhost:8000/admin/
- **Login**: http://localhost:8000/accounts/login/
- **Signup**: http://localhost:8000/accounts/signup/

---

**Version**: 3.0.0  
**Last Updated**: 2026-02-20  
**Status**: Production Ready ✅
