# Test Implementation Plan — Path to 99%

> Complete checklist of every test to write. No test gets written until this plan is reviewed and approved.
>
> **Current estimated confidence:** ~85%
> **Target:** 99%
> **Governing document:** `docs/02-design/TESTING_CONSTITUTION.md`
> **Quality audit:** `docs/04-testing/test-quality-audit.md`

---

## How This Plan Is Organized

1. **Phase 0 = fix existing bad tests FIRST** (no new tests until violations are resolved)
2. Each section = one test file to create or expand
3. Every test function is listed with its exact name and what it proves
4. Priority order: most impactful gaps first
5. Each section has a "confidence delta" — how much it moves the needle
6. Running total shows progress toward 99%

---

## PHASE 0: Fix Existing Test Quality Violations

> **Do this BEFORE writing a single new test.**
> Full details: [`test-quality-audit.md`](./test-quality-audit.md)

### Step 0.1: `test_scheduling.py` — 🔴 Rewrite (30 min)

- [ ] Use `_setup_project` helper for ALL 5 tests (currently 4 have inline setup)
- [ ] Line 79: `>= 3` → `== 3`
- [ ] Line 80: `is not None` → assert exact date `"2024-01-03"`
- [ ] Line 147: `>= 1` → `== 1`
- [ ] Line 235: `>= 2` → `== 2`
- [ ] Add comments on all `duration=480` / `duration=2100` values

### Step 0.2: `test_scheduling_flows.py` — 🔴 Tighten assertions (20 min)

- [ ] Line 118: `>= 3` → `== 3`
- [ ] Line 119: `>= 2` → `== 3` (A, B, C are all critical in single chain)
- [ ] Lines 127, 129: `>=` → exact date strings
- [ ] Line 135: `>= 2` → `== 3`
- [ ] Line 203: assert exact new start date, not just `>=`
- [ ] Line 292: `>= 0` → `> 0` (slack must be positive, not zero)

### Step 0.3: `test_insights.py` — 🔴 Rewrite (15 min)

- [ ] Line 74-77: `"key" in data` → assert actual KPI values
- [ ] Line 78: `>= 0` → `== 1` (we created exactly 1 project)
- [ ] Line 91: add error code assertion after status check

### Step 0.4: `test_utilization.py` — 🟡 Extract setup (20 min)

- [ ] Extract shared `_setup(client, suffix)` and `_setup_with_resource(client, suffix)` helpers
- [ ] Reduce each test from 30+ lines of setup to 1-2 lines
- [ ] Line 104: add `assert resp.json()["error"]["code"] == "NOT_FOUND"`

### Step 0.5: `test_tasks.py` — 🟡 Add error codes (10 min)

- [ ] Lines 335, 1225, 1376, 1652: add `resp.json()["error"]["code"]` assertion on all 400s

### Step 0.6: `test_project_members.py` — 🟡 Add error codes (5 min)

- [ ] Lines 202, 440, 485, 494, 509: add error code assertions on all 400s

### Step 0.7: Minor fixes (5 min)

- [ ] `test_auth_flows.py` L35: `>= 1` → `== 1`
- [ ] `test_ai_service.py` L175: `>= 1` → `== 1`
- [ ] `test_organizations.py` L93: `>= 6` → `== 6`

**Total Phase 0 effort: ~2 hours**

---

## FILE 1: `tests/unit/service/test_scheduling_service.py`

