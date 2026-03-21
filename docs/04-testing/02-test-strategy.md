# Test Strategy

**Version:** 1.0
**Date:** 2026-03-20

---

## Goal

Tests shall provide confidence that the system works correctly, not that lines of code were executed. Coverage numbers are a secondary metric. Risk coverage is primary.

---

## Risk-Based Prioritization

Not all code carries equal risk. Test effort shall be allocated by blast radius — how much breaks if this code is wrong.

| Risk level | Examples                                                         | Test depth                             |
| ---------- | ---------------------------------------------------------------- | -------------------------------------- |
| Critical   | Scheduling engine, task rollup, auth tokens                      | Full unit + integration coverage       |
| High       | Dependency validation, hierarchy operations, resource allocation | Unit coverage + key integration flows  |
| Medium     | CRUD endpoints, member management, notifications                 | API unit tests, happy path integration |
| Low        | UI layout, loading states, empty states                          | Minimal frontend unit tests            |

---

## Coverage Targets

Coverage targets shall be defined per layer, not as a single global number.

| Layer                              | Target                                   |
| ---------------------------------- | ---------------------------------------- |
| Backend service — critical modules | 95%+ branch coverage                     |
| Backend service — standard modules | 80%+ branch coverage                     |
| Backend API endpoints              | 100% of endpoints have at least one test |
| Integration flows                  | All cross-service side effects covered   |
| Frontend components                | Happy path + error state per component   |
| E2E                                | Critical user journeys only              |

---

## Critical Modules

### Scheduling Engine

The CPM scheduler shall have the deepest unit coverage in the codebase. Its errors are silent — a wrong date propagates through the entire WBS without raising an exception.

Coverage shall include all dependency types (FS, SS, FF, SF), all eight constraint types, forward and backward passes, slack calculation, critical path identification, summary task rollup, and calendar-aware scheduling.

### Auth and Token Security

Auth token behavior shall be tested at the service layer, not only through the API. Coverage shall include refresh token rotation, family revocation on reuse detection, token expiry, and malformed token rejection.

### Task Hierarchy and Rollup

Indent, outdent, and reorder operations shall be covered at the service layer. Summary task aggregation (dates, progress, cost, critical flag) shall be covered end-to-end including multi-level WBS propagation.

---

## Integration Flow Coverage

Integration tests shall cover every cross-service side effect:

- Schedule recalculation triggered by task changes, dependency changes, and calendar changes
- Summary rollup triggered by child create, update, and delete
- Notification creation on task assignment and comment mention
- Resource assignment cleanup on resource delete

---

## Frontend Testing Scope

Frontend tests shall focus on behavior visible to the user:

- Does the component render the correct data from the API response?
- Does the error state appear when the API call fails?
- Does the user action trigger the correct mutation?

Tests shall not assert on CSS classes, component internals, or implementation details invisible to the user.

---

## E2E Scope

E2E tests shall cover the critical user journeys only:

- Authentication (login, logout, password reset)
- Core task management (create, edit, reorder, complete)
- Gantt chart interaction (zoom, drag, dependency creation)
- Resource assignment

Exhaustive E2E coverage is not the goal. E2E tests are expensive to maintain and shall be reserved for flows where unit and integration tests cannot provide sufficient confidence.

---

## CI Gates

The following shall pass before any merge:

- All backend unit and integration tests pass
- All frontend unit tests pass
- E2E critical path suite passes

---

## Related Docs

- Infrastructure and tooling → `01-test-architecture.md`
