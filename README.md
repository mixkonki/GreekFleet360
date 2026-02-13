# GreekFleet 360 - Holistic Fleet & Mobility Management System

## 🚀 Επισκόπηση Έργου

Το **GreekFleet 360** είναι ένα ολοκληρωμένο **SaaS Fleet Management & Transport Management System** σχεδιασμένο ειδικά για την ελληνική αγορά. Παρέχει πλήρη διαχείριση στόλου, οικονομική ανάλυση, και decision support για εταιρείες μεταφορών.

### Βασικά Χαρακτηριστικά
- **Multi-Tenant SaaS Architecture**: Πολλαπλές εταιρείες με πλήρη απομόνωση δεδομένων
- **Polymorphic Vehicle Models**: Φορτηγά, Λεωφορεία, Ταξί, Επιβατικά, Μοτοσυκλέτες
- **Financial Engine**: True Break-Even & Profitability Analysis
- **Operations Tracking**: Καύσιμα, Συντηρήσεις, Συμβάντα
- **Modern Web UI**: HTMX + Tailwind CSS + Leaflet Maps
- **Authentication**: Πλήρες signup/login system

## 🛠️ Tech Stack

- **Backend**: Python 3.12, Django 5.0+
- **Database**: PostgreSQL (SQLite για development)
- **ORM**: django-polymorphic για vehicle inheritance
- **Frontend**: HTMX, Alpine.js, Tailwind CSS
- **Maps**: Leaflet.js με Nominatim & OSRM APIs
- **Admin**: Django Admin με Polymorphic support

## 📦 Εγκατάσταση

### Προαπαιτούμενα
- Python 3.12
- pip

### Βήματα Εγκατάστασης