**Status (2026-03-11):** Baseline implemented.
**Implemented now:** topological sort ordering, FS/SS/FF/SF driver dates, forward/backward constraint helpers, empty-project scheduling, deterministic FS chain scheduling, critical-path details ordering/span.
**Implemented in this slice (exact tests):**
- [x] `test_topological_sort_orders_dependencies_and_keeps_disconnected_nodes`
- [x] `test_compute_dep_driven_date_supports_fs_ss_ff_and_sf`
- [x] `test_apply_forward_constraints_handles_mso_snet_and_fnet`
- [x] `test_apply_backward_constraints_handles_fnlt_snlt_and_mfo`
- [x] `test_calculate_schedule_empty_project_returns_start_date`
- [x] `test_calculate_schedule_sets_fs_chain_dates_and_critical_flags`
- [x] `test_get_critical_path_details_returns_ordered_chain_and_span`
- [x] `test_single_task_no_deps_starts_at_project_start`
- [x] `test_fs_chain_two_tasks`
- [x] `test_ss_dependency_same_start`
- [x] `test_ff_dependency_derives_start_from_finish`
- [x] `test_sf_dependency_reverses_logic`
- [x] `test_fs_with_positive_lag`
- [x] `test_fs_with_zero_lag`
- [x] `test_multiple_predecessors_takes_latest`
- [x] `test_disconnected_tasks_start_at_project_start`
- [x] `test_es_lands_on_non_working_day_shifts_forward`
- [x] `test_terminal_task_lf_equals_project_finish`
- [x] `test_backward_pass_propagates_lf`
- [x] `test_multiple_successors_takes_earliest`
- [x] `test_critical_task_has_zero_total_slack`
- [x] `test_non_critical_task_has_positive_total_slack`
- [x] `test_free_slack_equals_gap_to_earliest_successor`
- [x] `test_free_slack_equals_total_slack_for_terminal_tasks`
- [x] `test_asap_is_default_no_effect`
- [x] `test_alap_shifts_to_late_dates`
- [x] `test_mso_forces_exact_start_date`
- [x] `test_mfo_derives_start_from_finish_date`
- [x] `test_snet_takes_later_of_dep_and_constraint`
- [x] `test_snet_ignored_when_dep_is_later`
- [x] `test_snlt_caps_late_start`
- [x] `test_fnet_pushes_start_if_finish_too_early`
- [x] `test_fnet_no_effect_when_finish_already_late_enough`
- [x] `test_fnlt_caps_late_finish`
- [x] `test_single_chain_all_tasks_are_critical`
- [x] `test_parallel_paths_longest_is_critical`
- [x] `test_diamond_pattern_identifies_driving_path`
- [x] `test_empty_project_returns_empty_critical_path`
- [x] `test_single_task_is_critical`
- [x] `test_fs_with_negative_lag_produces_lead_time`
- [x] `test_mixed_dependency_types_on_same_successor`
- [x] `test_summary_task_excluded_from_cpm_calculation`
- [x] `test_summary_inherits_min_start_max_finish_from_children`
- [x] `test_nested_summaries_propagate_bottom_up`
- [x] `test_summary_is_critical_if_any_child_is_critical`
- [x] `test_schedule_skips_weekends`
- [x] `test_schedule_skips_holiday_exception`
- [x] `test_schedule_with_custom_work_week`

**Why:** 647-line CPM engine with zero unit tests. Most complex and business-critical code.
**Confidence delta:** +4%  |  **Running total: ~89%**

### Forward Pass (ES/EF Calculation)

```
[x] test_single_task_no_deps_starts_at_project_start
      → 1 task, 0 deps → ES = project.start_date, EF = ES + duration

[x] test_fs_chain_two_tasks
      → A(2d) --FS--> B(3d) → B.ES = A.EF + 1 day

[x] test_ss_dependency_same_start
      → A --SS--> B → B.ES = A.ES

[x] test_ff_dependency_derives_start_from_finish
      → A --FF--> B(3d) → B.EF = A.EF, B.ES = B.EF - 3d

[x] test_sf_dependency_reverses_logic
      → A --SF--> B → B.EF = A.ES

[x] test_fs_with_positive_lag
      → A --FS+2d--> B → B.ES = A.EF + 1 + 2 working days

[x] test_fs_with_zero_lag
      → A --FS+0--> B → B.ES = A.EF + 1

[x] test_fs_with_negative_lag_produces_lead_time
      → A --FS-1d--> B → B.ES shifts earlier by one working day

[x] test_multiple_predecessors_takes_latest
      → A --FS--> C, B --FS--> C → C.ES = max(A.EF, B.EF) + 1

[x] test_mixed_dependency_types_on_same_successor
      → A --FS--> C and B --SS--> C → C.ES = max(mixed dep-driven starts)

[x] test_disconnected_tasks_start_at_project_start
      → A and B with no deps → both ES = project.start_date

[x] test_es_lands_on_non_working_day_shifts_forward
      → If computed ES is Saturday → shifts to Monday
```

