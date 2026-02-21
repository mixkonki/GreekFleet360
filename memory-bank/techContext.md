# Tech Context — GreekFleet 360

## Development Environment
- **OS:** Windows 11
- **IDE:** Visual Studio Code
- **Shell:** PowerShell / CMD
- **Web Server (dev):** WAMP64
- **Python venv:** `.venv\` (στο root του project)
- **Python command:** `.venv\Scripts\python.exe manage.py ...`
- **Working Directory:** `c:\wamp64\www\TransCost`

## Dependencies (requirements.txt)
```
asgiref==3.11.1
Django==5.0.14
django-extensions==4.1
django-polymorphic==4.11.0          # Υπάρχει αλλά δεν χρησιμοποιείται πλέον
django-unfold==0.79.0
djangorestframework==3.16.1
djangorestframework_simplejwt==5.5.1
pillow==12.1.1
psycopg2-binary==2.9.11
python-dateutil==2.9.0
python-dotenv==1.2.1
PyJWT==2.11.0
sqlparse==0.5.5
typing_extensions==4.15.0
tzdata==2025.3
```

## Django Settings Key Points

### INSTALLED_APPS (σειρά σημαντική)
```python
'unfold',                              # Πρέπει να είναι ΠΡΙΝ το django.contrib.admin
'unfold.contrib.filters',
'unfold.contrib.forms',
'django.contrib.admin',
...
'rest_framework',
'rest_framework_simplejwt',
'rest_framework_simplejwt.token_blacklist',
'polymorphic',
'django_extensions',
'core', 'operations', 'finance', 'web', 'accounts',
```

### Middleware (σειρά σημαντική)
```python
'core.middleware.CurrentCompanyMiddleware',  # Tenant isolation — μετά το AuthenticationMiddleware
```

### Database
- Dev: SQLite (`db.sqlite3`)
- Prod: PostgreSQL (via env vars)

### Localization
```python
LANGUAGE_CODE = 'el'
TIME_ZONE = 'Europe/Athens'
DATE_INPUT_FORMATS = ['%d/%m/%Y', '%d-%m-%Y', '%Y-%m-%d']
USE_THOUSAND_SEPARATOR = True
THOUSAND_SEPARATOR = '.'
DECIMAL_SEPARATOR = ','
```

### JWT Configuration
```python
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=15),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=30),
    'ROTATE_REFRESH_TOKENS': False,
    'BLACKLIST_AFTER_ROTATION': True,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'ALGORITHM': 'HS256',
    'TOKEN_BLACKLIST_ENABLED': True,
}
```

### DRF Configuration
```python
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',  # JWT πρώτο
        'rest_framework.authentication.SessionAuthentication',          # Session δεύτερο
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
        'rest_framework.permissions.IsAdminUser',
    ],
    'DEFAULT_RENDERER_CLASSES': ['rest_framework.renderers.JSONRenderer'],
    'COERCE_DECIMAL_TO_STRING': False,  # Decimals ως numbers στο JSON
}
```

### Authentication URLs
```python
LOGIN_URL = 'accounts:login'
LOGIN_REDIRECT_URL = 'web:dashboard'
LOGOUT_REDIRECT_URL = 'accounts:login'
```

## URL Structure
```
/                           → web:dashboard
/accounts/login/            → accounts:login
/accounts/logout/           → accounts:logout
/accounts/signup/           → accounts:signup
/admin/                     → Django admin (Unfold theme)
/api/v1/auth/token/         → JWT obtain
/api/v1/auth/refresh/       → JWT refresh
/api/v1/auth/logout/        → JWT blacklist
/api/v1/cost-engine/run/    → Cost Engine API
/api/v1/cost-engine/history/ → History API
/api/v1/kpis/company/summary/       → KPI summary
/api/v1/kpis/company/cost-structure/ → Cost structure
/api/v1/kpis/company/trend/         → Trend
/finance/debug/cost-engine/ → DEV ONLY
/vehicles/                  → Vehicle list (HTMX)
/orders/                    → Order list
/orders/<id>/               → Order detail
/orders/create/             → Create order
/fuel/create/               → Create fuel entry
/finance/settings/          → Finance settings
/fleet/                     → Fleet management
/settings/                  → Settings hub
```

## Management Commands
```bash
# Εκτέλεση με venv:
.venv\Scripts\python.exe manage.py <command>