1. **Clone το repository**
```bash
cd c:\wamp64\www\TransCost
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

#### VehicleAsset (Βασικό Όχημα)
- Polymorphic parent model
- Κοινά πεδία για όλα τα οχήματα (πινακίδα, VIN, ασφάλεια, ΚΤΕΟ)

#### Truck (Φορτηγό)
- Ταχογράφος, ADR, αριθμός αξόνων
- Σύνδεση με ρυμουλκούμενο

#### Bus (Λεωφορείο)
- Αριθμός θέσεων, WiFi, WC
- Ασφάλιση επιβατών

#### PassengerCar (Επιβατικό)
- Υποστήριξη Ταξί (ταξίμετρο, άδεια)
- Leasing information
- BiK tax value

#### Moto (Μοτοσυκλέτα)
- Κυβικά, top case
- Μέγιστο φορτίο για delivery

#### DriverProfile (Προφίλ Οδηγού)
- Κατηγορίες άδειας (B, C, D, E, A)
- ΠΕΙ (CPC) certification
- Ιατρικές εξετάσεις
- Σύστημα βαθμών (Σησάμι)

## 🎯 Ολοκληρωμένες Φάσεις

### Phase 1: Data Foundation ✅
- ✅ Multi-tenant Company model
- ✅ Polymorphic VehicleAsset (Truck, Bus, Taxi, PassengerCar, Moto)
- ✅ DriverProfile με άδειες, ΠΕΙ, ιατρικές
- ✅ Django Admin configuration

### Phase 2: Operations & Cost Ingestion ✅
- ✅ FuelEntry με auto-odometer update
- ✅ ServiceLog με invoice attachments
- ✅ IncidentReport (ατυχήματα, κλήσεις, βλάβες)
- ✅ Django Signals για automation

### Phase 3: Financial Core & Cost Engine ✅
- ✅ GlobalOverhead model με hourly rate calculation
- ✅ TransportOrder model (revenue tracking)
- ✅ **CostCalculator Service** (The Brain):
  - Fixed costs (depreciation, insurance, driver wage)
  - Overhead allocation
  - Variable costs (fuel από πραγματικά δεδομένα, tires, maintenance)
  - True profitability calculation

### Phase 4: Frontend Interface ✅
- ✅ Modern web UI με sidebar navigation
- ✅ Dashboard με 4 live KPIs
- ✅ Vehicle list με HTMX infinite scroll & health bars
- ✅ Order list με styled table
- ✅ **Order detail με Leaflet maps** (Nominatim + OSRM routing)

### Phase 5: Data Entry & Financial Configuration ✅
- ✅ Tailwind-styled forms
- ✅ Financial Settings page (GlobalOverhead configuration)
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
- ✅ All verbose names in Greek

## 📝 Σημειώσεις Ανάπτυξης

### Python Version
Το project χρησιμοποιεί **Python 3.12** για πλήρη συμβατότητα με GeoDjango, GDAL και βιβλιοθήκες υπολογισμών (Pandas/Numpy).

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
- Δημιουργήστε λογαριασμό χρήστη
- Εισάγετε στοιχεία εταιρείας (Επωνυμία, ΑΦΜ)
- Το σύστημα δημιουργεί αυτόματα Company + UserProfile
- Auto-login στο Dashboard

### 2. Ρύθμιση Οικονομικών
```
http://localhost:8000/finance/settings/
```
- Εισάγετε γενικά έξοδα (ενοίκιο, μισθοδοσία, κλπ)
- Δείτε την υπολογισμένη ωριαία επιβάρυνση

### 3. Προσθήκη Οχημάτων
```
http://localhost:8000/admin/core/vehicleasset/add/
```
- Επιλέξτε τύπο οχήματος (Truck, Bus, Taxi, Car, Moto)
- Συμπληρώστε στοιχεία (πινακίδα, VIN, ΚΤΕΟ, ασφάλεια)

### 4. Καταχώρηση Δεδομένων
- **Καύσιμα**: http://localhost:8000/fuel/create/
- **Εντολές**: http://localhost:8000/orders/create/
- **Συντηρήσεις**: Admin Panel

### 5. Ανάλυση & Αποφάσεις
- **Dashboard**: Live KPIs (έσοδα, κέρδος, συντήρηση)
- **Στόλος**: Health bars για κάθε όχημα
- **Εντολές**: Profitability analysis με maps

## 🔐 Security Features

- ✅ Multi-tenant data isolation
- ✅ Login required για όλες τις σελίδες
- ✅ Company-based filtering (users see only their data)
- ✅ CSRF protection
- ✅ Password validation
- ✅ Role-based access control (ready)

## 📈 Key Features

### Financial Intelligence
- **True Break-Even Calculation**: Fixed + Overhead + Variable costs
- **Real Fuel Consumption**: Από πραγματικά δεδομένα (full-tank method)
- **Profitability per Trip**: Live calculation με traffic lights
- **Cost Allocation**: Overhead distribution across fleet

### Operations Automation
- **Auto-Odometer Update**: Signals update vehicle mileage
- **Maintenance Alerts**: Based on km & time intervals
- **Fuel Consumption Tracking**: L/100km από ιστορικό

### Modern UX
- **HTMX**: Dynamic updates χωρίς page reload
- **Infinite Scroll**: Vehicle list pagination
- **Interactive Maps**: Route visualization με Leaflet
- **Auto-Calculations**: Alpine.js για real-time totals

## 🗺️ Project Structure

```
TransCost/
├── core/               # Company, VehicleAsset, DriverProfile
├── operations/         # FuelEntry, ServiceLog, IncidentReport
├── finance/            # GlobalOverhead, TransportOrder, CostCalculator
├── web/                # Frontend views & templates
├── accounts/           # Authentication & UserProfile
├── greekfleet/         # Django settings
├── requirements.txt    # Python dependencies
├── .env.example        # Environment variables template
└── README.md          # This file
```

## 🌐 URLs

- **Dashboard**: http://localhost:8000/
- **Στόλος**: http://localhost:8000/vehicles/
- **Εντολές**: http://localhost:8000/orders/
- **Οικονομικά**: http://localhost:8000/finance/settings/
- **Admin**: http://localhost:8000/admin/
- **Login**: http://localhost:8000/accounts/login/
- **Signup**: http://localhost:8000/accounts/signup/

---

**Version**: 2.0.0 (All Phases Complete)  
**Last Updated**: 2026-02-12  
**Status**: Production Ready ✅

</final_file_content>

IMPORTANT: For any future changes to this file, use the final_file_content shown above as your reference. This content reflects the current state of the file, including any auto-formatting (e.g., if you used single quotes but the formatter converted them to double quotes). Always base your SEARCH/REPLACE operations on this final version to ensure accuracy.

<environment_details>
# Visual Studio Code Visible Files
README.md

# Visual Studio Code Open Tabs
greekfleet/settings.py
core/admin.py
accounts/admin.py
README.md

# Actively Running Terminals
## Original command: `py -3.12 manage.py makemigrations core`
## Original command: `py -3.12 manage.py runserver`

# Current Time
2/12/2026, 9:17:48 AM (Europe/Athens, UTC+2:00)

# Current Mode
ACT MODE