### Backward Pass (LS/LF Calculation)

```
[x] test_terminal_task_lf_equals_project_finish
      → Last task in chain → LF = max(all EF) = project finish

[x] test_backward_pass_propagates_lf
      → A --FS--> B → A.LF = B.LS - 1

[x] test_multiple_successors_takes_earliest
      → A --FS--> B, A --FS--> C → A.LF = min(B.LS, C.LS) - 1
```

### Slack

```
[x] test_critical_task_has_zero_total_slack
      → Single chain, no parallel path → all tasks have total_slack=0

[x] test_non_critical_task_has_positive_total_slack
      → Parallel paths: long path (critical) + short path → short path has slack > 0

[x] test_free_slack_equals_gap_to_earliest_successor
      → A --FS--> C, B --FS--> C, A shorter → A.free_slack = C.ES - A.EF - 1

[x] test_free_slack_equals_total_slack_for_terminal_tasks
      → Task with no successors → free_slack = total_slack
```

### Constraints (all 8)

```
[x] test_asap_is_default_no_effect
      → Task with ASAP constraint → same as no constraint

[x] test_alap_shifts_to_late_dates
      → Task with ALAP → ES = LS, EF = LF

[x] test_mso_forces_exact_start_date
      → MSO with date → ES = constraint_date, ignoring deps

[x] test_mfo_derives_start_from_finish_date
      → MFO with date → EF = constraint_date, ES = EF - duration

[x] test_snet_takes_later_of_dep_and_constraint
      → SNET: if dep says Jan 5, constraint says Jan 10 → ES = Jan 10

[x] test_snet_ignored_when_dep_is_later
      → SNET: if dep says Jan 15, constraint says Jan 10 → ES = Jan 15

[x] test_snlt_caps_late_start
      → SNLT: LS cannot exceed constraint_date

[x] test_fnet_pushes_start_if_finish_too_early
      → FNET: if EF < constraint → push ES forward

[x] test_fnet_no_effect_when_finish_already_late_enough
      → FNET: if EF >= constraint → no change

[x] test_fnlt_caps_late_finish
      → FNLT: LF = min(LF, constraint_date)
```

### Critical Path Identification

```
[x] test_single_chain_all_tasks_are_critical
      → A → B → C, no parallel path → all 3 critical

[x] test_parallel_paths_longest_is_critical
      → Path1: A(5d) → B(5d), Path2: C(2d) → D(2d) → Path1 is critical

[x] test_diamond_pattern_identifies_driving_path
      → A → B, A → C, B → D, C → D → longest leg is critical

[x] test_empty_project_returns_empty_critical_path
      → 0 tasks → critical_path_task_ids = []

[x] test_single_task_is_critical
      → 1 task → it is critical (total_slack = 0)
```

### Summary Task Rollup in Scheduling

```
[x] test_summary_task_excluded_from_cpm_calculation
      → Summary tasks not in topological sort, not in schedule_data

[x] test_summary_inherits_min_start_max_finish_from_children
      → Parent gets start = min(children.start), finish = max(children.finish)

[x] test_nested_summaries_propagate_bottom_up
      → Grandparent → Parent → Leaf: grandparent dates = min/max of all descendants

[x] test_summary_is_critical_if_any_child_is_critical
      → One critical child → parent.is_critical = True
```

### Calendar-Aware Scheduling

```
[x] test_schedule_skips_weekends
      → Task starting Friday with 2d duration → finishes Monday (skips Sat/Sun)

[x] test_schedule_skips_holiday_exception
      → Monday is a holiday exception → task shifts to Tuesday

[x] test_schedule_with_custom_work_week
      → 4-day work week (Mon-Thu) → Friday is non-working
```