# Βασικές εντολές:
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
python manage.py test
python manage.py test tests.test_jwt_auth --verbosity=2

# Custom commands:
python manage.py calculate_costs --period-start 2026-01-01 --period-end 2026-01-31
python manage.py calculate_costs --dry-run
python manage.py seed_finance_data
python manage.py seed_cost_engine_demo
```

## Git Repository
- **Remote:** github.com/mixkonki/GreekFleet360 (ή παρόμοιο)
- **Current branch:** `feature/jwt-auth`
- **Main branch:** `main`
- **HEAD commit:** `b84eb89` — feat(auth): JWT authentication layer v1.0

### Branches
```
main                          ← Stable (a92042b)
feature/jwt-auth              ← HEAD (b84eb89) — JWT auth layer
feature/kpi-endpoints         ← KPI endpoints
feature/cost-engine-history-api ← History API
docs-alignment                ← Docs sync
docs-and-api-layer            ← Merged to main
cost-engine-pr9-1             ← Merged to main
cost-engine-logic             ← Merged to main
...
```

### Σχέση branches με main
- `feature/jwt-auth` είναι **3 commits ahead** του main
- Δεν έχει γίνει merge/PR ακόμα

## Test Suite
- **Συνολικά tests:** 133
- **Status:** ALL PASSING ✅
- **Εκτέλεση:** ~3 λεπτά (SQLite in-memory)
- **Αρχεία:**
  - `tests/test_jwt_auth.py` (20 tests) — JWT auth
  - `tests/test_kpi_endpoints.py` (35 tests) — KPI API
  - `tests/test_cost_engine_api.py` (11 tests) — Cost Engine API
  - `tests/test_cost_engine_history_api.py` — History API
  - `tests/test_cost_engine_calculation.py` — Calculations
  - `tests/test_cost_engine_persistence.py` (8 tests) — Persistence
  - `tests/test_cost_engine.py` (8 tests) — Integration
  - `tests/test_tenant_isolation.py` — Tenant isolation
  - `tests/test_admin_isolation.py` — Admin isolation
  - `tests/test_view_isolation.py` — View isolation
  - `tests/test_company_autoset.py` — Auto-assignment
  - `tests/test_guardrails.py` — Bypass manager detection

## Environment Variables (.env)
```bash
SECRET_KEY=<strong-random-key>
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
DB_ENGINE=django.db.backends.sqlite3
DB_NAME=<path>/db.sqlite3
EMAIL_HOST=smtp.example.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=
EMAIL_PASSWORD=
DEFAULT_FROM_EMAIL=
ADMIN_EMAIL=admin@example.com
```

## Logging
- File: `logs/system_errors.log`
- RotatingFileHandler: 10MB, 5 backups
- Level: ERROR (file), INFO (console)
- Admin email notifications σε production (DEBUG=False)

## Production Stack (Planned)
```
Internet → Nginx (SSL, static files)
         → Gunicorn (4 workers)
         → Django
         → PostgreSQL
         → Redis (future: Celery)
```

## Known Issues / Gotchas
1. **`python` command** χρησιμοποιεί system Python (3.14) — πάντα χρησιμοποίησε `.venv\Scripts\python.exe`
2. **`git log`** ανοίγει pager (less) — χρησιμοποίησε `git log --oneline -N 2>&1` ή `git log -N 2>&1`
3. **`head` command** δεν υπάρχει σε Windows CMD/PowerShell
4. **`django-polymorphic`** υπάρχει στο requirements.txt αλλά δεν χρησιμοποιείται πλέον (VehicleAsset διαγράφηκε)
5. **`web/migrations/`** έχει μόνο `__init__.py` — το web app δεν έχει δικά του models
6. **`finance/services.py`** ΔΕΝ ΥΠΑΡΧΕΙ — το services directory είναι `finance/services/`
