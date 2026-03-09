# Collaboration Features - Implementation Plan

**Created:** 2026-03-08
**Scope:** FR-CO-001 through FR-CO-011 (Functional Requirements 3.13)
**Roadmap alignment:** V1.0 (Phases 1-3), V1.1 (Phases 4-5)

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
- [x] WebSocket infrastructure

---

## Phase 1 - Project Members (V1.0)

**FR-CO-001** (invite), **FR-CO-002** (set role), **FR-CO-003** (remove), **FR-CO-004** (view)
Effort: Small - mirrors organization_members pattern
Depends on: Nothing

### Backend

- [x] Schema `schema/project_member.py` - ProjectMemberListItem, ProjectMemberInvite, ProjectMemberRoleUpdate
- [x] Service `service/project_member_service.py` - `list_members`, `invite_member`, `change_role`, `remove_member`
- [x] Endpoint `api/v1/endpoints/project_members.py` - mounted list/invite/invitation accept/resend/revoke/role/remove routes
- [x] Mount router in `main.py`
- [x] Project creation seeds owner membership rows and owner role backfill migration exists

### Frontend

- [x] API: `project-members.service.ts`
- [x] Hook: `useProjectMembers.ts` - list query + invite/role/remove mutations
- [x] UI: members tab in project settings page
- [x] Invitation acceptance page and auth redirect plumbing

### Tests

- [x] `backend/tests/unit/api/v1/test_project_members.py`
- [x] Integration coverage: invite, role change, remove, resend, revoke, accept flow
- [x] `frontend/src/features/projects/hooks/useProjectMembers.test.tsx`
- [x] Frontend coverage for members tab, invitation accept page, project settings integration, and auth redirect links

---

## Phase 2 - Activity Log (V1.0)

**FR-CO-007** (activity log)
Effort: Medium - simple service, many integration points
Depends on: Phase 1

### Backend

- [x] Schema `schema/activity_log.py` - ActivityLogItem, actor, and change-set payloads for the project activity feed
- [x] Service `service/activity_log_service.py` - `log_activity`, `list_activity`, request context, and diff serialization helpers
- [x] Endpoint `api/v1/endpoints/activity.py` - `GET /projects/{project_id}/activity`
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

- [x] `backend/tests/unit/api/v1/test_activity.py`
- [x] Direct service coverage in `backend/tests/unit/service/test_activity_log_service.py`
- [x] Integration coverage for task/project/resource/assignment/dependency/member activity records
- [x] Frontend coverage for `useProjectActivity`, `ProjectActivityFeedCard`, and project overview activity rendering

---

## Phase 3 - Real-time Updates (V1.0)

**FR-CO-005** (real-time updates), **FR-CO-006** (presence)
Effort: Medium - new infrastructure
Depends on: Phase 1

### Backend

- [x] WebSocket endpoint `api/v1/endpoints/ws.py` - `/api/v1/ws/projects/{project_id}` with cookie/query/header token auth and explicit close codes
- [x] Connection manager `core/websocket_manager.py` - track per-project connections, subscriptions, presence, and Redis-backed fan-out
- [x] Presence tracking - connected users per project with `viewing` / `editing` state and deduped snapshots
- [x] Redis pub/sub for multi-instance broadcasting
- [x] Wire broadcast calls into project/task/resource/assignment/dependency/project-member mutations and activity logging after successful commits

### Frontend

- [x] Hook: `useProjectWebSocket.ts` - connect on project mount, send default subscriptions, and auto-reconnect with capped backoff
- [x] React Query cache invalidation on received events
- [x] Store: `features/projects/store/websocket-store.ts` - connection state, subscriptions, reconnect attempts, and presence list
- [x] Presence UI: connected user avatars and connection state in the project header
- [x] Richer protocol support is in place now, while Phase 3 intentionally renders only connected-user presence in the UI

### Tests

