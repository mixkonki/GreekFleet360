---
name: greekfleet-pr-discipline
description: Enforces consistent commits/PRs for GreekFleet360 with tenant safety, migrations, tests, and rollback notes.
---

You are contributing to GreekFleet360. Always produce clean, reviewable changes.

WHEN COMPLETING ANY TASK:
You MUST provide:
1) A short summary of what changed
2) Files changed list (grouped by layer: models, views, templates, tests)
3) Migration notes (what migrations, and why safe)
4) Test evidence (command + result)
5) Rollback plan (how to revert safely)

COMMIT RULES:
- Keep diffs small and focused.
- Prefer one feature per commit/PR.
- Use descriptive messages (imperative tone).
- Never commit secrets (.env, db.sqlite3, .venv).

PR TEMPLATE (use this structure):
Title:
- <Area>: <Short summary>

Description:
- Context / Goal
- What changed
- Tenant safety notes
- Migration notes
- Tests run
- Screens/UI verified

CHECKLIST (must tick mentally):
- [ ] request.company not bypassed
- [ ] No company accepted from payload
- [ ] Orphan users handled (403 where relevant)
- [ ] Cross-tenant access blocked (where relevant)
- [ ] Migrations safe and applied
- [ ] Templates/forms/views updated for model changes
- [ ] python manage.py test is green
- [ ] No dead imports / no broken pages

ROLLBACK NOTES:
- Mention the git command(s) to revert:
  git revert <commit>
  OR reset to baseline tag if needed:
  git checkout v0.1-tenant-foundation

If any checklist item is missing, stop and ask for what is needed.
VERIFICATION RULE
- Never say "already completed" unless you confirm on the current branch with:
  - git status (clean or expected staged files)
  - python manage.py test output (green)