---

## FILE 2: `tests/unit/service/test_task_rollup_service.py`

**Status (2026-03-11):** Baseline implemented.
**Implemented now:** leaf progress sync/clamp, summary min/max date aggregation, weighted progress, cost aggregation, clear-summary reset, summary edit guard.
**Implemented in this slice (exact tests):**
- [x] `test_sync_leaf_duration_progress_sets_actual_and_remaining_minutes`
- [x] `test_sync_leaf_duration_progress_clamps_percent_out_of_bounds`
- [x] `test_apply_summary_rollup_aggregates_dates_progress_costs_and_critical`
- [x] `test_clear_summary_rollup_resets_computed_fields`
- [x] `test_validate_summary_rollup_edit_blocks_computed_fields`
- [x] `test_validate_summary_rollup_edit_blocks_start_and_percent_fields`
- [x] `test_validate_summary_rollup_edit_allows_notes_edit_on_summary`
- [x] `test_apply_summary_rollup_single_child_matches_child_values`
- [x] `test_apply_summary_rollup_all_children_complete_sets_100_percent`
- [x] `test_apply_summary_rollup_zero_duration_milestones`
- [x] `test_apply_summary_rollup_parent_with_mix_of_milestones_and_tasks`

**Why:** Summary task aggregation errors cascade up the entire WBS hierarchy silently.
**Confidence delta:** +2%  |  **Running total: ~91%**

### apply_summary_rollup

```
[x] test_summary_start_is_min_of_children_starts
[x] test_summary_finish_is_max_of_children_finishes
[x] test_summary_duration_computed_in_working_minutes
[x] test_summary_progress_weighted_by_duration
      → 3 children: (50%, 480min), (100%, 960min), (0%, 480min)
      → weighted = (50*480 + 100*960 + 0*480) / (480+960+480)
[x] test_summary_cost_aggregation
      → total_cost = sum(children.total_cost) + parent.fixed_cost
[ ] test_summary_earned_value_bcws_bcwp_acwp
[x] test_summary_is_critical_if_any_child_is_critical
```

### clear_summary_rollup

```
[x] test_clear_resets_to_single_day_leaf
      → When last child removed: duration=480, start=finish, progress=0
```

### sync_leaf_duration_progress

```
[x] test_actual_duration_from_percent_and_duration
      → 50% of 960min → actual_duration=480, remaining=480
[x] test_zero_percent_means_all_remaining
[x] test_hundred_percent_means_all_actual
```

### validate_summary_rollup_edit

```
[x] test_rejects_duration_edit_on_summary_task
[x] test_rejects_start_date_edit_on_summary_task
[x] test_rejects_percent_complete_edit_on_summary_task
[x] test_allows_name_edit_on_summary_task
[x] test_allows_notes_edit_on_summary_task
```

### Edge Cases

```
[x] test_single_child_rollup
[x] test_all_children_complete_100_percent
[x] test_all_children_zero_duration_milestones
[x] test_parent_with_mix_of_milestones_and_tasks
```

---

## FILE 3: `tests/unit/service/test_auth_service.py`

**Status (2026-03-11):** Baseline implemented.
**Implemented now:** registration hash verification, duplicate email rejection, login success/wrong-password/inactive-user paths, refresh rotation behavior, logout idempotent revoke, access token claim checks.
**Implemented in this slice (exact tests):**
- [x] `test_register_user_hashes_password_and_persists_refresh_token`
- [x] `test_register_user_rejects_duplicate_email`
- [x] `test_login_user_returns_tokens_for_valid_credentials`
- [x] `test_login_user_rejects_wrong_password`
- [x] `test_login_user_rejects_inactive_user`
- [x] `test_refresh_tokens_rotates_and_revokes_old_token`
- [x] `test_logout_user_revokes_token_and_is_idempotent`
- [x] `test_register_user_rejects_password_over_72_bytes`
- [x] `test_register_user_creates_user_with_correct_fields`
- [x] `test_access_token_expires_after_configured_minutes`
- [x] `test_refresh_tokens_rejects_expired_token`
- [x] `test_refresh_tokens_rejects_malformed_token`
- [x] `test_refresh_reuse_detection_revokes_active_token_family`
- [x] `test_expired_access_token_raises_authentication_error`

