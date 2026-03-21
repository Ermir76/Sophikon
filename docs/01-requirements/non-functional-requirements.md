# Sophikon V1 - Non-Functional Requirements

**Version:** 1.0
**Date:** 2026-03-20
**Scope:** Quality attributes and operational constraints observed from the current codebase

---

## Status Legend

- `DONE`: Implemented and evidenced in current codebase.
- `PARTIAL`: Present in part, but not fully covered or enforced end-to-end.
- `PENDING`: Not evidenced in current mounted product surface.

---

## 1. Security

| ID          | Non-Functional Requirement                                                                                           | Status  |
| ----------- | -------------------------------------------------------------------------------------------------------------------- | ------- |
| NFR-SEC-001 | All protected API surfaces must require authenticated user context.                                                  | DONE    |
| NFR-SEC-002 | Access control must enforce project-level role checks for mutating actions.                                          | DONE    |
| NFR-SEC-003 | Passwords must be hashed with bcrypt and never stored in plaintext.                                                  | DONE    |
| NFR-SEC-004 | Access tokens must be short-lived JWTs; refresh tokens must support rotation and revocation.                         | DONE    |
| NFR-SEC-005 | Authentication endpoints must be rate-limited.                                                                       | DONE    |
| NFR-SEC-006 | A global API rate-limiting layer must exist.                                                                         | DONE    |
| NFR-SEC-007 | Request payloads must be validated before business logic execution.                                                  | DONE    |
| NFR-SEC-008 | Auth cookies must be HttpOnly and use `Secure` in production.                                                        | DONE    |
| NFR-SEC-009 | Task attachments must be stored outside public media paths and served only through authenticated download endpoints. | DONE    |
| NFR-SEC-010 | Attachment path resolution must prevent directory traversal.                                                         | DONE    |
| NFR-SEC-011 | Session management endpoints for viewing/revoking active sessions must exist.                                        | PENDING |
| NFR-SEC-012 | Dedicated CSRF token enforcement for cookie-authenticated mutation flows must be implemented.                        | PARTIAL |

## 2. Performance & Scalability

| ID           | Non-Functional Requirement                                                                                 | Status  |
| ------------ | ---------------------------------------------------------------------------------------------------------- | ------- |
| NFR-PERF-001 | API and service layers must be asynchronous to support concurrent I/O workloads.                           | DONE    |
| NFR-PERF-002 | Database access must use pooled async connections with connection liveness checks.                         | DONE    |
| NFR-PERF-003 | List endpoints must enforce pagination with bounded page sizes.                                            | DONE    |
| NFR-PERF-004 | Realtime project and notification updates must be supported via WebSocket channels.                        | DONE    |
| NFR-PERF-005 | Scheduling-related task and dependency changes must trigger automatic schedule recalculation when enabled. | DONE    |
| NFR-PERF-006 | Explicit latency/error SLOs (for example p95 API latency budgets) must be defined and tracked.             | PENDING |

## 3. Reliability & Availability

| ID          | Non-Functional Requirement                                                                         | Status  |
| ----------- | -------------------------------------------------------------------------------------------------- | ------- |
| NFR-REL-001 | Application startup/shutdown must initialize and stop realtime managers cleanly.                   | DONE    |
| NFR-REL-002 | Unhandled server exceptions must return a sanitized error contract without internal stack details. | DONE    |
| NFR-REL-003 | A health endpoint must be available for basic liveness checks.                                     | DONE    |
| NFR-REL-004 | Core business entities must support soft-delete where recovery is required.                        | DONE    |
| NFR-REL-005 | Backup and restore requirements must be formally defined and verified.                             | PENDING |

## 4. Data Integrity & Governance

| ID          | Non-Functional Requirement                                                                        | Status  |
| ----------- | ------------------------------------------------------------------------------------------------- | ------- |
| NFR-DAT-001 | Database-level constraints must enforce valid enum ranges and value boundaries for core entities. | DONE    |
| NFR-DAT-002 | Upload size limits must be enforced for avatars and attachments.                                  | DONE    |
| NFR-DAT-003 | Project/organization data access must be isolated by membership checks.                           | DONE    |
| NFR-DAT-004 | Formal retention/deletion policy requirements must be documented and enforced.                    | PENDING |

## 5. Observability & Auditability

| ID          | Non-Functional Requirement                                                         | Status  |
| ----------- | ---------------------------------------------------------------------------------- | ------- |
| NFR-OBS-001 | User-visible business mutations must produce activity log records.                 | DONE    |
| NFR-OBS-002 | Notification events must be generated for key collaboration and AI-agent findings. | DONE    |
| NFR-OBS-003 | System-wide operational monitoring and alerting requirements must be defined.      | PARTIAL |

---

## Document History

| Version | Date       | Author | Changes                                                                                                                                  |
| ------- | ---------- | ------ | ---------------------------------------------------------------------------------------------------------------------------------------- |
| 1.0     | 2026-03-20 | Codex  | Initial NFR document created from observed auth, rate limiting, security, performance, and reliability patterns in the current codebase. |
