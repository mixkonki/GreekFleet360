# KPI API v1 — GreekFleet 360

**Version:** 1.0 | **Date:** 2026-02-20  
**Source:** Persisted data only (`CostRateSnapshot`). Never calls the cost engine pipeline.

---

## Overview

Three dashboard-ready KPI endpoints that read from persisted `CostRateSnapshot` records.

**Base URL:** `/api/v1/kpis/company/`  
**Authentication:** Session (cookie-based)  
**Permission:** Staff or Superuser  
**Tenant isolation:** All queries run inside `tenant_context(company)`

---

## Common Parameters

All three endpoints share the same period and company resolution logic:

| Parameter | Type | Default | Description |
|---|---|---|---|
| `month` | YYYY-MM | — | Preferred shortcut. Overrides period_start/end. |
| `period_start` | YYYY-MM-DD | previous month start | Period start (both required together) |
| `period_end` | YYYY-MM-DD | previous month end | Period end (both required together) |
| `company_id` | integer | user's company | Superuser only. Returns 403 for non-superusers. |
| `basis_unit` | KM\|HOUR\|TRIP\|REVENUE | KM | Filter by basis unit |

**Period defaulting:** If no `month` and no `period_start`/`period_end` are provided, the endpoint defaults to the **previous full calendar month** (e.g., if today is 2026-02-20, default is 2026-01-01 to 2026-01-31).

---

## 1. Company Summary

**Endpoint:** `GET /api/v1/kpis/company/summary/`

Aggregate KPIs for a company over a period.

### Parameters

All common parameters apply. No additional parameters.

### Response

```json
{
  "meta": {
    "schema": "kpi-v1",
    "period_start": "2026-01-01",
    "period_end": "2026-01-31",
    "grain": "period",
    "basis_unit": "KM"
  },
  "kpis": {
    "total_cost": "1300.00",
    "total_units": "500.000",
    "avg_rate": "2.6",
    "cost_per_unit": "2.6",
    "snapshot_count": 2,
    "missing_activity_count": 1,
    "missing_rate_count": 0
  }
}
```

### KPI Fields

| Field | Description |
|---|---|
| `total_cost` | Sum of `total_cost` across all matching snapshots |
| `total_units` | Sum of `total_units` across all matching snapshots |
| `avg_rate` | Weighted average rate (total_cost / total_units); falls back to simple avg if total_units=0 |
| `cost_per_unit` | Alias for `avg_rate` |
| `snapshot_count` | Number of snapshots in the period |
| `missing_activity_count` | Snapshots with `status=MISSING_ACTIVITY` |
| `missing_rate_count` | Snapshots with `status=MISSING_RATE` |

### Examples

```bash
# Previous month (default)
curl "http://localhost:8000/api/v1/kpis/company/summary/?company_id=1" \
  -H "Cookie: sessionid=<session>"

# Specific month
curl "http://localhost:8000/api/v1/kpis/company/summary/?month=2026-01&company_id=1" \
  -H "Cookie: sessionid=<session>"

# Custom period, HOUR basis
curl "http://localhost:8000/api/v1/kpis/company/summary/?period_start=2026-01-01&period_end=2026-03-31&basis_unit=HOUR&company_id=1" \
  -H "Cookie: sessionid=<session>"
```

---

## 2. Cost Structure

**Endpoint:** `GET /api/v1/kpis/company/cost-structure/`

Cost distribution by cost center for a period. Shows what percentage of total cost each cost center represents.

### Additional Parameters

| Parameter | Type | Default | Description |
|---|---|---|---|
| `group_by` | string | `cost_center` | Grouping dimension (only `cost_center` supported) |

### Response

```json
{
  "meta": {
    "schema": "kpi-v1",
    "period_start": "2026-01-01",
    "period_end": "2026-01-31",
    "grain": "period",
    "basis_unit": null,
    "group_by": "cost_center"
  },
  "items": [
    {
      "group_id": 9,
      "group_name": "CC-DEMO-001",
      "total_cost": "1000.00",
      "share_pct": "76.92"
    },
    {
      "group_id": 10,
      "group_name": "Overhead-General",
      "total_cost": "300.00",
      "share_pct": "23.08"
    }
  ],
  "totals": {
    "total_cost": "1300.00"
  }
}
```

