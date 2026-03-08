# Collaboration Features — Implementation Plan

**Created:** 2026-03-08
**Scope:** FR-CO-001 through FR-CO-011 (Functional Requirements 3.13)
**Roadmap alignment:** V1.0 (Phases 1–3), V1.1 (Phases 4–5)

---

## Current State

- [x] DB models defined: Comment, Attachment, Notification, ActivityLog
- [x] Enums defined: NotificationType, AuditAction, StorageProvider
- [x] User/Project model relationships wired
- [x] API spec documented for all endpoints
- [x] Organization members pattern exists as reference
- [x] ProjectMember and ProjectInvitation models in database
- [x] Phase 1 backend endpoints, services, schemas, and migration for project member management
- [x] Phase 1 frontend components, hooks, pages, and API client for project member management
- [x] Phase 1 tests for mounted backend API and frontend invite/member flows
- [ ] WebSocket infrastructure

---

## Phase 1 — Project Members (V1.0)

**FR-CO-001** (invite), **FR-CO-002** (set role), **FR-CO-003** (remove), **FR-CO-004** (view)
Effort: Small — mirrors organization_members pattern
Depends on: Nothing

### Backend

- [x] Schema `schema/project_member.py` — ProjectMemberListItem, ProjectMemberInvite, ProjectMemberRoleUpdate
- [x] Service `service/project_member_service.py` — `list_members`, `invite_member`, `change_role`, `remove_member`
- [x] Endpoint `api/v1/endpoints/project_members.py` — mounted list/invite/invitation accept/resend/revoke/role/remove routes
- [x] Mount router in `main.py`
- [x] Project creation seeds owner membership rows and owner role backfill migration exists

### Frontend

- [x] API: `project-members.service.ts`
- [x] Hook: `useProjectMembers.ts` — list query + invite/role/remove mutations
- [x] UI: members tab in project settings page
- [x] Invitation acceptance page and auth redirect plumbing

### Tests

- [x] `backend/tests/api/v1/test_project_members.py`
- [x] Integration coverage: invite, role change, remove, resend, revoke, accept flow
- [x] `frontend/src/features/projects/hooks/useProjectMembers.test.tsx`
- [x] Frontend coverage for members tab, invitation accept page, project settings integration, and auth redirect links

---

## Phase 2 — Activity Log (V1.0)

**FR-CO-007** (activity log)
Effort: Medium — simple service, many integration points
Depends on: Phase 1

### Backend

- [x] Schema `schema/activity_log.py` — ActivityLogItem, actor, and change-set payloads for the project activity feed
- [x] Service `service/activity_log_service.py` — `log_activity`, `list_activity`, request context, and diff serialization helpers
- [x] Endpoint `api/v1/endpoints/activity.py` — `GET /projects/{project_id}/activity`
- [x] Wire `log_activity` into `task_service.py` (create, update, delete)
- [x] Wire `log_activity` into `project_service.py` (create, update, delete)
- [x] Wire `log_activity` into `resource_service.py` (create, update, delete)
- [x] Wire `log_activity` into `assignment_service.py` (create, delete)
- [x] Wire `log_activity` into `dependency_service.py` (create, delete)
- [x] Wire `log_activity` into `project_member_service.py` (invite, role change, remove)

### Frontend

- [x] Hook: `useProjectActivity.ts`
- [x] Activity feed component with real API data in the project overview page
- [x] Keep dashboard `recent_activity` in the dashboard response temporarily because the main dashboard page still uses it

### Tests

- [x] `backend/tests/api/v1/test_activity.py`
- [x] Direct service coverage in `backend/tests/test_activity_log_service.py`
- [x] Integration coverage for task/project/resource/assignment/dependency/member activity records
- [x] Frontend coverage for `useProjectActivity`, `ProjectActivityFeedCard`, and project overview activity rendering

---

## Phase 3 — Real-time Updates (V1.0)

**FR-CO-005** (real-time updates), **FR-CO-006** (presence)
Effort: Medium — new infrastructure
Depends on: Phase 1

### Backend

- [ ] WebSocket endpoint `api/v1/endpoints/ws.py` — `/ws/projects/{project_id}` with JWT auth
- [ ] Connection manager `core/websocket_manager.py` — track connections per project, broadcast events
- [ ] Presence tracking — connected user IDs per project, join/leave events
- [ ] Redis pub/sub for multi-instance broadcasting
- [ ] Wire broadcast calls into task/project/resource services after DB commits

