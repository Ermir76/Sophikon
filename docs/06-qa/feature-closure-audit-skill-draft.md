# Feature Closure Audit Skill Draft

Proposed target path when moved into the project skill system:

- `.codex/skills/feature-closure-audit/SKILL.md`

---

```md
---
name: feature-closure-audit
description: Run a strict feature closure audit for Sophikon. Use when the user wants confidence that a feature is truly done, stable, demo-safe, and unlikely to need rework. Start from the user-facing feature, then trace frontend behavior, state, API usage, backend logic, repository/query behavior, schema/model constraints, permissions, time handling, persistence, and tests until the feature can be marked Closed or Failed Audit.
---

# Feature Closure Audit

This skill is for closing a feature with confidence, not just reviewing it.

A feature is only complete when the user-facing flow works and the underlying logic is trustworthy enough that we should not expect to revisit it unless requirements change.

## Read First

Always load:

1. `AGENTS.md`
2. `docs/06-qa/00-master-review-plan.md`
3. `docs/06-qa/01-feature-audits/README.md`
4. the matching file in `docs/06-qa/01-feature-audits/`
5. `frontend/src/app/App.tsx`

Then load only the relevant implementation context for the feature:

- matching `frontend/src/features/{feature}/`
- shared layout/shell files that affect the feature
- matching backend endpoints, services, repositories, and models when the feature depends on them

Load these as needed:

- `docs/02-design/03-frontend-architecture.md`
- `docs/02-design/08-api-specification.md`
- `docs/02-design/10-security-design.md`
- `docs/05-standards/01-backend-standards.md`
- `docs/05-standards/02-frontend-standards.md`
- `docs/05-standards/05-ux-standards.md`
- `docs/06-qa/qa-checklist.md`
- `docs/06-qa/ux-review-2026-03-26.md`

## Feature File Map

- Auth -> `docs/06-qa/01-feature-audits/auth.md`
- Dashboard -> `docs/06-qa/01-feature-audits/dashboard.md`
- Projects -> `docs/06-qa/01-feature-audits/projects.md`
- Project shell / workspace -> `docs/06-qa/01-feature-audits/project-workspace-shell.md`
- Tasks -> `docs/06-qa/01-feature-audits/tasks.md`
- Kanban -> `docs/06-qa/01-feature-audits/kanban.md`
- Gantt -> `docs/06-qa/01-feature-audits/gantt.md`
- Resources / Utilization -> `docs/06-qa/01-feature-audits/resources.md`
- Calendar -> `docs/06-qa/01-feature-audits/calendar.md`
- Reports -> `docs/06-qa/01-feature-audits/reports.md`
- Notifications -> `docs/06-qa/01-feature-audits/notifications.md`
- Settings -> `docs/06-qa/01-feature-audits/settings.md`
- AI panel -> `docs/06-qa/01-feature-audits/ai-panel.md`

If no file fits, start from:

- `docs/06-qa/01-feature-audits/_template.md`

## Audit Goal

The audit should end with one of these outcomes:

- `Closed`
- `Failed Audit`

Do not use vague success language.

## Audit Sequence

Run the feature in this order:

1. Define feature boundary
2. Verify critical user promises
3. Run the happy path
4. Run failure and recovery paths
5. Run role and permission checks
6. Run correctness checks
7. Trace backend / logic chain
8. Check refresh / persistence / realtime behavior
9. Review test coverage and regression risk
10. Apply the closure gate

## What To Check

### Feature Boundary

- where the feature starts
- where it ends
- included routes, dialogs, panels, and actions
- excluded adjacent behavior

### Critical User Promises

Identify the small number of promises that must be true for the feature to deserve trust.

Examples:
- notifications appear promptly and accurately
- comments render in the right order and thread correctly
- scheduling output is logically correct, not just visually rendered

### Happy Path

- main user goal works end-to-end
- success state is visible
- result survives refresh where expected

### Failure and Recovery

- empty input
- invalid input
- API/server failure
- bad deep link / missing resource / deleted resource
- recovery path after failure

### Permissions and Roles

- correct behavior for viewer/member/manager/owner where relevant
- hidden or disabled actions match access rules
- unauthorized actions fail clearly

### Correctness Checks

Always check these when relevant:

- timestamps and timezone correctness
- sorting and filtering correctness
- calculations and derived values
- state transitions
- status labels matching actual state
- comment/thread integrity
- unread/read counts
- schedule/dependency logic
- any other domain rule the feature depends on

### Backend / Logic Trace

Trace the full chain as needed:

- UI
- frontend state/query/cache
- API contract
- backend endpoint
- service logic
- repository/query logic
- models/schemas/constraints

This skill is not limited to UI/UX. It follows the feature down to the root cause.

### Refresh / Persistence / Realtime

- page refresh keeps or restores correct state
- stale cache risks checked
- websocket/realtime sync checked where relevant

### Test Coverage

- what automated tests already protect the feature
- what high-risk behavior is still untested
- what should be added before calling it truly closed

## Findings Standard

Record every issue with:

- `ID`
- `Severity`
- `Area`
- `Problem`
- `Expected`
- `Notes`

Severity rules:

- `P0`: demo-breaking, trust-breaking, data-loss/security, or the feature cannot complete its main job
- `P1`: confusing, rough, misleading, inconsistent, or obviously embarrassing
- `P2`: polish or non-blocking cleanup

## Required Output Behavior

When asked to audit a feature:

1. State which audit file you are using.
2. Summarize the feature boundary in 1-3 lines.
3. Present findings first, ordered by severity.
4. State whether the feature currently `Passed` or `Failed` the closure audit.
5. End with:
   - current status
   - open `P0/P1/P2` counts
   - next action

## Updating The Audit File

If maintaining the review docs:

- update `Status`
- update `Severity summary`
- fill only the checkboxes actually verified
- add rows to `Issues Found`
- use `Failed Audit` when trust is not yet earned
- only mark `Closed` when the closure gate genuinely passes

## Closure Gate

A feature may be marked `Closed` only if:

- feature boundary is clear
- critical user promises are verified
- happy path works end-to-end
- no open `P0` remains
- correctness checks passed
- backend / logic trace leaves no unresolved trust-breaking issue
- refresh / persistence / realtime behavior is acceptable
- role checks are correct
- test gaps are listed
- re-review passed after fixes

## Good Outcome

A good run of this skill leaves behind:

- one updated feature audit file
- a realistic feature status
- a short prioritized gap list
- a trustworthy decision: `Closed` or `Failed Audit`
```
