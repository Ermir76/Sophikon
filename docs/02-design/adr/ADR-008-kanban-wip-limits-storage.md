# ADR-008: Persist Kanban WIP Limits in Backend Project Settings

- Status: [CONFIRMED]
- Date: 2026-03-23

## Context

`KB-03` (FR-KB-010) requires per-column WIP limits that persist across sessions. The open design choice was where to store the limits:

- local browser storage (`localStorage`) per project
- backend persistence on the project

The product is collaborative and can be accessed from multiple browsers/devices. Browser-local storage does not follow the user or project across environments.

## Decision

Store WIP limits in backend project settings under:

- `project.settings.kanban_wip_limits`

Frontend still keeps a local UI copy in the kanban store for immediate rendering, but source-of-truth persistence is backend project settings via `PATCH /projects/{id}`.

## Consequences

### Positive

- WIP limits survive browser/device changes.
- Configuration is project-scoped and shared for all project members with update permission.
- No new DB table or migration required (reuses existing JSONB settings column).

### Tradeoffs

- Project settings schema must explicitly allow the new key.
- Kanban page now depends on project settings fetch/update path for persistence.
