# Frontend Styling Constitution

## 0) Mission

Keep styling simple, predictable, and safe to change.
If one style change breaks unrelated pages, the system is wrong.

---

## 1) Ownership Rules (Non-Negotiable)

1. `frontend/src/index.css` owns:

- design tokens (light + dark)
- base reset
- accessibility base

2. `frontend/src/shared/ui/*` owns:

- component visuals (Button, Input, Card, Dialog, Tooltip, etc.)
- focus behavior and states for those components

3. Feature files (`frontend/src/features/**`) own:

- layout and composition only
- business-state rendering (loading/empty/error)
- no private visual system

4. `frontend/src/components.css`:

- must stay empty (or not used)
- no visual ownership here

---

## 2) Styling Hierarchy (Mini-Lego)

Always build in this order:

1. Token (global variable)
2. Shared UI primitive (`shared/ui`)
3. Feature composition (page/component layout)

Never invert this order.

---

## 3) Allowed vs Forbidden

### Allowed

- Tailwind utility classes for layout/spacing/structure
- shadcn variants (`variant="outline"`, `size="sm"`, etc.)
- token-driven colors (`bg-background`, `text-foreground`, `border-border`)
- inline `style={{...}}` only when technically required (charts/canvas position math)

### Forbidden

- ad-hoc global hooks (`data-route`, `data-app-header`, etc.) for page visuals
- one-off “magic” classes that recreate component systems
- glassmorphism/glow effects unless explicitly approved for a specific surface
- duplicated color logic in many feature files

---

## 4) Theme Rules

1. Every semantic token changed in light mode must have a dark mode pair.
2. Prefer semantic tokens (`--primary`, `--border`, `--muted-foreground`) over raw colors.
3. If a raw color is unavoidable, document why in a nearby comment.

---

## 5) How To Change Styles Safely

### Change global app color mood

Edit tokens in:

- `frontend/src/index.css` (`:root` and `.dark`)

### Change all Buttons/Inputs/Cards

Edit the corresponding file in:

- `frontend/src/shared/ui/button.tsx`
- `frontend/src/shared/ui/input.tsx`
- `frontend/src/shared/ui/card.tsx`
- etc.

### Change one feature page

Use existing shared components and layout classes.
Do not create a second visual system in that page.

---

## 6) Deviation Rule

If you intentionally break a rule for technical reasons:

1. Keep the deviation minimal.
2. Add a short comment in code near that line: `DEVIATION: reason`.
3. Log it in your active cleanup/audit markdown.

No hidden deviations.

---

## 7) Pull Request Checklist (Styling)

Before merge, confirm:

1. Only one owner changed each visual area.
2. Light + dark both checked.
3. No new global style hacks.
4. No new duplicate color systems in feature files.
5. No unexplained hardcoded colors.
6. Plan/audit document updated if decisions changed.

---

## 8) AI Assistant Contract

Any assistant working on styling must:

1. Follow this constitution first.
2. Edit one file at a time when requested.
3. Preserve layout unless explicitly told otherwise.
4. Update the plan document after each meaningful styling change.

If an assistant cannot follow this, stop and ask.

---

## 9) Golden Principle

If future-you cannot explain “where this style comes from” in 10 seconds, delete or refactor it.
