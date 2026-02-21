# Project Brief — GreekFleet 360

## Ταυτότητα Project
- **Όνομα:** GreekFleet 360
- **Τύπος:** Multi-tenant SaaS Fleet & Transport Management System
- **Αγορά:** Ελληνική αγορά μεταφορών (2026)
- **Ρόλος AI:** Senior Django Architect & Business Intelligence Lead

## Core Vision
**"Asset Agnostic Fleet Intelligence for the Greek Market"**

Ολοκληρωμένη πλατφόρμα διαχείρισης στόλου που παρέχει:
1. **Fleet Management** — Οχήματα, οδηγοί, συμμόρφωση (KTEO, ΠΕΙ, ασφάλεια)
2. **Financial Intelligence** — Πραγματικό κόστος ανά km/ώρα/δρομολόγιο, κερδοφορία
3. **Decision Support** — Actionable recommendations (μελλοντικό)

## Target Market
1. Βαριές μεταφορές: ΦΔΧ/ΦΙΧ φορτηγά
2. Επιβατικές μεταφορές: Λεωφορεία, τουριστικά, minivans
3. Ταξί (συμπεριλαμβανομένης διπλής βάρδιας / Συνταιρία)
4. Εταιρικός στόλος: Αυτοκίνητα πωλητών, βαν τεχνικών
5. Micromobility: Μοτοσυκλέτες/scooters (delivery/courier)

## Tech Stack
- **Backend:** Python 3.12, Django 5.0.14, DRF 3.16.1
- **Auth:** djangorestframework-simplejwt 5.5.1
- **Frontend:** HTMX + Alpine.js + Tailwind CSS + Leaflet.js
- **Admin:** django-unfold
- **DB:** SQLite (dev) / PostgreSQL (prod)
- **Deployment:** WAMP64 (dev) → Gunicorn + Nginx (prod)

## Αρχιτεκτονικές Αρχές
- Multi-tenant: Shared DB, scoped queries (CompanyScopedManager)
- API-first: DRF REST API με JWT authentication
- Domain-driven: core / operations / finance / web / accounts
- Tenant isolation: Guardrails enforced via automated tests
- Decimal precision: Ποτέ float για χρηματικά ποσά

## Βασικά Constraints
- Κάθε model έχει `company` FK (tenant root)
- `objects` = CompanyScopedManager (scoped)
- `all_objects` = unscoped (ΑΠΑΓΟΡΕΥΕΤΑΙ σε services/views)
- Όλες οι service calls εντός `tenant_context(company)`
- `legacy_services.py` = DEPRECATED
- `operations.Vehicle` = το μοναδικό vehicle model (VehicleAsset διαγράφηκε)
