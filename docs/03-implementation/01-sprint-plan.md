# Sprint Plan

Purpose: define one sprint commitment with capacity, scope, and completion criteria.

---

## Current Sprint

**Sprint ID:** S01
**Dates:** 2026-03-21 -> 2026-04-04
**Goal:** Complete frontend quality audit — automated tool scan + feature-by-feature standards review — producing a prioritized issue backlog for remediation
**Owner(s):** wwwer

### Capacity

- Available focus days: `10`
- Focus factor: `0.6`
- Effective days: `10 * 0.6 = 6`
- Planned points capacity: `7`
- Buffer: `~15%` (1 pt)

### Commitment Rules

1. Do not exceed planned points capacity.
2. Do not commit blocked items.
3. Do not commit items without clear acceptance criteria.

### Committed Items

| Item ID | Title | Points | Why now | Dependencies | Done criteria |
| --- | --- | --- | --- | --- | --- |
| TECH-01 | Frontend Automated Audit | 2 | Foundation for all other audit work | - | tsc + eslint + test results captured; all surviving findings in issues/open_issues/ |
| TECH-02 | Frontend Standards Review | 5 | Identify dead code, standards violations, cross-agent inconsistencies | TECH-01 complete | All 12 features reviewed via /consistency-review; findings triaged into issues/ |

**Total committed points:** `7`

### Stretch (Optional)

| Item ID | Title | Points | Trigger to pull in |
| --- | --- | --- | --- |
| TECH-03 | Frontend Bug Remediation | TBD | Pull in only if TECH-01+02 finish early and scope is small |

### Risks and Blockers

| Risk/Blocker | Impact | Mitigation | Owner |
| --- | --- | --- | --- |
| tsc/eslint finds 50+ violations | Triage time blows out | Ruthlessly filter: dismissed_issues + roadmap items don't count | wwwer |
| Context loss mid-TECH-02 | Review quality degrades | One feature per session, findings committed to issues/ immediately | wwwer |

---

## Sprint Review (Fill at end)

- Planned points: `7`
- Completed points: `7`
- Carry-over points: `0`
- Main wins: Full frontend audit complete — tsc, eslint, tests captured; all 13 feature folders reviewed via /consistency-review; confirmed findings written to issues/open_issues/
- Main misses: -
- Process changes for next sprint: -

---

## Sprint History

| Sprint | Dates | Planned | Completed | Carry-over | Notes |
| --- | --- | --- | --- | --- | --- |
| S01 | 2026-03-21 -> 2026-04-04 | 7 | 7 | 0 | Frontend audit sprint — full tsc/eslint/test + 13-feature standards review complete |
