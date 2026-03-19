# Plan: Gantt Chart Interactive Features (FR-GC-014, FR-GC-016 – FR-GC-020)

**Date:** 2026-03-19
**Status:** Approved — ready for implementation
**Scope:** V1.0 MVP — complete the remaining Gantt interactive requirements

---

## Target Requirements

| FR | Requirement | Priority | Status |
|----|-------------|----------|--------|
| FR-GC-014 | Critical path highlight | Should | 🔶 Partial |
| FR-GC-016 | Double-click for details | Must | ❌ Not started |
| FR-GC-017 | Drag to change dates | Could | ❌ Not started |
| FR-GC-018 | Drag edges for duration | Could | ❌ Not started |
| FR-GC-019 | Drag to create dependency | Could | ❌ Not started |
| FR-GC-020 | Context menu | Should | ❌ Not started |

**No backend changes required.** All endpoints exist:
- `PATCH /projects/{id}/tasks/{id}` — `start_date`, `finish_date`, `duration`
- `POST /projects/{id}/dependencies`
- `DELETE /projects/{id}/tasks/{id}`
- `POST /projects/{id}/schedule/calculate`

---

## Architecture Context

```
GanttPage (state/data)
  └─ GanttContainer (scroll sync, resize, hook orchestration)
       └─ GanttChart (SVG renderer — bars, arrows, labels)
            └─ useGanttInteractions (click, wheel, hover)
```

SVG root has `pointerEvents: "none"`. Individual `<g>` elements opt in with `pointerEvents: "auto"`.

---

## Phase 1 — FR-GC-014: Complete Critical Path Hint

> **Problem:** `task.is_critical` is only set after `POST /schedule/calculate`. The toggle works visually but shows nothing if schedule hasn't been calculated.

- [x] **`GanttToolbar.tsx`** — add `criticalTaskCount: number` prop
- [x] **`GanttToolbar.tsx`** — when `showCriticalPath && criticalTaskCount === 0`, show amber warning icon + tooltip `"Run Schedule → Calculate to see critical path"`
- [x] **`GanttPage.tsx`** — pass `criticalTaskCount={tasks.filter(t => t.is_critical).length}` to `GanttToolbar`

✅ **Done when:** enabling critical path toggle with uncalculated schedule shows the amber hint.

---

## Phase 2 — FR-GC-016: Double-Click → Task Details

> Single-click keeps the existing `GanttBarPopover`. Double-click opens `TaskDetailPanel` (Sheet — already exists at `features/tasks/components/task-detail/`). No timer delay needed.

- [x] **`useGanttInteractions.ts`** — add `onTaskDoubleClick: (taskId: string) => void` prop
- [x] **`useGanttInteractions.ts`** — return `handleChartTaskDoubleClick` from the hook
- [x] **`GanttChart.tsx`** — add `onTaskDoubleClick` prop
- [x] **`GanttChart.tsx`** — add `onDoubleClick={() => onTaskDoubleClick(task.id)}` to each bar `<g>` (regular, summary, milestone)
- [x] **`GanttContainer.tsx`** — thread `onTaskDoubleClick` from interactions hook → `GanttChart`
- [x] **`GanttPage.tsx`** — add `detailTaskId: string | null` state
- [x] **`GanttPage.tsx`** — mount `<TaskDetailPanel isOpen={!!detailTaskId} taskId={detailTaskId} onClose={() => setDetailTaskId(null)} />`
- [x] **`GanttPage.tsx`** — pass `onTaskDoubleClick={(id) => setDetailTaskId(id)}`

✅ **Done when:** double-click opens the task sheet; single-click still opens the popover.

---

## Phase 3 — FR-GC-017 & FR-GC-018: Drag Bars + Resize Edges

> Both features share one hook with a `dragMode` discriminator. GC-017 moves the whole bar; GC-018 resizes it from left/right edges.

### 3a — Optimistic update prerequisite

- [x] **`useTasks.ts`** — add `onMutate` to `useUpdateTask`: snapshot `taskKeys.list(projectId)` cache, apply update optimistically, return rollback snapshot
- [x] **`useTasks.ts`** — add `onError`: restore rollback snapshot
- [x] **`useTasks.ts`** — add `onSettled`: `queryClient.invalidateQueries(taskKeys.list(projectId))`

### 3b — Create `useGanttBarDrag.ts`

New file: `frontend/src/features/gantt/hooks/useGanttBarDrag.ts`

```ts
interface DragState {
  taskId: string
  dragMode: "move" | "resize-left" | "resize-right"
  originalStartDate: string
  originalFinishDate: string
  originalDuration: number
  startClientX: number
  deltaDays: number
}
```

