# ADR-010: Unified Floating TaskDetailPanel Across All Views

- Status: [CONFIRMED]
- Date: 2026-03-28

## Context

The `TaskDetailPanel` component is shared across three views — Task Table, Gantt, and Kanban — but behaves inconsistently:

| View       | Open trigger                  | Panel mode   | State pattern                            |
|------------|-------------------------------|--------------|------------------------------------------|
| Task Table | Kebab menu → "View Details"   | Side sheet   | Single `selectedTaskId` (selection = open) |
| Kanban     | Click card                    | Side sheet   | Single `selectedTaskId` (selection = open) |
| Gantt      | Double-click bar/row          | **Floating** | Separate `selectedTaskId` + `detailTaskId` |

Problems:

1. **Inconsistent UX** — the panel appears differently depending on which view the user is on.
2. **Conflated state** — Task Table and Kanban use one state variable for both selection highlighting and detail opening, meaning any click immediately opens the panel.
3. **AI panel conflict** — when the AI docked panel is open on the right, a side sheet competes for the same screen edge. A floating panel lets the user position and resize it freely alongside the AI panel.

## Decision

**Unify all three views to use the Gantt page's pattern:**

1. **Floating mode everywhere** — pass `floating` to `TaskDetailPanel` on all three pages.
2. **Decouple selection from detail** — all pages adopt two separate state variables: `selectedTaskId` (highlight) and `detailTaskId` (open panel). Single click selects; double-click (or explicit action) opens details.
3. **Consistent open triggers** — double-click on a task row/card/bar opens the detail panel across all views. Kebab menu and context menu retain "View Details" as an alternative.

## Consequences

- **Pro:** Consistent interaction model across all views — users learn one pattern.
- **Pro:** Floating panel works well alongside the AI docked panel, enabling multi-panel workflows.
- **Pro:** Decoupled state allows selecting tasks (e.g. for bulk actions) without opening the detail panel.
- **Con:** Minor migration needed on Task Table and Kanban pages to split state and add double-click handlers.
- **Con:** Floating panels require the user to manually position them, which may feel less predictable than a fixed side sheet.
