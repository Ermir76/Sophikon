# Frontend Styling Constitution

Last updated: 2026-03-09
Owner: Frontend architecture

## 0) Mission

Keep visual behavior predictable and safe to change.
One style change must not break unrelated pages.

This document is the source of truth for frontend visual governance.

## 1) Current Problem Statement

The UI layer has drift:
- too many one-off class combinations
- modified `shared/ui/*` surfaces with inconsistent behavior
- feature-level overrides recreating local design systems

Because of this, visual changes are expensive and brittle.

## 2) Recovery Strategy (Non-Negotiable)

Use a two-track model:

1. Stabilization track:
- freeze style drift
- centralize style decisions
- normalize core shells and primitives

2. Recovery track:
- migrate screen by screen
- no mixed old/new styling pattern inside one component

## 3) Ownership Rules

1. `frontend/src/index.css` owns:
- design tokens
- base reset and typography baseline
- app-level accessibility defaults

2. `frontend/src/shared/ui/*` owns:
- base widget behavior and visuals (legacy modified shadcn layer)
- no per-feature edits in normal feature work

3. `frontend/src/shared/*` primitives/adapters own:
- semantic wrappers used by features (for example: app-level card/button/input shells, layout shells)
- normalization between drifted base widgets and feature usage

4. `frontend/src/features/**` owns:
- composition and layout
- business-state rendering
- no private visual systems

5. `frontend/src/components.css`:
- no ownership for visual system decisions

## 4) Styling Hierarchy

Always in this order:
1. Token
2. Base widget (`shared/ui`)
3. Adapter/primitives (`shared/*`)
4. Feature composition (`features/**`)

Never invert this order.

## 5) Allowed vs Forbidden

Allowed:
- token-driven utilities (`bg-background`, `text-foreground`, `border-border`)
- shared variant APIs (`variant`, `size`, semantic utility classes)
- inline style only for technical layout math (canvas/chart positioning)

Forbidden:
- route-scoped global hooks for visuals (`data-route`, ad-hoc global selectors)
- arbitrary one-off visual systems in feature files
- hidden style forks of base widgets in feature folders
- hardcoded color values when a semantic token exists

## 6) Foundation Freeze Rule

`shared/ui/*` is treated as a controlled foundation:
- normal feature PRs do not modify it
- foundation edits happen only in explicit UI-foundation PRs
- every foundation edit must include a note in `docs/03-implementation/ui-ux-recovery-tracker.md`

## 7) Adapter/Primitive Rule

Feature code should consume app adapters/primitives rather than raw drifted widgets where possible.

Migration default:
- existing code can remain until touched
- touched surfaces should move toward adapters/primitives
- do not create new direct drift patterns

## 8) Theme and Token Rules

1. Semantic token first, raw color last resort.
2. Light and dark token pairs must stay complete.
3. Any unavoidable raw color requires a short nearby comment.
4. Spacing and radius must use shared scale, not random arbitrary values.

## 9) Pull Request Checklist (Styling)

Before merge:
1. Source of style decision is clear (token/widget/adapter/feature).
2. No new ad-hoc global style hooks.
3. No new private visual systems in features.
4. Light/dark checked for changed surfaces.
5. Recovery tracker updated for meaningful visual decisions.

## 10) AI Assistant Contract

When an assistant modifies styling:
1. Follow this constitution first.
2. No silent test/doc drift around visual behavior.
3. No direct `shared/ui/*` edits unless task is explicitly foundation work.
4. Explain the ownership level touched (token, base widget, adapter, feature).

## 11) Golden Rule

If you cannot answer "where this style comes from" in 10 seconds, refactor it.