- [x] WebSocket connection/auth/protocol tests added in `backend/tests/unit/api/v1/test_ws.py`
- [x] Realtime service queue/channel coverage added in `backend/tests/unit/service/test_realtime_service.py`
- [x] Frontend websocket/header tests added for hook behavior, layout wiring, and header presence rendering

---

## Phase 4 - Comments and Mentions (V1.1)

**FR-CO-008** (comments on tasks), **FR-CO-009** (@mentions)
Effort: Medium
Depends on: Phase 2, Phase 3

### Backend

- [x] Schema `schema/comment.py` with `CommentCreate`, `CommentUpdate`, threaded `CommentItem`, and list payload
- [x] Service `service/comment_service.py` with entity resolution and `list/create/update/soft_delete`
- [x] Mention resolution parses ID-backed tokens `@[Name](user:uuid)`, validates membership, and stores UUID mentions
- [x] Endpoint `api/v1/endpoints/comments.py` mounted at `/api/v1/comments` for generic entity-scoped CRUD
- [x] Comment mutations wired into activity log and websocket broadcasts (`comment_created|updated|deleted`)
- [x] Mention notifications persisted as DB rows (`notification.type=mentioned`) for newly mentioned users

### Frontend

- [x] `CommentThread.tsx` in `features/tasks/components/task-detail/` with reply/edit/delete flows
- [x] `CommentInput.tsx` with mention autocomplete from project members and ID-backed token insertion
- [x] Hook `useComments.ts` with list query and create/update/delete mutations
- [x] Task detail panel includes the comment section
- [x] Task table renders `comments_count`
- [x] Project websocket hook subscribes to `comments` and invalidates comment/task queries for `comment_*` events

### Tests

- [x] Endpoint tests for CRUD, threading, mention resolution, and moderation behavior
- [x] Integration evidence that mention flows persist notification rows
- [x] Direct service coverage for mention-token parsing and deduplication
- [x] Frontend coverage for `useComments`, `CommentInput`, `CommentThread`, and websocket comment invalidation

---

## Phase 5 - Notifications and Attachments (V1.1)

**FR-CO-010** (attachments), **FR-CO-011** (notifications)
Effort: Large - two distinct features
Depends on: Phase 3, Phase 4

### Notifications - Backend

- [x] Schema `schema/notification.py` - NotificationItem, NotificationListResponse, NotificationSettings, NotificationSettingsUpdate
- [x] Service `service/notification_service.py` - `create_notification`, `list_notifications`, `mark_read`, `mark_all_read`, `get_settings`, `update_settings`
- [x] Endpoint `api/v1/endpoints/notifications.py` - list, mark-read, mark-all-read, settings read/update
- [x] Triggers: comment mentions, task assignment, deadline approaching (Celery periodic task)
- [x] Push new notifications via dedicated user WebSocket (`/api/v1/ws/notifications`)

### Notifications - Frontend

- [x] Bell icon in app header with unread count badge
- [x] Dropdown notification panel with mark-read and mark-all-read actions
- [x] Hook: `useNotifications.ts` (+ settings hooks)
- [x] Global websocket hook receives notification events and updates badge/query state

### Attachments - Backend

- [ ] Schema `schema/attachment.py` - AttachmentUpload, AttachmentResponse
- [ ] Service `service/attachment_service.py` - `upload`, `list`, `download`, `delete` (local or S3)
- [ ] Endpoint `api/v1/endpoints/attachments.py` - upload (multipart), list, download, delete

### Attachments - Frontend

- [ ] File list with upload dropzone in task detail panel
- [ ] Hook: `useAttachments.ts`

### Tests

- [x] Notification endpoint and trigger integration tests
- [ ] Attachment upload/download and storage provider tests

---

## Summary

| Phase                          | Requirements   | Effort | Depends on | Version |
| ------------------------------ | -------------- | ------ | ---------- | ------- |
| 1. Project Members             | CO-001-004     | Small  | Nothing    | V1.0    |
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