- [x] Define `DragState` interface + `dragState` state (null when idle)
- [x] `startDrag(e, task, mode)` — call `e.currentTarget.setPointerCapture(e.pointerId)`, set drag state
- [x] `pointermove` on document — compute `deltaDays = Math.round(deltaX / pxPerDay)`; only activate after `>4px` threshold
- [x] `pointerup` on document:
  - `"move"` → `useUpdateTask({ start_date, finish_date })`
  - `"resize-right"` → `useUpdateTask({ finish_date, duration })`
  - `"resize-left"` → `useUpdateTask({ start_date, duration })`, clamp `newDuration >= 1`
- [x] Attach `pointermove`/`pointerup` to document in `useEffect` when drag is active; clean up on pointerup
- [x] Return `{ dragState, startDrag }`

### 3c — Wire drag into `GanttChart.tsx`

- [x] Add `dragState`, `onBarDragStart` props (unified: mode passed as argument)
- [x] On each **regular** bar `<g>` — body: `onPointerDown → onBarDragStart(e, task, "move")`, `cursor: grab`
- [x] On each **regular** bar `<g>` — left 6px `<rect>` hit zone: `resize-left`, `cursor: w-resize`
- [x] On each **regular** bar `<g>` — right 6px `<rect>` hit zone: `resize-right`, `cursor: e-resize`
- [x] Resize `<rect>`s rendered **after** bar body in SVG order (so they win hit-test)
- [x] Ghost bar: when `dragState.taskId === task.id`, render semi-transparent `<rect>` at preview position; original bar at `opacity: 0.4`
- [x] Summary tasks and milestones: **no drag handles**

### 3d — Wire into `GanttContainer.tsx`

- [x] Add `projectId: string` to `GanttContainerProps` (also needed for GC-019/020)
- [x] Instantiate `useGanttBarDrag({ pxPerDay, projectId })`
- [x] Pass `dragState`, `onBarDragStart` to `GanttChart`
- [x] During active drag: add `cursor-grabbing` CSS class to container `div`

### 3e — `GanttPage.tsx`

- [x] Pass `projectId={projectId}` to `GanttContainer`

✅ **Done when:** dragging a bar moves its dates; dragging left/right edges changes duration. Task list updates instantly (optimistic).

---

## Phase 4 — FR-GC-020: Context Menu

> Right-click on any bar. Uses `DropdownMenu` from `@/shared/ui/dropdown-menu` (already installed), opened programmatically at pointer position.

### 4a — Create `GanttContextMenu.tsx`

New file: `frontend/src/features/gantt/components/GanttContextMenu.tsx`
Props: `task, projectId, x, y, onClose, onOpenDetails`

- [x] Render a `0×0` fixed `div` at `{left: x, top: y}` as anchor
- [x] Open `DropdownMenuContent` programmatically (controlled open)
- [x] Menu item: **Open Details** → `onOpenDetails(task.id)`
- [x] Menu item: **Add Dependency** → open `AddDependencyDialog` (already exists in tasks feature)
- [x] Menu item: **Set / Unset Milestone** → `useUpdateTask({ is_milestone: !task.is_milestone })`
- [x] Menu item: **Delete Task** → `useDeleteTask` + `AlertDialog` confirm
- [x] Separator
- [x] Menu item: **Copy WBS Code** → `navigator.clipboard.writeText(task.wbs_code)`
- [x] Call `onClose()` after any action or outside click

### 4b — Wire into `GanttChart.tsx`

- [x] Add `onTaskContextMenu: (e: React.MouseEvent, taskId: string) => void` prop
- [x] On each bar `<g>`: `onContextMenu={(e) => { e.preventDefault(); onTaskContextMenu(e, task.id) }}`

### 4c — Wire into `GanttContainer.tsx`

- [x] Add `contextMenuState: { taskId: string; x: number; y: number } | null` state
- [x] `handleTaskContextMenu(e, taskId)` — uses `e.clientX/Y` (fixed positioning, no rect math needed)
- [x] Mount `<GanttContextMenu>` when `contextMenuState` is set
- [x] Pass `onTaskDoubleClick` (= `setDetailTaskId` in GanttPage) as `onOpenDetails`

✅ **Done when:** right-click on any bar shows context menu; all 5 actions work.

---

## Phase 5 — FR-GC-019: Drag to Create Dependency

> Most complex. Connector dots appear on bar hover; dragging from dot to another bar creates a dependency.

