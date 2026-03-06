# UI/UX Recovery Tracker (Strict Gate Log)

Last updated: 2026-03-06
Owner: Codex + User
Source plans:

- `UI/UX Recovery Plan v2 (Strict, Clarity-First, Decision-Complete)`
- `UI Polish Plan (Core Routes, Clarity-First, Shared-Primitives-First)`

## Status Legend

- `[x]` Complete
- `[-]` Partial
- `[ ]` Not started

## Gate A: Foundation Lock

- [x] `components.css` kept empty (style ownership in `index.css` + `shared/ui/*`)
- [x] Core app background kept flat/neutral (no decorative app-wide gradients)
- [x] Dialog/Dropdown/AlertDialog moved to subtle motion style
- [x] Gantt internal scroll model preserved

## Gate B: Projects Deep Polish (Mandatory First Gate)

- [x] Compact toolbar (view toggle + compact `New Project` CTA)
- [x] Summary strip `Total / Active / At Risk / Completed`
- [x] Filter chips `All / Active / Completed / Archived / At Risk`
- [-] Sticky compact table header + compact rows (patched; verify in UI)
- [x] Decision columns visible in table (status/due/updated/actions)
- [x] Grid parity (status + due + updated)
- [x] Runtime-safe status normalization + fallback (`unknown`)

## Gate C: Shared Semantic Status Map

- [x] Single source in `features/projects/lib/project-status.ts`
- [x] Normalization for variants (`active`, `in progress`, etc.)
- [x] Safe fallback metadata to avoid runtime crash

## Gate D: Global Primitive Finishing

- [x] `Button` compact sizing + less heavy visual weight
- [x] `Card` tighter spacing/rhythm
- [x] `Table` compact hierarchy and subtle hover
- [x] `Dialog/Dropdown/AlertDialog` subtle transitions
- [x] `AlertDialogContent` destructive variant contract

## Gate E: Cross-Page Rollout

- [x] Dashboard: scan-first hierarchy, compact KPI cards, risk coloring
- [x] Project Overview: scan-first hierarchy, compact KPI/risk schedule blocks
- [x] Projects: deep polish applied
- [x] Tasks: improved (status/priority/KPI strip) + detail panel compact pass
- [x] Resources: improved (KPI strip/table density) + detail panel compact pass
- [x] Utilization: aligned with flat/subtle contract (kept existing data layout)
- [x] Gantt: toolbar/shell density aligned, timeline behavior unchanged

## Explicitly Pending (Not Done Yet)

- [x] Members page deep polish (header/table rhythm and action density)
- [x] Organization Settings deep polish
- [x] Project Settings deep polish
- [x] Task Detail panel visual hierarchy pass
- [x] Resource Detail panel visual hierarchy pass
- [ ] Full light/dark manual consistency sweep on all above pages

## Screenshot-Driven Open Issues (Current)

- [-] Project table sticky header not consistently sticky (shared table overflow patched)
- [-] Members page still visually dry vs new contract (compact pass applied; verify in UI)
- [-] Settings pages still old density/chrome (compact pass applied; verify in UI)
- [-] Side detail panel still heavy and long-scroll feeling (compact pass applied; verify in UI)

## Locked Design Decisions (Current)

- Flat neutral background for app pages (no global decorative gradient)
- Compact controls and medium data density
- Semantic colors only for meaningful status/risk signals
- Subtle motion only (no heavy glow/zoom defaults)

## Next Execution Order (Strict)

1. Verify project table sticky behavior in running app
2. Full light/dark manual consistency sweep
3. Closeout checklist and tracker finalization

## Rule for Future Updates

Every polish change must update this file:

- mark task status (`[x]`, `[-]`, `[ ]`)
- list exact file touched
- if deferred, add reason under `Explicitly Pending`

## Change Log

### 2026-03-06 — Step 1 (done)

- Target: destructive alert dialog surface (`AlertDialogContent`)
- Reason: remove glass/transparent look and reduce harsh pop feeling
- Files touched:
  - `frontend/src/shared/ui/alert-dialog.tsx`
- Result:
  - Removed destructive tinted fill (`bg-destructive/5`) so dialog body stays solid `bg-background`
  - Simplified motion to opacity-only transition (no scale pop)
  - Kept destructive border only for semantic emphasis


### 2026-03-06 - Step 2 (done)

- Target: project table sticky header reliability
- Reason: sticky headers were inconsistent because shared table container clipped vertical overflow
- Files touched:
  - `frontend/src/shared/ui/table.tsx`
- Result:
  - Changed shared table container from `overflow-x-auto` to `overflow-x-auto overflow-y-visible`
  - Prevents vertical clipping that breaks sticky table heads in long lists


### 2026-03-06 - Step 3 (done)

- Target: remove dialog/dropdown snap-pop motion
- Reason: open transitions felt abrupt in UI
- Files touched:
  - `frontend/src/shared/ui/dialog.tsx`
  - `frontend/src/shared/ui/dropdown-menu.tsx`
- Result:
  - Replaced scale+opacity transitions with opacity-only transitions
  - Increased transition duration slightly for smoother perceived open/close


### 2026-03-06 - Step 4 (done)

- Target: task/resource detail panel hierarchy and density
- Reason: side panels felt heavy, over-spaced, and long-scroll
- Files touched:
  - `frontend/src/features/tasks/components/task-detail/TaskDetailPanel.tsx`
  - `frontend/src/features/tasks/components/task-detail/TaskDetailCoreFields.tsx`
  - `frontend/src/features/resources/components/ResourceDetailPanel.tsx`
  - `frontend/src/features/resources/components/ResourceDetailsSection.tsx`
  - `frontend/src/features/resources/components/ResourceRatesSection.tsx`
  - `frontend/src/features/resources/components/ResourceStatusSection.tsx`
- Result:
  - Reduced sheet max width and spacing density
  - Made panel headers sticky with neutral surface
  - Reduced section heading weight and converted to compact utility style
  - Reduced notes/field vertical footprint to lower scroll pressure


### 2026-03-06 - Step 5 (done)

- Target: members/settings final compact polish pass
- Reason: unresolved density and hierarchy drift on admin/settings pages
- Files touched:
  - `frontend/src/features/organizations/pages/OrgMembersPage.tsx`
  - `frontend/src/features/organizations/pages/OrgSettingsPage.tsx`
  - `frontend/src/features/projects/pages/ProjectSettingsPage.tsx`
- Result:
  - Removed double-container border layer from members table composition
  - Tightened settings form/action density and reduced oversized primary action weight
  - Normalized danger-zone heading rhythm to compact utility style
