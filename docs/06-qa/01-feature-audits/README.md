# Feature Audits

This folder breaks the application review into one file per feature.

Use these files to:
- run the review
- capture issues
- track retesting
- decide when a feature is actually safe

## How To Read An Audit File

Each audit item should use one of these states:

- `PASS`: this item was reviewed and signed off
- `FAIL`: this item was reviewed and did not pass
- `NOT CHECKED`: this item was not reviewed yet
- `BLOCKED`: this item could not be signed off because another issue blocked meaningful verification

Important:

- `PASS` means "audited and okay"
- `FAIL` means "audited and not okay"
- `NOT CHECKED` means "not yet audited"
- `BLOCKED` means "cannot honestly sign off yet"

Do not interpret a missing checkmark as meaning any one of those by default. The audit file should say which one it is.

Working rule:
- one feature file owns the truth for that feature
- do not spread the same findings across multiple random notes

Current audit files:
- `auth.md`
- `dashboard.md`
- `projects.md`
- `project-workspace-shell.md`
- `tasks.md`
- `kanban.md`
- `gantt.md`
- `resources.md`
- `calendar.md`
- `reports.md`
- `notifications.md`
- `settings.md`
- `ai-panel.md`

Reference docs:
- `docs/06-qa/00-master-review-plan.md`
- `docs/06-qa/qa-checklist.md`
- `docs/06-qa/ux-review-2026-03-26.md`
