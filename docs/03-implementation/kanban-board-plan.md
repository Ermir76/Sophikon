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

- [ ] `docs/01-requirements/functional-requirements.md` — add section 3.15 Kanban Board with FR-KB-001 through FR-KB-007
- [ ] `docs/02-design/api-specification.md` — add `status` field to TaskCreate, TaskUpdate, TaskResponse schema tables; note it is used by existing `PATCH /projects/:id/tasks/:taskId` (no new endpoint)
- [ ] `docs/02-design/database-schema.md` — add `status` column to `task` table: `TaskStatus` enum, NOT NULL, default `BACKLOG`, indexed
- [ ] `docs/02-design/frontend-architecture.md` — add `kanban/` module to the feature directory tree
- [ ] `docs/03-implementation/project-plan.md` — add Kanban to V1.0 feature list
- [ ] `docs/ROADMAP.md` — add Kanban Board subsection to V1.0 Foundation
- [ ] `docs/03-implementation/requirements-traceability.md` — add FR-KB-001 through FR-KB-007 rows with status `Not evidenced` (will be updated to `Implemented` as phases complete)

---

## Phase 1 — Backend: Add `status` field to Task

- [ ] `backend/app/models/enums.py` — add `TaskStatus` enum (`BACKLOG`, `TODO`, `IN_PROGRESS`, `IN_REVIEW`, `DONE`)
- [ ] `backend/app/models/task.py` — add `status` column (default `BACKLOG`, indexed)
- [ ] `backend/alembic/versions/xxxx_add_task_status.py` — migration: `op.add_column` + `op.create_index`
- [ ] `backend/app/schema/task.py` — add `status` to `TaskCreate`, `TaskUpdate`, `TaskResponse`
- [ ] Run `alembic upgrade head` and verify column exists with default `BACKLOG`

**Tests — `backend/tests/unit/api/v1/test_tasks.py`**

- [ ] `test_create_task_default_status` — POST task without `status` → response includes `"status": "BACKLOG"`
- [ ] `test_create_task_explicit_status` — POST task with `"status": "IN_PROGRESS"` → response includes `"status": "IN_PROGRESS"`
- [ ] `test_patch_task_status` — PATCH task `{"status": "DONE"}` → 200, response `status` is `"DONE"`
- [ ] `test_patch_task_invalid_status` — PATCH task `{"status": "INVALID"}` → 422
- [ ] `test_list_tasks_includes_status` — GET tasks → each item has `status` field

**Tests — `backend/tests/integration/flows/test_task_flows.py`**

- [ ] `test_status_transition_flow` — create task (BACKLOG) → patch to TODO → patch to DONE → verify each transition persists and is returned in list

---

## Phase 2 — Frontend: Feature Scaffold + Routing

- [ ] Create `frontend/src/features/kanban/types.ts` — `TaskStatus` type, `KanbanColumn` interface, `KANBAN_COLUMNS` constant
- [ ] Create `frontend/src/features/kanban/index.ts` — barrel exports
- [ ] Update `frontend/src/features/tasks/types.ts` — add `status: TaskStatus` to `Task` interface
- [ ] Add route in `frontend/src/app/App.tsx` — `/projects/:projectId/kanban` → `KanbanPage`
- [ ] Add nav item in `frontend/src/shared/layout/AppSidebar.tsx` — "Kanban" after Gantt, `Kanban` icon

_(No dedicated test file for phase 2 — routing and types are covered by phase 3 page tests)_

---

## Phase 3 — Core UI (static, no drag yet)

- [ ] `frontend/src/features/kanban/pages/KanbanPage.tsx` — fetch tasks, filter `!is_summary`, group by status, render board
- [ ] `frontend/src/features/kanban/components/KanbanBoard.tsx` — flex row layout, overflow-x-scroll, renders 5 columns
- [ ] `frontend/src/features/kanban/components/KanbanColumn.tsx` — droppable zone, column header + card list
- [ ] `frontend/src/features/kanban/components/KanbanColumnHeader.tsx` — column name, count badge, `+` add button
- [ ] `frontend/src/features/kanban/components/KanbanCard.tsx` — task card: left color border, WBS, priority badge, name, date, comments count, progress strip
- [ ] `frontend/src/features/kanban/components/KanbanToolbar.tsx` — search input + priority filter dropdown

**Tests — `frontend/src/features/kanban/pages/KanbanPage.test.tsx`**

Mock pattern: `vi.mock("@/features/tasks", ...)` with `useTasks` returning controlled data. Mock `react-router` `useParams` → `{ projectId: "proj-1" }`. Mock child components (`KanbanBoard`, `KanbanToolbar`) to keep tests focused on page logic.

