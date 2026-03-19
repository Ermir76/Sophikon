# Kanban Board — Implementation Plan

## Overview

Professional Kanban board view for Sophikon projects. Same tasks as Gantt/Task list — different view. Tasks grouped into 5 fixed status columns. Drag-and-drop moves tasks between columns (changes task status). Leaf tasks only (no summary/WBS containers).

**Route:** `/projects/:projectId/kanban`
**Sidebar position:** After Gantt

---

## Columns (fixed)

| Column      | Status value  | Color  |
| ----------- | ------------- | ------ |
| Backlog     | `BACKLOG`     | muted  |
| To Do       | `TODO`        | blue   |
| In Progress | `IN_PROGRESS` | yellow |
| In Review   | `IN_REVIEW`   | purple |
| Done        | `DONE`        | green  |

---

## Card Design

```
┌─────────────────────────────────────┐
│▌  WBS-01  ·  ● HIGH                 │  ← colored left border + WBS + priority
│   Build Authentication System       │  ← task name (bold, 2-line clamp)
│                                     │
│   📅 Mar 15  ⚠️  💬 3              │  ← deadline (red if overdue) + comment count
├─────────────────────────────────────┤
│  ████████████░░░░░  65%             │  ← progress strip
└─────────────────────────────────────┘
```

**Priority** from `task.priority` (0–1000):

- ≥ 750 → HIGH (orange)
- ≥ 500 → MEDIUM (yellow)
- ≥ 250 → LOW (gray)
- < 250 → MINIMAL (muted)

---

## Phase 0 — Specs & Design Docs (before any code)

Update the source-of-truth docs first. Implementation follows these contracts, not the other way around.

- [x] `docs/01-requirements/functional-requirements.md` — add section 3.15 Kanban Board with FR-KB-001 through FR-KB-007
- [x] `docs/02-design/api-specification.md` — add `status` field to TaskCreate, TaskUpdate, TaskResponse schema tables; note it is used by existing `PATCH /projects/:id/tasks/:taskId` (no new endpoint)
- [x] `docs/02-design/database-schema.md` — add `status` column to `task` table: `TaskStatus` enum, NOT NULL, default `BACKLOG`, indexed
- [x] `docs/02-design/frontend-architecture.md` — add `kanban/` module to the feature directory tree
- [x] `docs/03-implementation/project-plan.md` — add Kanban to V1.0 feature list
- [x] `docs/ROADMAP.md` — add Kanban Board subsection to V1.0 Foundation
- [x] `docs/03-implementation/requirements-traceability.md` — add FR-KB-001 through FR-KB-007 rows with status `Not evidenced` (will be updated to `Implemented` as phases complete)

---

## Phase 1 — Backend: Add `status` field to Task

- [x] `backend/app/models/enums.py` — add `TaskStatus` enum (`BACKLOG`, `TODO`, `IN_PROGRESS`, `IN_REVIEW`, `DONE`)
- [x] `backend/app/models/task.py` — add `status` column (default `BACKLOG`, indexed)
- [x] `backend/alembic/versions/xxxx_add_task_status.py` — migration: `op.add_column` + `op.create_index`
- [x] `backend/app/schema/task.py` — add `status` to `TaskCreate`, `TaskUpdate`, `TaskResponse`
- [x] Run `alembic upgrade head` and verify column exists with default `BACKLOG`

**Tests — `backend/tests/unit/api/v1/test_tasks.py`**

- [x] `test_create_task_default_status` — POST task without `status` → response includes `"status": "BACKLOG"`
- [x] `test_create_task_explicit_status` — POST task with `"status": "IN_PROGRESS"` → response includes `"status": "IN_PROGRESS"`
- [x] `test_patch_task_status` — PATCH task `{"status": "DONE"}` → 200, response `status` is `"DONE"`
- [x] `test_patch_task_invalid_status` — PATCH task `{"status": "INVALID"}` → 422
- [x] `test_list_tasks_includes_status` — GET tasks → each item has `status` field

**Tests — `backend/tests/integration/flows/test_task_flows.py`**

- [x] `test_status_transition_flow` — create task (BACKLOG) → patch to TODO → patch to DONE → verify each transition persists and is returned in list

---

## Phase 2 — Frontend: Feature Scaffold + Routing

- [x] Create `frontend/src/features/kanban/types.ts` — `TaskStatus` type, `KanbanColumn` interface, `KANBAN_COLUMNS` constant
- [x] Create `frontend/src/features/kanban/index.ts` — barrel exports
- [x] Update `frontend/src/features/tasks/types.ts` — add `status: TaskStatus` to `Task` interface
- [x] Add route in `frontend/src/app/App.tsx` — `/projects/:projectId/kanban` → `KanbanPage`
- [x] Add nav item in `frontend/src/shared/layout/AppSidebar.tsx` — "Kanban" after Gantt, `Kanban` icon