**Why:** Token security is never "nice-to-have" — it's the gate to all data.
**Confidence delta:** +1.5%  |  **Running total: ~92.5%**

```
[x] test_register_hashes_password_with_bcrypt
[x] test_register_rejects_password_over_72_bytes
      → bcrypt silently truncates at 72 bytes — DoS protection
[x] test_register_rejects_duplicate_email
[x] test_register_creates_user_with_correct_fields
[x] test_login_verifies_password_and_returns_tokens
[x] test_login_rejects_wrong_password
[x] test_login_rejects_inactive_user
[x] test_access_token_contains_correct_claims
      → sub=user.id, exp=now+30min
[x] test_access_token_expires_after_configured_minutes
[x] test_refresh_token_stored_hashed_in_db
[x] test_refresh_rotation_invalidates_old_token
[x] test_refresh_reuse_detection_revokes_family
      → If old refresh token reused after rotation → revoke ALL tokens for user
[x] test_logout_revokes_refresh_token_from_db
[x] test_expired_access_token_raises_authentication_error
[x] test_expired_refresh_token_raises_authentication_error
[x] test_malformed_refresh_token_raises_authentication_error
```

---

## FILE 4: `tests/unit/service/test_calendar_service.py`

**Why:** Calendar bugs silently break scheduling — wrong dates everywhere.
**Confidence delta:** +1%  |  **Running total: ~93.5%**

```
[ ] test_create_calendar_with_default_work_week
[ ] test_create_calendar_with_custom_work_week
[ ] test_calendar_inheritance_from_base
      → Child calendar inherits base work_week, overrides specific days
[ ] test_get_effective_work_week_merges_base_and_child
[ ] test_create_exception_marks_holiday_as_non_working
[ ] test_create_exception_marks_special_day_as_working
[ ] test_exception_overlap_handling
      → Two exceptions on same date → latest one wins, or error?
[ ] test_delete_base_calendar_cascades_or_errors
[ ] test_delete_calendar_referenced_by_project_errors
[ ] test_list_exceptions_filtered_by_date_range
```

---

## FILE 5: `tests/unit/service/test_task_hierarchy_service.py`

**Why:** Indent/outdent is the core WBS interaction — bugs break the entire tree structure.
**Confidence delta:** +1%  |  **Running total: ~94.5%**

```
[ ] test_indent_moves_task_under_previous_sibling
[ ] test_indent_updates_wbs_codes
[ ] test_indent_updates_outline_level
[ ] test_indent_marks_new_parent_as_summary
[ ] test_indent_first_task_rejected
      → First task has no previous sibling → InvalidOperationError
[ ] test_indent_preserves_child_subtree
      → Task with children → entire subtree moves

[ ] test_outdent_moves_task_up_one_level
[ ] test_outdent_re_parents_subsequent_siblings_as_children
[ ] test_outdent_root_task_rejected
      → outline_level=1 → InvalidOperationError
[ ] test_outdent_updates_wbs_codes

[ ] test_reorder_within_same_parent
[ ] test_reorder_to_different_parent
[ ] test_reorder_descendant_under_self_rejected
      → Cannot move parent under its own child → InvalidOperationError
[ ] test_deep_nesting_5_levels_correct_outline_levels
```

---

## FILE 6: `tests/unit/service/test_utilization_service.py`

**Why:** Over-allocation detection drives resource management decisions.
**Confidence delta:** +0.5%  |  **Running total: ~95%**

