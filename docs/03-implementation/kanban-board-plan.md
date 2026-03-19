# Kanban Board — Implementation Plan

## Overview
Professional Kanban board view for Sophikon projects. Same tasks as Gantt/Task list — different view. Tasks grouped into 5 fixed status columns. Drag-and-drop moves tasks between columns (changes task status). Leaf tasks only (no summary/WBS containers).

**Route:** `/projects/:projectId/kanban`
**Sidebar position:** After Gantt

---

## Columns (fixed)

| Column | Status value | Color |
|---|---|---|
| Backlog | `BACKLOG` | muted |
| To Do | `TODO` | blue |
| In Progress | `IN_PROGRESS` | yellow |
| In Review | `IN_REVIEW` | purple |
| Done | `DONE` | green |

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

## Phase 1 — Backend: Add `status` field to Task

- [ ] `backend/app/models/enums.py` — add `TaskStatus` enum (`BACKLOG`, `TODO`, `IN_PROGRESS`, `IN_REVIEW`, `DONE`)
- [ ] `backend/app/models/task.py` — add `status` column (default `BACKLOG`, indexed)
- [ ] `backend/alembic/versions/xxxx_add_task_status.py` — migration: `op.add_column` + `op.create_index`
- [ ] `backend/app/schema/task.py` — add `status` to `TaskCreate`, `TaskUpdate`, `TaskResponse`
- [ ] Run `alembic upgrade head` and verify column exists with default `BACKLOG`

---

## Phase 2 — Frontend: Feature Scaffold + Routing

- [ ] Create `frontend/src/features/kanban/types.ts` — `TaskStatus` type, `KanbanColumn` interface, `KANBAN_COLUMNS` constant
- [ ] Create `frontend/src/features/kanban/index.ts` — barrel exports
- [ ] Update `frontend/src/features/tasks/types.ts` — add `status: TaskStatus` to `Task` interface
- [ ] Add route in `frontend/src/app/App.tsx` — `/projects/:projectId/kanban` → `KanbanPage`
- [ ] Add nav item in `frontend/src/shared/layout/AppSidebar.tsx` — "Kanban" after Gantt, `LayoutKanban` icon

---

## Phase 3 — Core UI (static, no drag yet)

- [ ] `frontend/src/features/kanban/pages/KanbanPage.tsx` — fetch tasks, filter `!is_summary`, group by status, render board
- [ ] `frontend/src/features/kanban/components/KanbanBoard.tsx` — flex row layout, overflow-x-scroll, renders 5 columns
- [ ] `frontend/src/features/kanban/components/KanbanColumn.tsx` — droppable zone, column header + card list
- [ ] `frontend/src/features/kanban/components/KanbanColumnHeader.tsx` — column name, count badge, `+` add button
- [ ] `frontend/src/features/kanban/components/KanbanCard.tsx` — task card: left color border, WBS, priority badge, name, date, comments count, progress strip
- [ ] `frontend/src/features/kanban/components/KanbanToolbar.tsx` — search input + priority filter dropdown
- [ ] Verify: board loads, all tasks appear in Backlog, summary tasks not shown

---

## Phase 4 — Drag & Drop

- [ ] `frontend/src/features/kanban/hooks/useKanbanDrag.ts` — `@dnd-kit/core` sensors, `handleDragStart`, `handleDragEnd` (calls `useUpdateTask({ status: newColumn })` on column change)
- [ ] Wire `DndContext` + `DragOverlay` into `KanbanBoard.tsx`
- [ ] `KanbanColumn.tsx` — `useDroppable({ id: column.id })`, highlight on hover
- [ ] `KanbanCard.tsx` — `useDraggable({ id: task.id, data: { status } })`, opacity-40 while dragging
- [ ] Verify: drag card between columns → optimistic move → status saved to DB → rollback on error

---

## Phase 5 — Polish & Store

- [ ] `frontend/src/features/kanban/store/kanban-store.ts` — Zustand store: collapsed columns, search query, priority filter (persisted to localStorage)
- [ ] Column collapse: click toggle → column shrinks to `w-12` vertical label strip, cards hidden
- [ ] Quick-add card: click `+` in column header → inline input → Enter → `useCreateTask({ name, status, start_date: today })`
- [ ] Empty column state: centered muted "No tasks" message
- [ ] Connect search + filter from `KanbanToolbar` to card visibility

---

## Phase 6 — Docs Update

- [ ] `docs/01-requirements/functional-requirements.md` — add section 3.15 Kanban Board with FR-KB-001 through FR-KB-007
- [ ] `docs/02-design/api-specification.md` — add `status` field to TaskUpdate and TaskResponse schema tables
- [ ] `docs/02-design/frontend-architecture.md` — add `kanban/` module to directory tree
- [ ] `docs/03-implementation/project-plan.md` — add Kanban to V1.0 feature list
- [ ] `docs/ROADMAP.md` — add Kanban Board subsection to V1.0 Foundation
- [ ] `docs/03-implementation/requirements-traceability.md` — add FR-KB-001 through FR-KB-007 rows

---

## Files Changed Summary

### New files
| File | Phase |
|------|-------|
| `backend/alembic/versions/xxxx_add_task_status.py` | 1 |
| `frontend/src/features/kanban/pages/KanbanPage.tsx` | 3 |
| `frontend/src/features/kanban/components/KanbanBoard.tsx` | 3 |
| `frontend/src/features/kanban/components/KanbanColumn.tsx` | 3 |
| `frontend/src/features/kanban/components/KanbanCard.tsx` | 3 |
| `frontend/src/features/kanban/components/KanbanColumnHeader.tsx` | 3 |
| `frontend/src/features/kanban/components/KanbanToolbar.tsx` | 3 |
| `frontend/src/features/kanban/hooks/useKanbanDrag.ts` | 4 |
| `frontend/src/features/kanban/store/kanban-store.ts` | 5 |
| `frontend/src/features/kanban/types.ts` | 2 |
| `frontend/src/features/kanban/index.ts` | 2 |

### Modified files
| File | Change | Phase |
|------|--------|-------|
| `backend/app/models/enums.py` | Add `TaskStatus` enum | 1 |
| `backend/app/models/task.py` | Add `status` column | 1 |
| `backend/app/schema/task.py` | Add `status` to schemas | 1 |
| `frontend/src/features/tasks/types.ts` | Add `status` to `Task` | 2 |
| `frontend/src/app/App.tsx` | Add kanban route | 2 |
| `frontend/src/shared/layout/AppSidebar.tsx` | Add nav item | 2 |

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
