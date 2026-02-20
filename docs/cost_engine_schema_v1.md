# Cost Engine Schema v1

## Overview

The Cost Engine calculates cost rates per cost center and order profitability breakdowns. All calculations must run within `tenant_context(company)` to ensure proper tenant isolation.

## Result Contract

The Cost Engine returns a dictionary with the following top-level keys:

```python
{
    "meta": {...},           # Calculation metadata
    "snapshots": [...],      # Cost rate snapshots per cost center
    "breakdowns": [...],     # Order cost breakdowns
    "summary": {...}         # Aggregated summary statistics
}
```

## Meta Fields

The `meta` object contains calculation metadata:

| Field | Type | Description |
|-------|------|-------------|
| `schema_version` | str | Schema version (currently "1.0") |
| `company_id` | int | Company ID for which calculation was performed |
| `period_start` | str | Period start date (ISO 8601: YYYY-MM-DD) |
| `period_end` | str | Period end date (ISO 8601: YYYY-MM-DD) |
| `calculated_at` | str | Timestamp when calculation was performed (ISO 8601) |
| `basis_unit` | str | Primary basis unit used for allocation |

## Snapshots

Each snapshot represents calculated cost rates for a cost center:

```python
{
    "cost_center_id": int,
    "basis_unit": str,        # KM, HOUR, TRIP, or REVENUE
    "total_cost": Decimal,
    "total_units": Decimal,
    "rate": Decimal,
    "status": str             # OK or MISSING_ACTIVITY
}
```

### Basis Units

| Unit | Description | Used For |
|------|-------------|----------|
| `KM` | Kilometers | Distance-based allocation |
| `HOUR` | Hours | Time-based allocation |
| `TRIP` | Trips | Per-trip allocation |
| `REVENUE` | Revenue | Revenue-based allocation |

### Status Rules

- **OK**: Normal calculation with activity data
- **MISSING_ACTIVITY**: Set when `total_units == 0` for KM, HOUR, or TRIP basis units

## Breakdowns

Each breakdown represents cost analysis for a transport order:

```python
{
    "order_id": int,
    "vehicle_alloc": Decimal,
    "overhead_alloc": Decimal,
    "direct_cost": Decimal,
    "total_cost": Decimal,
    "revenue": Decimal,
    "profit": Decimal,
    "margin": Decimal,
    "status": str             # OK or MISSING_RATE
}
```

## Summary

Aggregated statistics across all calculations:

```python
{
    "total_revenue": Decimal,
    "total_cost": Decimal,
    "total_profit": Decimal,
    "average_margin": Decimal,
    "order_count": int
}
```

## Tenant Context Requirement

**CRITICAL:** All Cost Engine operations must run within `tenant_context(company)`:

```python
from core.tenant_context import tenant_context
from finance.services.cost_engine.calculator import CostEngineCalculator

with tenant_context(company):
    calculator = CostEngineCalculator(company, period_start, period_end)
    result = calculator.calculate()
```

This ensures:
- Proper tenant isolation
- Scoped manager queries work correctly
- No cross-tenant data leakage

## Persistence

Results can be persisted using `CostEnginePersistence`:

```python
from finance.services.cost_engine.persist import CostEnginePersistence

with tenant_context(company):
    persistence = CostEnginePersistence()
    
    # Save snapshots
    persistence.save_cost_rate_snapshots(
        company, period_start, period_end, result["snapshots"]
    )
    
    # Save breakdowns
    persistence.save_order_cost_breakdowns(
        company, period_start, period_end, result["breakdowns"]
    )
```

## API Endpoint

### REST API (Production)

**Endpoint:** `GET /api/v1/cost-engine/run/`

**Authentication:** Required (Session or Token)
**Permission:** Staff or Superuser only

**Query Parameters:**

| Parameter | Required | Type | Description |
|-----------|----------|------|-------------|
| `period_start` | Yes | string | Period start date (YYYY-MM-DD) |
| `period_end` | Yes | string | Period end date (YYYY-MM-DD) |
| `company_id` | No | integer | Company ID (superuser only) |
| `only_nonzero` | No | boolean | Filter snapshots with cost/rate > 0 (0 or 1, default 0) |
| `include_breakdowns` | No | boolean | Include order breakdowns (0 or 1, default 1) |

**Example Request:**
```bash
curl -X GET "http://localhost:8000/api/v1/cost-engine/run/?period_start=2026-01-01&period_end=2026-01-31&company_id=1" \
  -H "Authorization: Session <session_cookie>" \
  -H "Content-Type: application/json"
```

**Example Response:**
```json
{
  "meta": {
    "schema_version": 1,
    "engine_version": "dev",
    "company_id": 1,
    "period_start": "2026-01-01",
    "period_end": "2026-01-31",
    "generated_at": "2026-02-19T20:48:00.000Z"
  },
  "snapshots": [...],
  "breakdowns": [...],
  "summary": {...}
}
```

**Response Codes:**
- `200 OK` - Successful calculation
- `400 Bad Request` - Invalid parameters
- `403 Forbidden` - Permission denied
- `404 Not Found` - Company not found

### Debug Endpoint (Development Only)

**Endpoint:** `GET /finance/debug/cost-engine/`

**Authentication:** None required
**Availability:** DEBUG mode only (returns 404 in production)

Uses first company in database with hardcoded period (2026-01-01 to 2026-01-31).

## Version History

- **v1.0** (2026-02-19): Initial schema with meta, snapshots, breakdowns, summary
