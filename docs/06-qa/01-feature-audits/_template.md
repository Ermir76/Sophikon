# Feature Name

Status: `In Audit`
Owner: `wwwer`
Severity summary: `P0: 0 | P1: 0 | P2: 0`

## Review State Legend

- `PASS`: reviewed and acceptable
- `FAIL`: reviewed and not acceptable
- `NOT CHECKED`: not reviewed yet
- `BLOCKED`: could not be signed off because another issue prevented meaningful verification

Rule: every audit line must use one of these states. Never rely on a bare unchecked checkbox.

## Boundary Notes

- Summarize the exact feature boundary in 1-3 lines.
- State what is included.
- State what is explicitly out of scope.

## Critical User Promises

- List the 3-5 promises this feature must keep to deserve trust.

## Review Matrix

### Feature Boundary

| Item | State | Evidence / Notes |
| --- | --- | --- |
| Exact screens, routes, dialogs, and panels included are defined | `NOT CHECKED` | |
| Out-of-scope adjacent behavior is defined | `NOT CHECKED` | |
| Feature start point for the user is clear | `NOT CHECKED` | |
| Feature end point for the user is clear | `NOT CHECKED` | |

### Entry Points

| Item | State | Evidence / Notes |
| --- | --- | --- |
| All routes, buttons, menus, and deep links into the feature are listed | `NOT CHECKED` | |

### Happy Path

| Item | State | Evidence / Notes |
| --- | --- | --- |
| Main happy path works end-to-end | `NOT CHECKED` | |
| Success state is clear | `NOT CHECKED` | |
| Data persists after refresh if expected | `NOT CHECKED` | |
| Navigation after success makes sense | `NOT CHECKED` | |

### Validation And Failure Paths

| Item | State | Evidence / Notes |
| --- | --- | --- |
| Empty input states checked | `NOT CHECKED` | |
| Invalid input states checked | `NOT CHECKED` | |
| API/server failure path checked | `NOT CHECKED` | |
| User can recover from failure | `NOT CHECKED` | |
| Error copy is understandable | `NOT CHECKED` | |

### Empty, Loading, And Refresh States

| Item | State | Evidence / Notes |
| --- | --- | --- |
| Loading state is visible and not confusing | `NOT CHECKED` | |
| Empty state is intentional and helpful | `NOT CHECKED` | |
| Refresh behavior does not break state | `NOT CHECKED` | |

### Correctness Checks

| Item | State | Evidence / Notes |
| --- | --- | --- |
| Sorting and filtering are correct where relevant | `NOT CHECKED` | |
| Derived values and calculations are correct where relevant | `NOT CHECKED` | |
| Status transitions are valid where relevant | `NOT CHECKED` | |
| Timestamps and timezones are correct where relevant | `NOT CHECKED` | |

### Data / Time / State Integrity

| Item | State | Evidence / Notes |
| --- | --- | --- |
| Cache invalidation / stale data risks checked | `NOT CHECKED` | |
| Persistence after refresh checked | `NOT CHECKED` | |
| Realtime/websocket behavior checked where relevant | `NOT CHECKED` | |
| Invalid data states are prevented or handled safely | `NOT CHECKED` | |

### Backend / Logic Trace

| Item | State | Evidence / Notes |
| --- | --- | --- |
| Relevant API endpoints checked | `NOT CHECKED` | |
| Relevant backend service logic checked | `NOT CHECKED` | |
| Relevant repository/query logic checked | `NOT CHECKED` | |
| Relevant schema/model constraints checked | `NOT CHECKED` | |

### Permissions And Roles

| Item | State | Evidence / Notes |
| --- | --- | --- |
| Role differences were checked where relevant | `NOT CHECKED` | |
| Authorized actions work | `NOT CHECKED` | |
| Unauthorized actions are blocked clearly | `NOT CHECKED` | |
| UI does not expose misleading actions | `NOT CHECKED` | |

### UX And Visual Review

| Item | State | Evidence / Notes |
| --- | --- | --- |
| Primary action is obvious | `NOT CHECKED` | |
| Labels are human-readable | `NOT CHECKED` | |
| Important content is visible | `NOT CHECKED` | |
| Layout is not cramped or confusing | `NOT CHECKED` | |
| Feedback is timely and understandable | `NOT CHECKED` | |

### Responsive Review

| Item | State | Evidence / Notes |
| --- | --- | --- |
| Desktop checked | `NOT CHECKED` | |
| Mobile checked | `NOT CHECKED` | |
| Overflow, clipping, and touch target problems checked | `NOT CHECKED` | |

### Test Coverage

| Item | State | Evidence / Notes |
| --- | --- | --- |
| Existing automated coverage reviewed | `NOT CHECKED` | |
| Missing high-risk test cases listed | `NOT CHECKED` | |

## Issues Found

| ID | Severity | Area | Problem | Expected | Notes |
| --- | --- | --- | --- | --- | --- |
| | | | | | |

## Re-Review

| Item | State | Evidence / Notes |
| --- | --- | --- |
| All `P0` items retested | `NOT CHECKED` | |
| Important `P1` items retested | `NOT CHECKED` | |
| No regression introduced by fixes | `NOT CHECKED` | |

## Closure Gate

| Item | State | Evidence / Notes |
| --- | --- | --- |
| Feature boundary is clear | `NOT CHECKED` | |
| Critical user promises are satisfied | `NOT CHECKED` | |
| Happy path is reliable | `NOT CHECKED` | |
| No open `P0` issues remain | `NOT CHECKED` | |
| Correctness checks passed | `NOT CHECKED` | |
| Data / time / state integrity is acceptable | `NOT CHECKED` | |
| Backend / logic trace leaves no unresolved trust-breaking risk | `NOT CHECKED` | |
| Key UX blockers are addressed or explicitly accepted | `NOT CHECKED` | |
| Remaining gaps are documented | `NOT CHECKED` | |
| Feature can be demonstrated without embarrassment-level failure | `NOT CHECKED` | |
| Feature is safe to mark `Closed` | `NOT CHECKED` | |