_(No dedicated test file for phase 2 — routing and types are covered by phase 3 page tests)_

---

## Phase 3 — Core UI (static, no drag yet)

- [x] `frontend/src/features/kanban/pages/KanbanPage.tsx` — fetch tasks, filter `!is_summary`, group by status, render board
- [x] `frontend/src/features/kanban/components/KanbanBoard.tsx` — flex row layout, overflow-x-scroll, renders 5 columns
- [x] `frontend/src/features/kanban/components/KanbanColumn.tsx` — droppable zone, column header + card list
- [x] `frontend/src/features/kanban/components/KanbanColumnHeader.tsx` — column name, count badge, `+` add button
- [x] `frontend/src/features/kanban/components/KanbanCard.tsx` — task card: left color border, WBS, priority badge, name, date, comments count, progress strip
- [x] `frontend/src/features/kanban/components/KanbanToolbar.tsx` — search input + priority filter dropdown

**Tests — `frontend/src/features/kanban/pages/KanbanPage.test.tsx`**

Mock pattern: `vi.mock("@/features/tasks", ...)` with `useTasks` returning controlled data. Mock `react-router` `useParams` → `{ projectId: "proj-1" }`. Mock child components (`KanbanBoard`, `KanbanToolbar`) to keep tests focused on page logic.

- [x] `renders loading state` — `useTasks` returns `{ isLoading: true }` → `PageLoading` shown
- [x] `renders error state` — `useTasks` returns `{ error: new Error("fail") }` → `QueryError` shown
- [x] `renders board when data loads` — `useTasks` returns tasks → `KanbanBoard` rendered with `tasksByStatus`
- [x] `filters out summary tasks` — tasks with `is_summary: true` must not appear in any column's task list
- [x] `search filters by task name` — type in search → only matching tasks passed to board
- [x] `priority filter removes non-matching tasks` — set priority filter to "high" → only tasks with priority ≥ 750 passed to board

**Tests — `frontend/src/features/kanban/components/KanbanCard.test.tsx`**

- [x] `renders task name and WBS code`
- [x] `shows HIGH badge for priority ≥ 750`
- [x] `shows MED badge for priority ≥ 500`
- [x] `shows LOW badge for priority ≥ 250`
- [x] `shows no badge for priority < 250`
- [x] `shows overdue warning when finish_date is in the past and status is not DONE`
- [x] `does not show overdue warning when status is DONE`
- [x] `renders progress bar when percent_complete > 0`
- [x] `does not render progress bar when percent_complete is 0`

**Tests — `frontend/src/features/kanban/components/KanbanColumn.test.tsx`**

- [x] `shows empty state when no tasks`
- [x] `renders correct task count in header`
- [x] `renders a KanbanCard for each task`

---

## Phase 4 — Drag & Drop

- [x] `frontend/src/features/kanban/hooks/useKanbanDrag.ts` — `@dnd-kit/core` sensors, `handleDragStart`, `handleDragEnd` (calls `useUpdateTask({ status: newColumn })` on column change)
- [x] Wire `DndContext` + `DragOverlay` into `KanbanBoard.tsx`
- [x] `KanbanColumn.tsx` — `useDroppable({ id: column.id })`, highlight on hover
- [x] `KanbanCard.tsx` — `useDraggable({ id: task.id, data: { status } })`, opacity-40 while dragging

**Tests — `frontend/src/features/kanban/hooks/useKanbanDrag.test.ts`**

Mock `useUpdateTask` from `@/features/tasks`. Use `renderHook`.

- [x] `handleDragEnd does nothing when dropped on the same column` — `over.id === active.data.current.status` → `updateTask` not called
- [x] `handleDragEnd calls updateTask with new status when column changes` — `over.id !== active.data.current.status` → `updateTask.mutate` called with `{ taskId, data: { status: newColumn } }`
- [x] `handleDragEnd does nothing when over is null` — dropped outside any column → `updateTask` not called
- [x] `handleDragStart sets activeTaskId`
- [x] `handleDragEnd clears activeTaskId`

---

## Phase 5 — Polish & Store

- [x] `frontend/src/features/kanban/store/kanban-store.ts` — Zustand store: collapsed columns, search query, priority filter (persisted to localStorage)
- [x] Column collapse: click toggle → column shrinks to `w-12` vertical label strip, cards hidden
- [x] Quick-add card: click `+` in column header → inline input → Enter → `useCreateTask({ name, status, start_date: today })`
- [x] Empty column state: centered muted "No tasks" message
- [x] Connect search + filter from `KanbanToolbar` to card visibility