### Notes

- Items are ordered by `total_cost` descending (highest cost first)
- `share_pct` values sum to 100% (within rounding tolerance)
- `totals.total_cost` equals the sum of all `items[].total_cost`
- If `basis_unit` is not provided, all basis units are included

### Examples

```bash
# All cost centers, all basis units
curl "http://localhost:8000/api/v1/kpis/company/cost-structure/?month=2026-01&company_id=1" \
  -H "Cookie: sessionid=<session>"

# KM basis only
curl "http://localhost:8000/api/v1/kpis/company/cost-structure/?month=2026-01&basis_unit=KM&company_id=1" \
  -H "Cookie: sessionid=<session>"
```

---

## 3. Trend

**Endpoint:** `GET /api/v1/kpis/company/trend/`

Time-series cost trend. Returns a series of buckets (by month or week) with aggregated cost metrics.

### Additional Parameters

| Parameter | Type | Default | Description |
|---|---|---|---|
| `grain` | `month`\|`week` | `month` | Time bucket size |

### Response

```json
{
  "meta": {
    "schema": "kpi-v1",
    "period_start": "2026-01-01",
    "period_end": "2026-02-28",
    "grain": "month",
    "basis_unit": "KM"
  },
  "series": [
    {
      "period_start": "2026-01-01",
      "period_end": "2026-01-31",
      "total_cost": "1300.00",
      "total_units": "500.000",
      "avg_rate": "2.6"
    },
    {
      "period_start": "2026-02-01",
      "period_end": "2026-02-28",
      "total_cost": "900.00",
      "total_units": "450.000",
      "avg_rate": "2"
    }
  ]
}
```

### Grain Behavior

- **`month`**: Buckets align to calendar months. A 3-month range produces 3 buckets.
- **`week`**: Buckets align to ISO weeks (Monday–Sunday). Partial weeks at boundaries are included.

### Examples

```bash
# Monthly trend for Q1 2026
curl "http://localhost:8000/api/v1/kpis/company/trend/?period_start=2026-01-01&period_end=2026-03-31&grain=month&company_id=1" \
  -H "Cookie: sessionid=<session>"

# Weekly trend for January 2026
curl "http://localhost:8000/api/v1/kpis/company/trend/?month=2026-01&grain=week&company_id=1" \
  -H "Cookie: sessionid=<session>"
```

---

## Error Responses

All endpoints return consistent error responses:

| Status | Condition |
|---|---|
| `400` | Invalid date format, invalid date range, invalid basis_unit, invalid grain, invalid group_by |
| `403` | Unauthenticated, non-staff user, or non-superuser specifying company_id |
| `404` | Company not found |

**Error response format:**
```json
{"error": "Human-readable error message"}
```

---

## Decimal Serialization

All monetary and rate values are serialized as **strings** (not numbers) for JSON safety:
- `"1300.00"` not `1300.0`
- `"2.000000"` not `2.0`

This is consistent with the `/history/` endpoint and different from the `/run/` endpoint (which returns numbers).

---

## Guardrails

- ✅ Never calls `calculate_company_costs()` or any cost engine pipeline
- ✅ Reads only from `CostRateSnapshot` (persisted data)
- ✅ All queries run inside `tenant_context(company)`
- ✅ Uses `CompanyScopedManager` (scoped to current tenant)
- ✅ No `all_objects` usage in service layer

---

## Test Coverage

35 tests in `tests/test_kpi_endpoints.py`:
- Auth/permissions for all 3 endpoints
- Default period (previous month) for all 3 endpoints
- `month=YYYY-MM` shortcut for all 3 endpoints
- Tenant isolation for all 3 endpoints
- Aggregation math verification (summary, structure, trend)
- `grain` validation (trend)
- `basis_unit` validation
- `group_by` validation (structure)
- Date validation errors

---

*GreekFleet 360 KPI API v1 | Last updated: 2026-02-20*
