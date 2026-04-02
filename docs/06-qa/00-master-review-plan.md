# Master Review Plan

Purpose: run a strict, feature-by-feature closure audit across the whole product until each feature can be trusted as truly done, stable, and demo-safe.

Use this folder as the source of truth for the review effort. Do not keep findings in chat only.

Related docs:
- `docs/06-qa/qa-checklist.md`
- `docs/06-qa/ux-review-2026-03-26.md`
- `docs/06-qa/01-feature-audits/`

## Review State Legend

Every audit item must use an explicit review state:

- `PASS`: reviewed and acceptable
- `FAIL`: reviewed and not acceptable
- `NOT CHECKED`: not reviewed yet
- `BLOCKED`: could not be signed off because another issue prevented meaningful verification

Rule: never rely on a plain unchecked box without explaining whether it means `FAIL`, `NOT CHECKED`, or `BLOCKED`.

## Goal

By the end of this review program, every major feature should have:
- a documented feature boundary
- critical user promises listed explicitly
- a tested happy path
- checked failure, recovery, loading, and empty states
- reviewed permissions and role behavior where relevant
- correctness checks for time, state, calculations, and persistence
- backend and logic trace completed where needed
- responsive validation for desktop and mobile
- known gaps recorded with severity
- an explicit closure gate marked complete

## Review Workflow

For each feature:

1. Read the feature audit file.
2. Execute the review in this order:
   - Feature boundary
   - Critical user promises
   - Happy path
   - Validation and error paths
   - Empty and loading states
   - Permissions and role variants
   - Correctness checks
   - Data / time / state integrity
   - Backend / logic trace
   - Visual clarity and UX
   - Responsive behavior
   - Persistence and refresh behavior
   - Regression risk and test gaps
3. Record every issue directly in the feature file.
4. Give each issue a severity:
   - `P0`: demo-breaking, trust-breaking, or data-loss/security risk
   - `P1`: confusing, ugly, inconsistent, or recovery is weak
   - `P2`: polish or non-blocking cleanup
5. Do not mark the feature complete until the closure gate passes.

## Feature Order

Recommended review order:

1. Authentication
2. Dashboard
3. Projects
4. Project Workspace Shell
5. Tasks
6. Kanban
7. Gantt
8. Resources
9. Calendar
10. Reports
11. Notifications
12. Settings
13. AI Panel

Reasoning:
- Start with access and session trust.
- Then validate core entry and navigation flows.
- Then review the main project execution surfaces.
- Leave secondary/supporting features after the core app is stable.

## Definition Of Closed

A feature is only `Closed` when all of these are true:

- `PASS` Feature boundary is clear.
- `PASS` Critical user promises are verified.
- `PASS` Primary happy path works end-to-end.
- `PASS` No untriaged `P0` issues remain.
- `PASS` Error, empty, and loading states are acceptable.
- `PASS` Correctness checks passed for the feature.
- `PASS` Data, time, and state integrity are acceptable.
- `PASS` Backend / logic trace found no unresolved trust-breaking issue.
- `PASS` Refresh/persistence behavior is verified where relevant.
- `PASS` Mobile and desktop behavior were both checked where relevant.
- `PASS` Relevant permissions/roles were checked where relevant.
- `PASS` Test gaps are listed.
- `PASS` Remaining `P1` and `P2` items are explicitly documented.
- `PASS` Re-review passed after fixes.

## Status Model

Use one of these statuses per feature:

- `In Audit`
- `Failed Audit`
- `Fixes In Progress`
- `Ready For Re-Review`
- `Closed`

## Evidence Rules

Every important finding should include:
- what the user did
- what happened
- what should have happened
- severity
- optional screenshot/video note

Every fixed item should later include:
- fix reference
- verification note
- re-test result

## Suggested Daily Rhythm

1. Pick one feature.
2. Finish the audit for that feature in one sitting if possible.
3. Decide honestly: `Failed Audit` or `Ready For Re-Review`.
4. Fix the highest-severity problems first.
5. Re-review the same feature.
6. Move to the next feature.

## Folder Structure

- `docs/06-qa/00-master-review-plan.md`
- `docs/06-qa/01-feature-audits/README.md`
- `docs/06-qa/01-feature-audits/_template.md`
- `docs/06-qa/01-feature-audits/*.md`

## Notes

- Keep this system simple enough that you actually use it.
- Record reality, not hope.
- A feature can fail audit and still be recoverable. The point is to make the gap visible and finite.