**Tests — `frontend/src/features/kanban/store/kanban-store.test.ts`**

- [x] `toggleCollapse adds column to collapsedColumns`
- [x] `toggleCollapse removes column from collapsedColumns on second call`
- [x] `setSearch updates searchQuery`
- [x] `setPriorityFilter updates priorityFilter`
- [x] `initial state has no collapsed columns and empty search`

---

## Phase 6 — Traceability Sign-off

Update traceability status now that all FRs are implemented (rows were added in Phase 0 as `Not evidenced`).

- [x] `docs/03-implementation/requirements-traceability.md` — update FR-KB-001 through FR-KB-007 from `Not evidenced` → `Implemented` with evidence anchors
- [x] `docs/01-requirements/functional-requirements.md` — update FR-KB-001 through FR-KB-007 emoji to ✅

---

## Files Changed Summary

### New files

| File                                                               | Phase |
| ------------------------------------------------------------------ | ----- |
| `backend/alembic/versions/xxxx_add_task_status.py`                 | 1     |
| `docs/01-requirements/functional-requirements.md` (§3.15 added)    | 0     |
| `docs/02-design/api-specification.md` (status field added)         | 0     |
| `docs/02-design/database-schema.md` (status column added)          | 0     |
| `docs/02-design/frontend-architecture.md` (kanban/ added)          | 0     |
| `docs/03-implementation/project-plan.md` (kanban added)            | 0     |
| `docs/ROADMAP.md` (kanban section added)                           | 0     |
| `docs/03-implementation/requirements-traceability.md` (FR-KB rows) | 0, 6  |
| `frontend/src/features/kanban/pages/KanbanPage.tsx`                | 3     |
| `frontend/src/features/kanban/components/KanbanBoard.tsx`          | 3     |
| `frontend/src/features/kanban/components/KanbanColumn.tsx`         | 3     |
| `frontend/src/features/kanban/components/KanbanCard.tsx`           | 3     |
| `frontend/src/features/kanban/components/KanbanColumnHeader.tsx`   | 3     |
| `frontend/src/features/kanban/components/KanbanToolbar.tsx`        | 3     |
| `frontend/src/features/kanban/hooks/useKanbanDrag.ts`              | 4     |
| `frontend/src/features/kanban/store/kanban-store.ts`               | 5     |
| `frontend/src/features/kanban/types.ts`                            | 2     |
| `frontend/src/features/kanban/index.ts`                            | 2     |
| `backend/tests/unit/api/v1/test_tasks.py` (additions)              | 1     |
| `backend/tests/integration/flows/test_task_flows.py` (additions)   | 1     |
| `frontend/src/features/kanban/pages/KanbanPage.test.tsx`           | 3     |
| `frontend/src/features/kanban/components/KanbanCard.test.tsx`      | 3     |
| `frontend/src/features/kanban/components/KanbanColumn.test.tsx`    | 3     |
| `frontend/src/features/kanban/hooks/useKanbanDrag.test.ts`         | 4     |
| `frontend/src/features/kanban/store/kanban-store.test.ts`          | 5     |

### Modified files

| File                                        | Change                  | Phase |
| ------------------------------------------- | ----------------------- | ----- |
| `backend/app/models/enums.py`               | Add `TaskStatus` enum   | 1     |
| `backend/app/models/task.py`                | Add `status` column     | 1     |
| `backend/app/schema/task.py`                | Add `status` to schemas | 1     |
| `backend/app/service/task_service.py`       | Pass `status` on create | 1     |
| `frontend/src/features/tasks/types.ts`      | Add `status` to `Task`  | 2     |
| `frontend/src/app/App.tsx`                  | Add kanban route        | 2     |
| `frontend/src/shared/layout/AppSidebar.tsx` | Add nav item            | 2     |

---

## Verification Checklist

- [x] `alembic upgrade head` runs clean, `task.status` column exists
- [x] Existing tasks return `"status": "BACKLOG"` via API
- [x] `/projects/:id/kanban` loads without errors
- [x] All leaf tasks appear in their correct column
- [x] Summary tasks (`is_summary=true`) do NOT appear
- [x] Drag card to another column → card moves instantly → DB updated
- [x] Drag fails (API error) → card snaps back
- [x] Search filters cards by name in real time
- [x] Priority filter works
- [x] Column collapse hides cards, shrinks column
- [x] `+` button creates a task in that column's status
