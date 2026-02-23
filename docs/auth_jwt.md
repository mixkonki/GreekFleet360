# JWT Authentication — GreekFleet 360 API

**Version:** 1.0 | **Date:** 2026-02-20  
**Library:** `djangorestframework-simplejwt` v5.5.1  
**Algorithm:** HS256 | **Blacklist:** Enabled

---

## Overview

The GreekFleet 360 API uses **JSON Web Tokens (JWT)** for stateless authentication. The implementation uses `djangorestframework-simplejwt` with token blacklisting enabled for secure logout.

### Token Lifetimes

| Token | Lifetime | Notes |
|---|---|---|
| Access Token | 15 minutes | Short-lived, stateless. Cannot be revoked individually. |
| Refresh Token | 30 days | Long-lived, stored in blacklist DB on logout. |

---

## Endpoints

### 1. Obtain Tokens

**`POST /api/v1/auth/token/`**

Exchange username/password for an access + refresh token pair.

**Request:**
```json
{
  "username": "your_username",
  "password": "your_password"
}
```

**Response (200 OK):**
```json
{
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Error Responses:**
| Status | Condition |
|---|---|
| `400` | Missing `username` or `password` field |
| `401` | Invalid credentials |

---

### 2. Refresh Access Token

**`POST /api/v1/auth/refresh/`**

Exchange a valid refresh token for a new access token.

**Request:**
```json
{
  "refresh": "<refresh_token>"
}
```

**Response (200 OK):**
```json
{
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Error Responses:**
| Status | Condition |
|---|---|
| `400` | Missing `refresh` field |
| `401` | Invalid, expired, or blacklisted refresh token |

---

### 3. Logout (Blacklist Refresh Token)

**`POST /api/v1/auth/logout/`**

Blacklists the provided refresh token, preventing further use. The access token remains valid until it expires (15 min).

**Authentication:** Required (`Authorization: Bearer <access_token>`)

**Request:**
```json
{
  "refresh": "<refresh_token>"
}
```

**Response (200 OK):**
```json
{
  "detail": "Successfully logged out. Refresh token has been blacklisted."
}
```

**Error Responses:**
| Status | Condition |
|---|---|
| `400` | Missing `refresh` field |
| `400` | Invalid or already blacklisted token |
| `401` | Not authenticated (no/invalid access token) |

---

## Using Tokens in API Requests

Include the access token in the `Authorization` header:

```
Authorization: Bearer <access_token>
```

**Example:**
```bash
curl "http://localhost:8000/api/v1/kpis/company/summary/?month=2026-01&company_id=1" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

---

## Authentication Flow

```
Client                          Server
  │                               │
  │  POST /api/v1/auth/token/     │
  │  {username, password}         │
  │ ─────────────────────────────►│
  │                               │  Validate credentials
  │  {access, refresh}            │
  │ ◄─────────────────────────────│
  │                               │
  │  GET /api/v1/kpis/...         │
  │  Authorization: Bearer <acc>  │
  │ ─────────────────────────────►│
  │                               │  Validate access token (stateless)
  │  200 OK + data                │
  │ ◄─────────────────────────────│
  │                               │
  │  [15 min later — access expires]
  │                               │
  │  POST /api/v1/auth/refresh/   │
  │  {refresh}                    │
  │ ─────────────────────────────►│
  │                               │  Validate refresh token
  │  {access: new_token}          │
  │ ◄─────────────────────────────│
  │                               │
  │  POST /api/v1/auth/logout/    │
  │  Authorization: Bearer <acc>  │
  │  {refresh}                    │
  │ ─────────────────────────────►│
  │                               │  Blacklist refresh token in DB
  │  200 OK                       │
  │ ◄─────────────────────────────│
```

---

## Security Notes

### Access Token Revocation
Access tokens are **stateless** — they cannot be individually revoked. After logout, the access token remains valid until its 15-minute expiry. This is a deliberate trade-off for performance (no DB lookup per request).

**Mitigation strategies:**
- Keep access token lifetime short (15 min — already configured)
- For high-security operations, check token age on the server side
- Future: implement a short-lived token denylist (Redis) if needed

### Refresh Token Blacklisting
Refresh tokens are stored in the `token_blacklist` table (Django DB) upon logout. This ensures that:
- A stolen refresh token cannot be used after the user logs out
- The blacklist is checked on every `/refresh/` request

### Token Storage (Client-Side Recommendations)
| Storage | Recommendation | Risk |
|---|---|---|
| `localStorage` | ⚠️ Avoid for access tokens | XSS vulnerable |
| `sessionStorage` | ⚠️ Acceptable for access tokens | XSS vulnerable, cleared on tab close |
| `httpOnly Cookie` | ✅ Recommended for refresh tokens | CSRF protected with `SameSite=Strict` |
| Memory (JS variable) | ✅ Recommended for access tokens | Lost on page refresh |

---

## Configuration Reference

Settings in `greekfleet/settings.py`:

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

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',  # JWT first
        'rest_framework.authentication.SessionAuthentication',         # Session second (HTMX)
    ],
    ...
}
```

**Installed apps required:**
```python
INSTALLED_APPS = [
    ...
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',  # Required for logout
    ...
]
```

---

## Test Coverage

`tests/test_jwt_auth.py` — 18 tests across 4 test classes:

| Class | Tests |
|---|---|
| `JWTTokenObtainTest` | Valid credentials, invalid password, nonexistent user, missing fields |
| `JWTTokenRefreshTest` | Valid refresh, invalid token, missing field |
| `JWTLogoutTest` | Valid logout, blacklist verification, double-logout, missing field, unauthenticated, invalid token |
| `JWTProtectedEndpointTest` | Valid token, no token, invalid token, access after refresh blacklisted, programmatic token |

---

## Quick Start (curl)

```bash
# 1. Obtain tokens
curl -X POST http://localhost:8000/api/v1/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "yourpassword"}'

# 2. Use access token
ACCESS="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
curl http://localhost:8000/api/v1/kpis/company/summary/?month=2026-01&company_id=1 \
  -H "Authorization: Bearer $ACCESS"

# 3. Refresh when access expires
REFRESH="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
curl -X POST http://localhost:8000/api/v1/auth/refresh/ \
  -H "Content-Type: application/json" \
  -d "{\"refresh\": \"$REFRESH\"}"

# 4. Logout
curl -X POST http://localhost:8000/api/v1/auth/logout/ \
  -H "Authorization: Bearer $ACCESS" \
  -H "Content-Type: application/json" \
  -d "{\"refresh\": \"$REFRESH\"}"
```

---

*GreekFleet 360 JWT Auth v1.0 | Last updated: 2026-02-20*
