# Project Workspace Shell

Status: `Not Started`
Owner: `wwwer`
Severity summary: `P0: 0 | P1: 0 | P2: 0`

## Scope

- [ ] `/projects/:projectId`
- [ ] project-level sidebar/header/breadcrumbs
- [ ] project overview page
- [ ] project route navigation
- [ ] project-level access handling

## Entry Points

- [ ] Open a project from `/projects`
- [ ] Direct deep link into project routes
- [ ] Breadcrumb and sidebar navigation within project

## Happy Path

- [ ] Project overview loads
- [ ] Project navigation between tabs works
- [ ] Header/breadcrumb/context reflect the active project
- [ ] Refresh inside project routes works

## Validation And Failure Paths

- [ ] Non-member access behavior checked
- [ ] Deleted project access behavior checked
- [ ] Broken project ID behavior checked

## Empty, Loading, And Refresh States

- [ ] Initial project load state checked
- [ ] Missing-access state checked
- [ ] Refresh on nested routes checked

## Permissions And Roles

- [ ] Non-member blocked clearly
- [ ] Viewer/member/manager/owner navigation exposure checked

## UX And Visual Review

- [ ] Header is understandable
- [ ] Project context is always obvious
- [ ] Navigation feels stable and predictable
- [ ] Presence/realtime indicators are understandable

## Responsive Review

- [ ] Desktop project shell checked
- [ ] Mobile project shell checked
- [ ] Sidebar/header behavior on small screens checked

## Test Coverage

- [ ] Project layout coverage reviewed
- [ ] Route-level regression gaps listed

## Issues Found

| ID | Severity | Area | Problem | Expected | Notes |
| --- | --- | --- | --- | --- | --- |
| | | | | | |

## Re-Review

- [ ] Project shell navigation retested
- [ ] Access handling retested

## Exit Criteria

- [ ] Entering and moving around a project feels trustworthy
- [ ] No open `P0` shell/navigation issues remain
