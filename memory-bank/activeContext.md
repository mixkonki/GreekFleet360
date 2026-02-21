# Active Context — GreekFleet 360

## Τρέχουσα Εστίαση
**Ημερομηνία:** 2026-02-21  
**Branch:** `feature/jwt-auth`  
**Τελευταία εργασία:** JWT Authentication Layer (Phase 10) — ΟΛΟΚΛΗΡΩΘΗΚΕ ✅

---

## Πρόσφατες Αλλαγές (feature/jwt-auth branch)

### Commit: `b84eb89` — feat(auth): JWT authentication layer v1.0
- Προστέθηκε `djangorestframework-simplejwt` v5.5.1
- Νέα αρχεία:
  - `finance/api/v1/auth_urls.py` — JWT URL routing
  - `finance/api/v1/auth_views.py` — `LogoutView` (blacklist)
  - `finance/api/v1/permissions.py` — `AnalyticsPermission` (RBAC scaffold)
  - `tests/test_jwt_auth.py` — 20 JWT tests
  - `docs/auth_jwt.md` — JWT documentation
- Ενημερώθηκε `greekfleet/settings.py`:
  - `SIMPLE_JWT` configuration
  - `REST_FRAMEWORK` authentication classes (JWT πρώτο)
  - `rest_framework_simplejwt.token_blacklist` στο INSTALLED_APPS
- Ενημερώθηκε `greekfleet/urls.py`:
  - `path('api/v1/auth/', include('finance.api.v1.auth_urls'))`

### Προηγούμενα commits (στο branch, πριν το main):
- `d01d198` — KPI endpoints (summary, cost-structure, trend)
- `9fac728` — Cost Engine History API

---

## Τρέχουσα Κατάσταση Tests
- **136 tests, ALL PASSING** ✅ (133 original + 3 νέα test_settings_403)
- Τελευταία εκτέλεση: 2026-02-21 (~151 sec χωρίς token_blacklist / ~183 sec με)
- JWT tests: 20/20 ✅
- Settings 403 tests: 3/3 ✅

---

## Ενεργές Αποφάσεις & Σκέψεις

### 1. Branch Strategy
- `feature/jwt-auth` είναι έτοιμο για PR → main
- Περιέχει: JWT auth + KPI endpoints + History API + docs
- Όλα τα tests περνούν

### 2. Legacy Services
- `web/views.py` χρησιμοποιεί ακόμα `CostCalculator` από `legacy_services.py`
  - `dashboard_home()` → profit margin calculation
  - `order_detail()` → trip profitability
- Αυτό είναι **γνωστό technical debt** — δεν είναι bug, απλά deprecated code
- Δεν χρειάζεται άμεση διόρθωση αλλά πρέπει να γίνει eventually

### 3. Vehicle Search Bug ✅ ΔΙΟΡΘΩΘΗΚΕ (2026-02-21)
- `vehicle_list` view: `Q(plate__icontains=...)` → `Q(license_plate__icontains=...)`
- `django check` → 0 issues
- View isolation tests: 3/3 PASSING

### 4. AnalyticsPermission
- Δημιουργήθηκε ως RBAC scaffold
- Δεν χρησιμοποιείται ακόμα στα views (χρησιμοποιείται `IsAdminUser`)
- Σχεδιασμένο για μελλοντική επέκταση με UserProfile.role

### 5. Settings Hub ✅ ΔΙΟΡΘΩΘΗΚΕ (2026-02-21)
- Canonical related_name: `profile` (ορίζεται στο `accounts/models.py`)
- `web/views.py`: όλα τα `userprofile` → `profile` (27 views, 100% consistent)
- `core/admin.py`: `userprofile` → `profile` + `userprofile__company` → `profile__company`
- `django check` → 0 issues | 15 isolation tests PASSING

---

## Επόμενα Βήματα (Άμεσα)

### Προτεραιότητα 1: Merge feature/jwt-auth → main
```bash
git checkout main
git merge feature/jwt-auth
# ή μέσω GitHub PR
```

### ~~Προτεραιότητα 2: Fix vehicle_list search bug~~ ✅ ΟΛΟΚΛΗΡΩΘΗΚΕ

### Προτεραιότητα 2 (νέα): Fix UserProfile access inconsistency
```python
# Ορισμένα views χρησιμοποιούν:
request.user.profile.company      # related_name='profile' στο UserProfile
# Άλλα χρησιμοποιούν:
request.user.userprofile.company  # default Django related name
# Πρέπει να γίνει consistent → χρησιμοποίησε 'profile' (το related_name)
```

### Προτεραιότητα 4: Deprecation notice σε legacy_services.py
```python
# Προσθήκη στην αρχή του αρχείου:
import warnings
warnings.warn(
    "legacy_services.py is deprecated. Use finance.services.cost_engine instead.",
    DeprecationWarning,
    stacklevel=2
)
```

---

## Σημαντικά Patterns που Πρέπει να Θυμάσαι

### Tenant Context (ΥΠΟΧΡΕΩΤΙΚΟ)
```python
from core.tenant_context import tenant_context
with tenant_context(company):
    result = calculate_company_costs(company, start, end)
```

### Company από Request
```python
# Σωστός τρόπος (consistent):
try:
    company = request.user.profile.company  # related_name='profile'
except:
    company = Company.objects.first()  # Fallback για development
```

### JWT Test Pattern
```python
from rest_framework_simplejwt.tokens import RefreshToken
refresh = RefreshToken.for_user(user)
access = str(refresh.access_token)
client.get(url, HTTP_AUTHORIZATION=f'Bearer {access}')
```

### HTMX Delete Pattern
```python
def expense_delete(request, expense_id):
    expense.delete()
    return HttpResponse('', status=200)  # HTMX αφαιρεί το row
```

---

## Αρχεία που Άνοιξαν Πρόσφατα
- `finance/migrations/0006_alter_companyexpense_is_amortized_and_more.py`
- `web/forms.py`
- `finance/models.py`
- `core/admin.py`
- `operations/admin.py`
- `finance/admin.py`

---

## Σημειώσεις για Επόμενη Συνεδρία
1. Το Memory Bank δημιουργήθηκε σήμερα (2026-02-21) — πρώτη φορά
2. Το project είναι σε πολύ καλή κατάσταση — production-ready αρχιτεκτονικά
3. Το επόμενο λογικό βήμα είναι merge → main και deployment readiness
4. Σήμερα διορθώθηκαν 3 issues: vehicle search bug, userprofile inconsistency, settings 403 enforcement
5. Test suite: 136 tests (133 + 3 νέα) — ALL PASSING (αναμένεται)