```
[ ] test_single_assignment_under_max_not_over_allocated
[ ] test_single_assignment_over_max_is_over_allocated
[ ] test_multiple_assignments_same_day_sum_units
[ ] test_no_assignments_in_range_returns_zero_allocations
[ ] test_resource_with_zero_max_units_always_over_allocated
[ ] test_assignment_partially_overlaps_range_clamped
[ ] test_peak_units_is_maximum_across_all_days
[ ] test_average_utilization_excludes_unallocated_days
[ ] test_project_summary_aggregates_all_resources
[ ] test_detect_over_allocations_returns_only_exceeding_days
```

---

## FILE 7: `tests/unit/service/test_dependency_service.py`

**Why:** Circular dependency detection is critical — infinite loops crash the scheduler.
**Confidence delta:** +0.5%  |  **Running total: ~95.5%**

```
[ ] test_create_dependency_success_fs
[ ] test_create_dependency_success_ss_ff_sf
[ ] test_circular_direct_a_to_b_to_a_rejected
[ ] test_circular_transitive_a_to_b_to_c_to_a_rejected
[ ] test_self_reference_rejected
[ ] test_duplicate_dependency_rejected
[ ] test_cross_project_dependency_rejected
[ ] test_dependency_on_deleted_task_rejected
[ ] test_create_triggers_schedule_recalculation
[ ] test_delete_triggers_schedule_recalculation
[ ] test_update_lag_triggers_schedule_recalculation
```

---

## FILE 8: `tests/integration/flows/test_calendar_scheduling_flows.py`

**Why:** Calendar changes must trigger schedule recalculation — untested integration.
**Confidence delta:** +0.5%  |  **Running total: ~96%**

```
[ ] test_add_holiday_exception_reschedules_affected_tasks
      → Create task spanning Monday. Add holiday on Monday. Task shifts to Tuesday.

[ ] test_change_project_calendar_reschedules_all_tasks
      → Switch from 5-day to 4-day week → all durations recalculate

[ ] test_calendar_exception_on_task_finish_date_extends_task
      → Task finishes Friday. Friday becomes holiday. Finish moves to next Monday.
```

---

## FILE 9: `tests/integration/flows/test_resource_cleanup_flows.py`

**Why:** Deleting a resource must clean up assignments — data integrity.
**Confidence delta:** +0.5%  |  **Running total: ~96.5%**

```
[ ] test_delete_resource_removes_all_assignments
[ ] test_delete_resource_with_utilization_data_succeeds
[ ] test_deactivate_resource_blocks_new_assignments
      → Create inactive resource → assign → error
```

---

## FILE 10: `tests/integration/flows/test_notification_flows.py`

**Why:** Notifications are user-visible — failures are immediately noticed.
**Confidence delta:** +0.5%  |  **Running total: ~97%**

```
[ ] test_comment_mention_creates_notification_for_mentioned_user
[ ] test_task_assignment_creates_notification_for_assignee
[ ] test_notification_not_created_when_actor_is_recipient
[ ] test_mark_all_read_clears_unread_count
[ ] test_notification_settings_disable_suppresses_creation
```

---

## FILE 11: `tests/integration/flows/test_bulk_rollup_flows.py`

**Why:** Bulk task creation must cascade summary rollup correctly.
**Confidence delta:** +0.5%  |  **Running total: ~97.5%**

```
[ ] test_bulk_create_under_parent_triggers_summary_rollup
      → Bulk create 3 children → parent dates/progress updated

[ ] test_bulk_delete_last_children_clears_parent_summary
      → Delete all children → parent.is_summary = False

[ ] test_bulk_update_duration_cascades_to_ancestors
      → Update child duration → parent duration recalculates → schedule recalculates
```

---

## FILE 12: `tests/unit/api/v1/test_security.py`

**Why:** Input validation prevents embarrassing demo failures.
**Confidence delta:** +0.5%  |  **Running total: ~98%**

