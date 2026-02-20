# Seed Cost Engine Demo Report

## Summary

Successfully created repeatable demo dataset for Cost Engine testing. The debug endpoint now shows non-zero rates and at least 1 breakdown with realistic profitability data.

## Management Command Created

**File:** `finance/management/commands/seed_cost_engine_demo.py`

**Usage:**
```bash
python manage.py seed_cost_engine_demo [options]
```

**Options:**
- `--company-id` - Company ID (default: first company)
- `--period-start` - Period start YYYY-MM-DD (default: 2026-01-01)
- `--period-end` - Period end YYYY-MM-DD (default: 2026-01-31)
- `--vehicle-km` - Vehicle kilometers (default: 500)
- `--order-revenue` - Order revenue (default: 2000)
- `--vehicle-cost` - Vehicle cost posting (default: 1000)
- `--overhead-cost` - Overhead cost posting (default: 300)

## Objects Created

### Test Run Results (Company: Met IKE, ID: 1)

**Period:** 2026-01-01 to 2026-01-31

| Object Type | Details | ID |
|-------------|---------|-----|
| Vehicle | DEMO-001 (Mercedes Actros) | 3 |
| CostCenter (VEHICLE) | CC-DEMO-001 | 9 |
| CostCenter (OVERHEAD) | Overhead-General | 10 |
| CostItem (Vehicle) | Vehicle Operating Cost | 2 |
| CostItem (Overhead) | General Overhead | 3 |
| CostPosting (Vehicle) | €1000 for period | 2 |
| CostPosting (Overhead) | €300 for period | 3 |
| TransportOrder | Athens → Thessaloniki, 500km, €2000 | 1 |

## Cost Engine Calculation Results

### Summary Statistics
```
Total Snapshots: 8
Total Breakdowns: 1
Total Cost: €1300.00
Total Revenue: €2000.00
Total Profit: €700.00
Average Margin: 35.00%
```

### Sample Snapshots
```
CC-DEMO-001 (VEHICLE): €2.0000/KM [OK]
DEMO-001 - Mercedes (OTHER): €0.0000/KM [OK]
```

**Rate Calculation:**
- Vehicle cost: €1000
- Distance: 500 km
- Rate: €1000 / 500km = €2.00/km ✅

### Sample Breakdown
```
Order ID: 1
Total Cost: €1300.00
Revenue: €2000.00
Profit: €700.00
Margin: 35.00%
```

**Breakdown Calculation:**
- Vehicle allocation: 500km × €2.00/km = €1000
- Overhead allocation: €2000 × 15% = €300
- Total cost: €1300
- Profit: €2000 - €1300 = €700
- Margin: (€700 / €2000) × 100 = 35% ✅

## Debug Endpoint Verification

**URL:** `http://127.0.0.1:8000/finance/debug/cost-engine/`

**Status:** ✅ **200 OK**

**Response Structure:**
```json
{
  "meta": {
    "schema_version": 1,
    "engine_version": "dev",
    "company_id": 1,
    "period_start": "2026-01-01",
    "period_end": "2026-01-31",
    "generated_at": "2026-02-19T20:18:36.640+00:00"
  },
  "snapshots": [
    {
      "cost_center_id": 9,
      "cost_center_name": "CC-DEMO-001",
      "cost_center_type": "VEHICLE",
      "basis_unit": "KM",
      "total_cost": 1000.0,
      "total_units": 500.0,
      "rate": 2.0,
      "status": "OK"
    },
    {
      "cost_center_id": 10,
      "cost_center_name": "Overhead-General",
      "cost_center_type": "OVERHEAD",
      "basis_unit": "REVENUE",
      "total_cost": 300.0,
      "total_units": 2000.0,
      "rate": 0.15,
      "status": "OK"
    },
    ...
  ],
  "breakdowns": [
    {
      "order_id": 1,
      "order_ref": "Demo Customer - Athens → Thessaloniki - 2026-01-01",
      "vehicle_alloc": 1000.0,
      "overhead_alloc": 300.0,
      "direct_cost": 0.0,
      "total_cost": 1300.0,
      "revenue": 2000.0,
      "profit": 700.0,
      "margin": 35.0,
      "status": "OK"
    }
  ],
  "summary": {
    "total_snapshots": 8,
    "total_breakdowns": 1,
    "total_cost": 1300.0,
    "total_revenue": 2000.0,
    "total_profit": 700.0,
    "average_margin": 35.0
  }
}
```

## Model Field Assumptions

### TransportOrder
- `date` field used for order date (falls within period)
- `distance_km` field for kilometers
- `agreed_price` field for revenue
- `assigned_vehicle` FK to Vehicle model
- `status` field (set to 'COMPLETED')

### CostPosting
- Uses `period_start` and `period_end` (NOT "period")
- Requires FK to `CostCenter` and `CostItem`
- `amount` field for cost value

### CostCenter
- `type` field with choices: VEHICLE, OVERHEAD, etc.
- `vehicle` FK (nullable) for linking to Vehicle
- `is_active` boolean flag

## Tenant Isolation

✅ All operations executed inside `tenant_context(company)`
✅ Uses scoped managers (`objects`) throughout
✅ No bypass manager usage in service code
✅ Proper data isolation maintained

## Conclusion

✅ Demo dataset successfully created
✅ Cost Engine produces non-zero rates
✅ At least 1 breakdown with realistic profitability (35% margin)
✅ Debug endpoint returns valid schema v1 JSON
✅ All calculations respect tenant isolation

**Status:** ✅ **DEMO DATASET OPERATIONAL**
