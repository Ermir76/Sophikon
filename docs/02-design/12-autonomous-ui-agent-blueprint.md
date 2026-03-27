# Autonomous UI Agent Blueprint (Draft)

**Version:** 0.1 (Draft)
**Date:** 2026-03-26
**Status:** Proposed

---

## Goal

Define how Sophikon can evolve from an embedded AI assistant into a high-autonomy in-app agent for project execution, while preserving strict safety boundaries.

This draft focuses on project/workflow autonomy, not identity or security administration.

---

## Non-Negotiable Boundaries

The autonomous agent must never perform these areas without explicit future design approval:

- User management (create/update/deactivate users)
- Organization membership and role management
- Authentication and security settings
- Billing, secrets, and integration credentials

These capabilities are out of scope for autonomous execution in this design.

---

## Scope In

Allowed autonomy domain (project-scoped):

- Task planning and decomposition (single and bulk create)
- Task updates (dates, progress, priority, notes, hierarchy, ordering)
- Dependency management
- Schedule recalculation
- Resource assignment and unassignment
- Project comments and status communication
- Read-heavy analysis (insights, risks, utilization, critical path)

---

## Architecture Model

The model remains tool-driven, not pixel-driven.

- Frontend: AI panel embedded in project UI
- Backend agent loop: plan, execute, stream events, enforce policies
- Tool layer: typed action contracts for all allowed operations
- Domain services: existing service/repository/database path
- Event stream: transparent tool calls/results + approvals + completion status

No generic browser automation should be introduced for core operations.

---

## Capability & Policy Layer

Introduce a centralized policy decision point before every tool execution.

Policy checks per action:

- Action allowlist/denylist
- Role and project membership check
- Risk tier (read/write/destructive)
- Required approval mode
- Scope ownership (project-bound IDs only)

Policy outcomes:

- `allow`
- `allow_with_approval`
- `deny`

---

## Approval Strategy

- Read actions: auto
- Low-risk writes: auto if policy allows
- Medium-risk writes: plan approval required
- Destructive actions: per-action confirmation always required

Approval UX must clearly show:

- proposed action
- affected entities
- reversible vs irreversible
- reason from plan

---

## Closed-Loop Execution

Each step in execution must follow:

1. Plan step selected
2. Tool action executed
3. Post-condition verified
4. If mismatch: retry or safe stop
5. Continue or escalate

This prevents silent drift between intended and actual state.

---

## Reliability Requirements

- Idempotency keys for write operations
- Conflict handling (concurrent edits, stale entity references)
- Deterministic error classes for agent retries
- Max iteration/time budget per run
- Kill switch per project and per organization
- Full audit trail for all agent actions

---

## UI Action Contract Expansion

Current UI actions are limited. To support stronger in-app autonomy, expand typed UI action contracts for:

- route navigation including kanban-specific routes
- task focus/open in current view
- filter and board-state manipulation
- context-preserving transitions between views

All UI actions must remain explicit typed events; no free-form click automation.

---

## Observability & Governance

Minimum telemetry for production readiness:

- Action success/failure rate per tool
- Approval rate and denial rate
- Rollback or retry frequency
- Time-to-completion per autonomous run
- Escalation count to user
- Unsafe-attempt denials (policy blocks)

Governance controls:

- Runtime policy config
- Security-reviewed tool onboarding checklist
- Periodic access boundary audits

---

## Rollout Plan

### Phase A — Harden Existing Agent

- Add centralized policy engine
- Add post-condition verification for current write tools
- Improve approval payload quality

### Phase B — Expand Project Autonomy

- Add missing project-scoped tools
- Expand UI typed action contract (including kanban navigation)
- Add richer recovery flows for partial failure

### Phase C — Operational Maturity

- Add SLOs and alerts for autonomy regressions
- Add governance dashboards and review cadence
- Add staged autonomy levels per organization/project

---

## Definition of Ready for “High Autonomy”

Before enabling higher autonomy level in a project:

- policy denylist active for user/member/auth domains
- >95% success on non-destructive project writes in staging scenarios
- mandatory audit logs verified
- kill switch tested
- rollback path tested for key flows

---

## Open Questions

- Should resource assignment be medium-risk by default when over-allocation is detected?
- Should schedule recalculation require approval when critical path shifts beyond threshold?
- What is the default autonomy level for new projects?