### 5a — Create `useGanttDependencyDrag.ts`

New file: `frontend/src/features/gantt/hooks/useGanttDependencyDrag.ts`

```ts
interface DepDragState {
  sourceTaskId: string
  sourceEdge: "start" | "finish"   // finish → FS, start → SS
  fromX: number; fromY: number
  currentX: number; currentY: number
  targetTaskId: string | null
}
```

- [ ] Define `DepDragState` interface + state
- [ ] `startDrag(e, task, edge)` — set pointer capture, set state
- [ ] `pointermove` on document — update `currentX/Y`; compute `targetTaskId` via Y-hit-test: `Math.floor((currentY - timelineTop) / rowHeight)`
- [ ] `pointerup` on document — if `targetTaskId` valid and ≠ source, call `createDependency.mutateAsync({ predecessor_id: sourceTaskId, successor_id: targetTaskId, type: edge === "finish" ? "FS" : "SS" })`
- [ ] Attach/detach `pointermove`/`pointerup` on document via `useEffect` when active
- [ ] Return `{ depDragState, startConnectorDrag }`

### 5b — Wire into `GanttChart.tsx`

- [ ] Add `dependencyDragState: DepDragState | null` and `onConnectorDragStart` props
- [ ] On each regular bar + milestone when `hoveredTaskId === task.id`:
  - Left connector `<circle cx={barX - 8} cy={barMidY} r={5}>` — `edge="start"`, `cursor: crosshair`
  - Right connector `<circle cx={barX + barWidth + 8} cy={barMidY} r={5}>` — `edge="finish"`, `cursor: crosshair`
  - `onPointerDown={(e) => { e.stopPropagation(); onConnectorDragStart(e, task, edge) }}`
  - Rendered **after** resize handles in SVG order
- [ ] When `dependencyDragState` active: render dashed `<line>` (`stroke-primary`, `pointerEvents: none`) from `fromX/Y` to `currentX/Y`
- [ ] When `targetTaskId` non-null: render highlight ring on the target bar

### 5c — Wire into `GanttContainer.tsx`

- [ ] Instantiate `useGanttDependencyDrag({ pxPerDay, projectId, tasks, rowHeight, timelineTop })`
- [ ] Pass `dependencyDragState` and `onConnectorDragStart` to `GanttChart`

✅ **Done when:** hovering a bar shows connector dots; dragging from one to another creates a dependency arrow in the Gantt.

---

## Files Summary

### New files

| File | For |
|------|-----|
| `frontend/src/features/gantt/hooks/useGanttBarDrag.ts` | GC-017 + GC-018 |
| `frontend/src/features/gantt/hooks/useGanttDependencyDrag.ts` | GC-019 |
| `frontend/src/features/gantt/components/GanttContextMenu.tsx` | GC-020 |

### Modified files

| File | Changes |
|------|---------|
| `frontend/src/features/gantt/pages/GanttPage.tsx` | `detailTaskId` state, `TaskDetailPanel`, `projectId` prop, critical count |
| `frontend/src/features/gantt/components/GanttContainer.tsx` | `projectId` prop, all new hooks, context menu state |
| `frontend/src/features/gantt/components/GanttChart.tsx` | All new event props, ghost bars, connector dots, resize handles, double-click, context menu |
| `frontend/src/features/gantt/hooks/useGanttInteractions.ts` | `onTaskDoubleClick` |
| `frontend/src/features/gantt/components/GanttToolbar.tsx` | `criticalTaskCount` + amber warning |
| `frontend/src/features/tasks/hooks/useTasks.ts` | Optimistic update in `useUpdateTask` |

---

## Interaction Conflict Rules

- Connector `onPointerDown` calls `e.stopPropagation()` — prevents move-drag from firing
- Drag activates only after `>4px` threshold — no accidental drags on click
- `setPointerCapture` on all drags — handles fast mouse movement outside SVG
- Dependency preview `<line>` has `pointerEvents: none` — doesn't block target bar hover

---

## Verification Checklist

- [x] GC-014 — enable critical path with no schedule calculated → amber warning on toolbar
- [x] GC-016 — double-click bar → detail sheet opens; single-click → popover still works
- [x] GC-017 — drag bar → ghost preview follows; release → dates updated, task list reflects change
- [x] GC-018 — drag right edge → bar stretches; drag left edge → start moves; min 1 day enforced
- [x] GC-020 — right-click → menu appears; all 5 actions work; click outside → menu closes
- [ ] GC-019 — hover → connector dots appear; drag to another bar → dependency created and arrow drawn
