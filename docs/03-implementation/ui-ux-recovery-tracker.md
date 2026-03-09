# UI/UX Recovery Tracker (Evidence-Only)

Last updated: 2026-03-09
Owner: User + AI assistants
Authority:

- `docs/02-design/FRONTEND_STYLING_CONSTITUTION.md`
- `docs/02-design/frontend-architecture.md`

## Why This Version Exists

The previous tracker drifted and mixed facts, assumptions, and stale status notes.
This file is reset as an evidence-only tracker.

## Trust Contract (Mandatory)

Rules for all future updates:

1. No item is marked `verified` without explicit evidence.
2. Evidence must include:
   - date checked
   - checker
   - scope (page/component)
   - file paths touched or inspected
3. If evidence is missing, status stays `unverified`.
4. Do not carry forward old status lines without re-checking.

## Recovery Mode (Active)

- Foundation freeze:
  - avoid direct `frontend/src/shared/ui/*` edits in routine feature work
  - allow only dedicated UI-foundation changes
- Drift containment:
  - no route-scoped global styling hooks
  - no private visual systems inside feature folders
- Touched-surface migration:
  - when touching a screen, move toward shared adapters/primitives
  - do not mix old/new styling patterns in the same component

## Verification Board

Status values:

- `verified`: checked with explicit evidence
- `unverified`: not checked or evidence missing

| Surface                                               | Status     | Last check | Evidence | Next action                                         |
| ----------------------------------------------------- | ---------- | ---------- | -------- | --------------------------------------------------- |
| Projects page visual hierarchy                        | unverified | -          | -        | Manual UI pass in light/dark and desktop/mobile     |
| Dashboard visual hierarchy                            | unverified | -          | -        | Manual UI pass in light/dark and desktop/mobile     |
| Tasks page + task detail panel                        | unverified | -          | -        | Manual UI pass and interaction pass                 |
| Resources page + resource detail panel                | unverified | -          | -        | Manual UI pass and interaction pass                 |
| Members/settings pages density                        | unverified | -          | -        | Manual UI pass and compare against constitution     |
| Shared primitives consistency (`shared/ui`, adapters) | unverified | -          | -        | Audit touched components from last frontend changes |
| Sticky table header behavior                          | unverified | -          | -        | Verify on long datasets and small viewport          |

## Current Execution Order

1. Validate foundation ownership boundaries (`index.css`, `shared/ui`, adapters, features).
2. Run manual visual sweep on core routes (light/dark + responsive).
3. Record only evidence-backed `verified` entries in this tracker.
4. Open issues for anything that is still unverified or broken.

## Update Template

Use this exact template for each verified update:

```
### YYYY-MM-DD - <short title>
- Status: verified
- Checker: <name>
- Scope: <page/component>
- Files checked/touched:
  - <path>
  - <path>
- Result:
  - <fact 1>
  - <fact 2>
- Follow-up:
  - <if any>
```