- [ ] `renders loading state` — `useTasks` returns `{ isLoading: true }` → `PageLoading` shown
- [ ] `renders error state` — `useTasks` returns `{ error: new Error("fail") }` → `QueryError` shown
- [ ] `renders board when data loads` — `useTasks` returns tasks → `KanbanBoard` rendered with `tasksByStatus`
- [ ] `filters out summary tasks` — tasks with `is_summary: true` must not appear in any column's task list
- [ ] `search filters by task name` — type in search → only matching tasks passed to board
- [ ] `priority filter removes non-matching tasks` — set priority filter to "high" → only tasks with priority ≥ 750 passed to board

**Tests — `frontend/src/features/kanban/components/KanbanCard.test.tsx`**

- [ ] `renders task name and WBS code`
- [ ] `shows HIGH badge for priority ≥ 750`
- [ ] `shows MED badge for priority ≥ 500`
- [ ] `shows LOW badge for priority ≥ 250`
- [ ] `shows no badge for priority < 250`
- [ ] `shows overdue warning when finish_date is in the past and status is not DONE`
- [ ] `does not show overdue warning when status is DONE`
- [ ] `renders progress bar when percent_complete > 0`
- [ ] `does not render progress bar when percent_complete is 0`

**Tests — `frontend/src/features/kanban/components/KanbanColumn.test.tsx`**

- [ ] `shows empty state when no tasks`
- [ ] `renders correct task count in header`
- [ ] `renders a KanbanCard for each task`

---

## Phase 4 — Drag & Drop

- [ ] `frontend/src/features/kanban/hooks/useKanbanDrag.ts` — `@dnd-kit/core` sensors, `handleDragStart`, `handleDragEnd` (calls `useUpdateTask({ status: newColumn })` on column change)
- [ ] Wire `DndContext` + `DragOverlay` into `KanbanBoard.tsx`
- [ ] `KanbanColumn.tsx` — `useDroppable({ id: column.id })`, highlight on hover
- [ ] `KanbanCard.tsx` — `useDraggable({ id: task.id, data: { status } })`, opacity-40 while dragging

**Tests — `frontend/src/features/kanban/hooks/useKanbanDrag.test.ts`**

Mock `useUpdateTask` from `@/features/tasks`. Use `renderHook`.

- [ ] `handleDragEnd does nothing when dropped on the same column` — `over.id === active.data.current.status` → `updateTask` not called
- [ ] `handleDragEnd calls updateTask with new status when column changes` — `over.id !== active.data.current.status` → `updateTask.mutate` called with `{ taskId, data: { status: newColumn } }`
- [ ] `handleDragEnd does nothing when over is null` — dropped outside any column → `updateTask` not called
- [ ] `handleDragStart sets activeTaskId`
- [ ] `handleDragEnd clears activeTaskId`

---

## Phase 5 — Polish & Store

- [ ] `frontend/src/features/kanban/store/kanban-store.ts` — Zustand store: collapsed columns, search query, priority filter (persisted to localStorage)
- [ ] Column collapse: click toggle → column shrinks to `w-12` vertical label strip, cards hidden
- [ ] Quick-add card: click `+` in column header → inline input → Enter → `useCreateTask({ name, status, start_date: today })`
- [ ] Empty column state: centered muted "No tasks" message
- [ ] Connect search + filter from `KanbanToolbar` to card visibility

**Tests — `frontend/src/features/kanban/store/kanban-store.test.ts`**

- [ ] `toggleCollapse adds column to collapsedColumns`
- [ ] `toggleCollapse removes column from collapsedColumns on second call`
- [ ] `setSearch updates searchQuery`
- [ ] `setPriorityFilter updates priorityFilter`
- [ ] `initial state has no collapsed columns and empty search`

---

## Phase 6 — Traceability Sign-off

Update traceability status now that all FRs are implemented (rows were added in Phase 0 as `Not evidenced`).

- [ ] `docs/03-implementation/requirements-traceability.md` — update FR-KB-001 through FR-KB-007 from `Not evidenced` → `Implemented` with evidence anchors
- [ ] `docs/01-requirements/functional-requirements.md` — update FR-KB-001 through FR-KB-007 emoji to ✅

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
| `frontend/src/features/tasks/types.ts`      | Add `status` to `Task`  | 2     |
| `frontend/src/app/App.tsx`                  | Add kanban route        | 2     |
| `frontend/src/shared/layout/AppSidebar.tsx` | Add nav item            | 2     |

---

## Verification Checklist

- [ ] `alembic upgrade head` runs clean, `task.status` column exists
- [ ] Existing tasks return `"status": "BACKLOG"` via API
- [ ] `/projects/:id/kanban` loads without errors
- [ ] All leaf tasks appear in their correct column
- [ ] Summary tasks (`is_summary=true`) do NOT appear
- [ ] Drag card to another column → card moves instantly → DB updated
- [ ] Drag fails (API error) → card snaps back
- [ ] Search filters cards by name in real time
- [ ] Priority filter works
- [ ] Column collapse hides cards, shrinks column
- [ ] `+` button creates a task in that column's status
