> ⚠️ **ARCHIVED:** This document reflects the original project vision (February 2026).
> For current architecture, implementation state, and roadmap see:
> - [`docs/GREEKFLEET360_SINGLE_SOURCE.md`](docs/GREEKFLEET360_SINGLE_SOURCE.md) — Entry point
> - [`docs/MASTER_SYSTEM_ARCHITECTURE.md`](docs/MASTER_SYSTEM_ARCHITECTURE.md) — Full reference

---

# Project Name: GreekFleet 360 (Holistic FMS & TMS)
# Role: Senior Django Architect & Business Intelligence Lead

## 1. Vision & Scope
Create a unified **Fleet & Mobility Management Ecosystem** for the Greek market (2026).
The platform must be "Asset Agnostic," capable of managing:
- **Heavy Transport:** Public (ΦΔΧ) & Private (ΦΙΧ) Trucks.
- **Passenger Transport:** Buses (Public/Private), Minivans (Transfer/Tourism), Taxis.
- **Corporate Fleet:** Sales cars, Technician vans, Pool vehicles.
- **Micromobility:** Motorcycles/Scooters (Delivery/Courier).

**Core Promise:** Not just "tracking," but **Decision Support**. The system analyzes data to propose cost-saving actions (e.g., "Change tires to Class A rolling resistance to save €400/year").

## 2. Tech Stack (The Engine)
- **Backend:** Python 3.12+, Django 5.0+ (utilizing GenericForeignKeys & Polymorphism).
- **Database:** PostgreSQL + PostGIS.
- **Frontend:** HTMX + Alpine.js (for reactive dashboards without React bloat) + Leaflet.js.
- **Mobile:** Progressive Web App (PWA) for drivers (Expense capture, Check-in).

## 3. Data Architecture (The Polymorphic Model)

### A. The "Universal Asset" (Parent Model)
Every vehicle shares:
- **Identity:** Plate, VIN, Make, Model, Purchase Date, Purchase Price.
- **Compliance:** Insurance exp., KTEO exp., Circulation Tax (Teli) status.
- **Maintenance:** Service logs, Tire logs (Position, Brand, KM installed).
- **Incidents:** Accidents (Photos, Cost), Fines (Traffic police/Troxaia).

### B. Specialized Attributes (Child Models)
- **Trucks:** Tachograph calibration, ADR cert, Trailer link, Axle config.
- **Buses/Transfers:** Seat count, Wifi availability, Toilet, Pax Insurance.
- **Taxis:** Taximeter S/N, Shift capability (Double shift/Syntairia).
- **Sales Cars:** Leasing contract details, Benefit-in-Kind (BiK) tax value.

### C. Human Resources (The Users)
- **Role Based Access Control (RBAC):**
  - *Admin:* Full view.
  - *Fleet Manager:* Can approve repairs.
  - *Driver:* Can only see their vehicle and tasks.
  - *Accountant:* Read-only access to invoices.
- **Driver Profiles:** License Categories (B, C, D, E), CPC (PEI) expiration, Medical exam expiration, Point System (Sesame).

## 4. The Intelligence Modules (AI & DSS)

### A. Cost Center & Profit Center Logic
- **Private Use (ΦΙΧ/Sales):** Focus on *Cost per KM* & *TCO*.
  - *Alert:* "Vehicle X consumption increased by 15% this month. Check injectors."
- **Public Use (ΦΔΧ/Bus/Taxi):** Focus on *Profitability*.
  - *Calculation:* Revenue - (Fixed + Variable + Allocated Overhead).

### B. Smart Decision Engine (The "Consultant")
- **Fuel Optimization:**
  - *Algorithm:* Compare Route A (Shortest) vs Route B (Cheaper Gas Station).
  - *Suggestion:* "Detour 2km to 'EKO' to save €0.15/L. Net saving: €12."
- **Tire Strategy:**
  - *Calc:* Input Tire Price vs Rolling Resistance (Fuel Impact).
  - *Suggestion:* "Buying the Michelin (Class A) over the budget tire will save €300 in fuel over 50k km."
- **Maintenance Prediction:**
  - *Logic:* "Based on current daily km, Service B is due in 14 days. Book now."

### C. Operational Dashboard
- **Kanban Board:** For Service appointments and Repairs.
- **Calendar:** Unified view of all expirations (Licenses, KTEO, Insurance).
- **Maps:** Live tracking (via API/GPS) + Route Planning.

## 5. Integrations & Automation
- **Fuel Cards:** Parsers for CSV files from major providers (Coral, BP, EKO, Avin).
- **Gov APIs:** Open input for future TaxisNet/MyData integration.
- **Telematics:** Generic webhook receiver for GPS providers (Teltonika, Geotab).

## 6. User Experience Flow
1. **Onboarding:** User selects "Business Type" (e.g., "Tour Operator"). System hides "Truck" features and highlights "Bus/Transfer" features.
2. **Daily Routine (Manager):** Dashboard shows "Red Flags" (Expired licenses, Pending fines, Loss-making vehicles).
3. **Daily Routine (Driver):** Log in via Mobile -> Check vehicle condition (Walk-around check) -> Upload Gas Receipt -> View Schedule.
## 7. Deployment & Web Architecture
- **Web-First:** The application is a SaaS cloud platform.
- **Server:** Linux (Ubuntu) running Gunicorn + Nginx.
- **Security:** HTTPS (SSL), Secure Cookies, CSRF protection strictly enforced.
- **Multi-Tenancy:** The system must be designed so multiple companies can use it securely, with each company only seeing their own data (Data Isolation).