```
[ ] test_sql_injection_in_task_name_sanitized
      → name="'; DROP TABLE tasks;--" → stored as literal string, no error

[ ] test_xss_payload_in_comment_stored_as_text
      → content="<script>alert('xss')</script>" → stored verbatim (frontend escapes)

[ ] test_invalid_uuid_in_path_returns_422_not_500
      → GET /projects/not-a-uuid/tasks → 422 validation error

[ ] test_oversized_request_body_rejected
      → POST with 2MB JSON body → 413 or 422

[ ] test_unauthenticated_request_returns_401_not_500
      → Every protected endpoint without cookie → 401
```

---

## FILE 13: Frontend `features/gantt/hooks/useGantt.test.ts`

**Why:** Gantt is the flagship UI feature — zero tests currently.
**Confidence delta:** +0.5%  |  **Running total: ~98.5%**

```
[ ] renders_gantt_page_without_crash
[ ] fetches_tasks_and_dependencies_on_mount
[ ] timeline_zoom_switches_between_day_week_month
[ ] displays_loading_state_while_fetching
[ ] displays_error_state_on_fetch_failure
[ ] displays_empty_state_when_no_tasks
```

---

## FILE 14: Frontend `features/calendar/hooks/useCalendars.test.ts`

**Confidence delta:** +0.25%  |  **Running total: ~98.75%**

```
[ ] fetches_calendars_for_project
[ ] creates_calendar_and_invalidates_cache
[ ] deletes_calendar_and_invalidates_cache
[ ] displays_error_on_fetch_failure
```

---

## FILE 15: Frontend `features/resources/components/ResourcesPage.test.tsx`

**Confidence delta:** +0.25%  |  **Running total: ~99%**

```
[ ] renders_resource_table_with_data
[ ] renders_empty_state_when_no_resources
[ ] opens_create_resource_dialog
[ ] renders_utilization_view_tab
```

---

## Summary

| # | File | New Tests | Δ Confidence | Running Total |
|---|------|-----------|--------------|---------------|
| 1 | `test_scheduling_service.py` | 7 (implemented) | +4.0% | 89% |
| 2 | `test_task_rollup_service.py` | 5 (implemented) | +2.0% | 91% |
| 3 | `test_auth_service.py` | 7 (implemented) | +1.5% | 92.5% |
| 4 | `test_calendar_service.py` | ~10 | +1.0% | 93.5% |
| 5 | `test_task_hierarchy_service.py` | ~14 | +1.0% | 94.5% |
| 6 | `test_utilization_service.py` | ~10 | +0.5% | 95% |
| 7 | `test_dependency_service.py` | ~11 | +0.5% | 95.5% |
| 8 | `test_calendar_scheduling_flows.py` | ~3 | +0.5% | 96% |
| 9 | `test_resource_cleanup_flows.py` | ~3 | +0.5% | 96.5% |
| 10 | `test_notification_flows.py` | ~5 | +0.5% | 97% |
| 11 | `test_bulk_rollup_flows.py` | ~3 | +0.5% | 97.5% |
| 12 | `test_security.py` | ~5 | +0.5% | 98% |
| 13 | `useGantt.test.ts` | ~6 | +0.5% | 98.5% |
| 14 | `useCalendars.test.ts` | ~4 | +0.25% | 98.75% |
| 15 | `useResources.test.tsx` | ~4 | +0.25% | 99% |
| | **TOTAL** | **~147 tests** | **+14%** | **99%** |

---

## Execution Order

Fix first, then build. Each phase is self-contained.

```
Phase 0: Fix existing violations                      → ~2 hours     → Foundation solid
Week 1:  Files 1-3   (scheduling, rollup, auth)      → 85% → 92.5%
Week 2:  Files 4-7   (calendar, hierarchy, util, deps) → 92.5% → 95.5%
Week 3:  Files 8-12  (integration flows, security)    → 95.5% → 98%
Week 4:  Files 13-15 (frontend gaps)                  → 98% → 99%
```

---

*This plan covers Phase 0 (quality fixes) + 147 new test functions across 15 files. Combined with the existing 250+ tests, the total test suite will have ~400 tests — all passing the Testing Constitution.*
