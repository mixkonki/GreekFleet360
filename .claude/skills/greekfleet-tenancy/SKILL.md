---
name: django-safe-migrations
description: Ensures safe schema evolution and data integrity in GreekFleet360 migrations.
---

When modifying Django models:

SAFETY PRINCIPLES:

1. Never remove fields before checking data usage.
2. Always check existing records before FK changes.
3. Prefer additive migrations over destructive ones.
4. Maintain backward compatibility when possible.

WORKFLOW:

Step 1: Inspect existing data.
Step 2: Add new nullable field.
Step 3: Data migration (if needed).
Step 4: Update code usage.
Step 5: Remove old field later.

TEST REQUIREMENTS:
- Run full test suite after migrations.
- Verify tenant isolation still holds.
- Ensure serializers still validate.

If migration risk exists:
propose phased migration instead of direct change.