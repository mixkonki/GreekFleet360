---
name: greekfleet-search-and-sweep
description: Standard "before done" sweep to catch dead references, broken pages, and regressions in GreekFleet360.
---

Before marking any task "done", run a sweep.

1) SEARCH FOR BROKEN REFERENCES
- If you removed/renamed fields/classes, run ripgrep:
  rg "<old_name>" .
- Common hotspots:
  - web/forms.py
  - web/views.py
  - web/templates/
  - admin registrations
  - tests/

2) DJANGO CHECKS
- python manage.py check

3) MIGRATIONS
- Ensure migrations exist and apply cleanly:
  python manage.py migrate

4) SMOKE PAGES (manual or basic verification guidance)
- /finance/settings/ (tabs: expenses, cost centers, personnel)
- transport order list
- transport order detail page
- any page touched by the change

5) TESTS
- python manage.py test
- If full suite is too slow during iteration, run targeted tests first, but full suite must be green before final.

If any step fails, stop and fix before proceeding.