# ADR-005: Feature-Sliced Frontend Structure

- Status: [CONFIRMED]
- Date: 2026-03-20

## Context

The frontend includes multiple domains (auth, projects, tasks, gantt, kanban, resources, AI, notifications). File-type grouping would create cross-domain coupling and unclear ownership.

## Decision

Organize frontend by domain feature slices:
- `frontend/src/features/{feature}/...`
- each feature owns hooks, API calls, types, store, components/pages
- shared cross-feature primitives remain under `frontend/src/shared`

## Evidence

- Directory structure under `frontend/src/features/*`
- Shared layer under `frontend/src/shared/*`
- Existing design source: `docs/02-design/frontend-architecture.md`
- Git history signal: `af7679a feat(frontend): add React Router...` and later feature-by-feature commits (`gantt`, `kanban`, `ai`, etc.)

## Consequences

- Feature-level work can be implemented and tested with clearer boundaries.
- Shared layer remains constrained to truly cross-feature concerns.