### Frontend

- [ ] Hook: `useProjectWebSocket.ts` — connect on project mount, auto-reconnect with backoff
- [ ] React Query cache invalidation on received events
- [ ] Store: `features/projects/store/websocket-store.ts` — connection state, presence list
- [ ] Presence UI: connected user avatars in project header

### Tests

- [ ] WebSocket connection and auth test
- [ ] Broadcast delivery test
- [ ] Reconnection behavior test

---

## Phase 4 — Comments and Mentions (V1.1)

**FR-CO-008** (comments on tasks), **FR-CO-009** (@mentions)
Effort: Medium
Depends on: Phase 2, Phase 3

### Backend

- [ ] Schema `schema/comment.py` — CommentCreate, CommentUpdate, CommentResponse (with author, replies)
- [ ] Service `service/comment_service.py` — `list_comments`, `create_comment`, `update_comment`, `delete_comment`
- [ ] Mention resolution — parse @-references, resolve to user UUIDs, store in mentions array
- [ ] Endpoint `api/v1/endpoints/comments.py` — CRUD scoped to entity type and ID
- [ ] Wire into activity log and WebSocket broadcast

### Frontend

- [ ] `CommentThread.tsx` in `features/tasks/components/` — threaded comment list
- [ ] `CommentInput.tsx` — text input with @mention autocomplete (query project members)
- [ ] Hook: `useComments.ts` — list query + CRUD mutations
- [ ] Add comment section to task detail panel

### Tests

- [ ] Endpoint tests: CRUD, threading, mention resolution
- [ ] Integration test: comment triggers notification for mentioned users

---

## Phase 5 — Notifications and Attachments (V1.1)

**FR-CO-010** (attachments), **FR-CO-011** (notifications)
Effort: Large — two distinct features
Depends on: Phase 3, Phase 4

### Notifications — Backend

- [ ] Schema `schema/notification.py` — NotificationItem, NotificationListResponse
- [ ] Service `service/notification_service.py` — `create_notification`, `list_notifications`, `mark_read`, `mark_all_read`
- [ ] Endpoint `api/v1/endpoints/notifications.py` — list, mark-read, mark-all-read
- [ ] Triggers: comment mentions, task assignment, deadline approaching (Celery periodic task)
- [ ] Push new notifications via WebSocket

### Notifications — Frontend

- [ ] Bell icon in app header with unread count badge
- [ ] Dropdown notification panel with mark-read actions
- [ ] Hook: `useNotifications.ts`
- [ ] WebSocket: receive notification events, update badge without polling

### Attachments — Backend

- [ ] Schema `schema/attachment.py` — AttachmentUpload, AttachmentResponse
- [ ] Service `service/attachment_service.py` — `upload`, `list`, `download`, `delete` (local or S3)
- [ ] Endpoint `api/v1/endpoints/attachments.py` — upload (multipart), list, download, delete

### Attachments — Frontend

- [ ] File list with upload dropzone in task detail panel
- [ ] Hook: `useAttachments.ts`

### Tests

- [ ] Notification endpoint and trigger integration tests
- [ ] Attachment upload/download and storage provider tests

---

## Summary

| Phase                          | Requirements   | Effort | Depends on | Version |
| ------------------------------ | -------------- | ------ | ---------- | ------- |
| 1. Project Members             | CO-001–004     | Small  | Nothing    | V1.0    |
| 2. Activity Log                | CO-007         | Medium | Phase 1    | V1.0    |
| 3. Real-time Updates           | CO-005, CO-006 | Medium | Phase 1    | V1.0    |
| 4. Comments + Mentions         | CO-008, CO-009 | Medium | Phase 2, 3 | V1.1    |
| 5. Notifications + Attachments | CO-010, CO-011 | Large  | Phase 3, 4 | V1.1    |

## Convention reminders

- Backend services: plain async functions, not classes
- Domain exceptions from `core/exceptions.py`
- All endpoints require auth via `get_project_or_404` or `get_current_active_user`
- Frontend: feature-scoped hooks and components, absolute imports, barrel exports
- Reference pattern for members: `organization_members.py` + `organization_member_service.py`
- Reference pattern for CRUD services: `task_service.py`
