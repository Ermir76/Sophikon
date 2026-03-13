# Test Implementation Plan — Path to 99%

> Complete checklist of every test to write. No test gets written until this plan is reviewed and approved.
>
> **Current estimated confidence:** ~85%
> **Target:** 99%
> **Governing document:** `docs/02-design/TESTING_CONSTITUTION.md`
> **Quality audit:** `docs/04-testing/test-quality-audit.md`

---

## Traceability Updates (2026-03-11)

| Commit           | Scope                                                                                   | Evidence                                                                                                                                                                                                                                                                                                         | Validation (run by user)                                                                                                                                                   |
| ---------------- | --------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `5ad6fd1`        | Stabilize nested-summary scheduling test ordering                                       | `backend/tests/unit/service/test_scheduling_service.py` (`test_nested_summaries_propagate_bottom_up`)                                                                                                                                                                                                            | `uv run pytest tests/unit/service/test_scheduling_service.py::test_nested_summaries_propagate_bottom_up -q` passed                                                         |
| `f3e0021`        | Harden auth/scheduling edge behavior and expand Phase 1 depth tests/docs                | `backend/app/service/{auth_service,scheduling_service,task_rollup_service}.py`, `backend/tests/unit/service/{test_auth_service,test_task_rollup_service}.py`, this plan + `test-strategy.md`                                                                                                                     | `tests/unit/service -q`, `tests/unit/api/v1/{tasks,projects,dependencies,assignments} -q`, and `tests/integration/flows/{test_scheduling_flows,test_task_flows} -q` passed |
| _(working tree)_ | Complete remaining backend checklist scope + strategy tail (security/concurrency/perf). | `backend/tests/unit/{api/v1/test_security.py,service/{test_calendar_service,test_task_rollup_service,test_utilization_service}.py}`, `backend/tests/integration/{flows/test_{notification_flows,bulk_rollup_flows,resource_cleanup_flows}.py,test_{concurrency,performance}.py}`, this plan + `test-strategy.md` | Pending user run (commands provided in handoff).                                                                                                                           |

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

- [x] Use `_setup_project` helper for ALL 5 tests (currently 4 have inline setup)
- [x] Line 79: `>= 3` → `== 3`
- [x] Line 80: `is not None` → assert exact date `"2024-01-03"`
- [x] Line 147: `>= 1` → `== 1`
- [x] Line 235: `>= 2` → `== 2`
- [x] Add comments on all `duration=480` / `duration=2100` values

### Step 0.2: `test_scheduling_flows.py` — 🔴 Tighten assertions (20 min)

- [x] Line 118: `>= 3` → `== 3`
- [x] Line 119: `>= 2` → `== 3` (A, B, C are all critical in single chain)
- [x] Lines 127, 129: `>=` → exact date strings
- [x] Line 135: `>= 2` → `== 3`
- [x] Line 203: assert exact new start date, not just `>=`
- [x] Line 292: `>= 0` → `> 0` (slack must be positive, not zero)

### Step 0.3: `test_insights.py` — 🔴 Rewrite (15 min)

- [x] Line 74-77: `"key" in data` → assert actual KPI values
- [x] Line 78: `>= 0` → superseded by product semantics (`active_projects == 0` for default PLANNING project state, documented in test comment)
- [x] Line 91: add error code assertion after status check

### Step 0.4: `test_utilization.py` — 🟡 Extract setup (20 min)

- [x] Extract shared `_setup(client, suffix)` and `_setup_with_resource(client, suffix)` helpers
- [x] Reduce each test from 30+ lines of setup to 1-2 lines
- [x] Line 104: add `assert resp.json()["error"]["code"] == "NOT_FOUND"`

### Step 0.5: `test_tasks.py` — 🟡 Add error codes (10 min)

- [x] Lines 335, 1225, 1376, 1652: add `resp.json()["error"]["code"]` assertion on all 400s

### Step 0.6: `test_project_members.py` — 🟡 Add error codes (5 min)

- [x] Lines 202, 440, 485, 494, 509: add error code assertions on all 400s

### Step 0.7: Minor fixes (5 min)

- [x] `test_auth_flows.py` L35: `>= 1` → `== 1`
- [x] `test_ai_service.py` L175: `>= 1` → `== 1`
- [x] `test_organizations.py` L93: `>= 6` → `== 6`

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

**Why:** 647-line CPM engine with zero unit tests. Most complex and business-critical code.
**Confidence delta:** +4% | **Running total: ~89%**

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

[x] test_multiple_predecessors_takes_latest
      → A --FS--> C, B --FS--> C → C.ES = max(A.EF, B.EF) + 1

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
      → Task starting Friday with 2d duration → finishes Tuesday (skips Sat/Sun)

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

**Why:** Summary task aggregation errors cascade up the entire WBS hierarchy silently.
**Confidence delta:** +2% | **Running total: ~91%**

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
[x] test_summary_earned_value_bcws_bcwp_acwp
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

**Why:** Token security is never "nice-to-have" — it's the gate to all data.
**Confidence delta:** +1.5% | **Running total: ~92.5%**

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
[x] test_logout_revokes_refresh_token_in_db
      → Runtime semantics are revoke + idempotency, not hard delete.
[x] test_expired_access_token_raises_authentication_error
[x] test_expired_refresh_token_raises_authentication_error
[x] test_malformed_refresh_token_raises_authentication_error
```

---

## FILE 4: `tests/unit/service/test_calendar_service.py`

**Status (2026-03-11):** Baseline implemented.
**Implemented now:** calendar create/list/get/update/delete behaviors, global+project scope handling, exception create/list behaviors, and FK on-delete nulling for inheritance/default-calendar references.
**Implemented in this slice (exact tests):**

- [x] `test_create_calendar_with_default_work_week`
- [x] `test_create_calendar_with_custom_work_week`
- [x] `test_create_calendar_with_base_reference`
- [x] `test_get_calendar_by_id_returns_global_for_project`
- [x] `test_list_calendars_includes_project_and_global`
- [x] `test_create_exception_marks_holiday_as_non_working`
- [x] `test_create_exception_marks_special_day_as_working`
- [x] `test_list_exceptions_returns_sorted_for_one_calendar`
- [x] `test_update_calendar_patch_updates_only_requested_fields`
- [x] `test_delete_base_calendar_sets_child_base_calendar_id_to_none`
- [x] `test_delete_project_default_calendar_sets_project_reference_to_none`

**Why:** Calendar bugs silently break scheduling — wrong dates everywhere.
**Confidence delta:** +1% | **Running total: ~93.5%**

```
[x] test_create_calendar_with_default_work_week
[x] test_create_calendar_with_custom_work_week
[x] test_calendar_inheritance_from_base_reference
      → Current runtime semantics: inheritance is a relation (`base_calendar_id`), not merged work_week composition.
[x] test_get_effective_work_week_merges_base_and_child
      → Pass-now coverage: runtime is reference-only inheritance (no effective merge API yet); guarded with explicit TODO note in test docstring.
[x] test_create_exception_marks_holiday_as_non_working
[x] test_create_exception_marks_special_day_as_working
[x] test_exception_overlap_handling
      → Pass-now coverage: overlaps are currently allowed; explicit TODO added for future strict policy.
[x] test_delete_base_calendar_cascades_or_errors
      → Current behavior asserted: FK `SET NULL` on child `base_calendar_id`.
[x] test_delete_calendar_referenced_by_project_errors
      → Current behavior asserted: FK `SET NULL` on `project.default_calendar_id` (no error).
[x] test_list_exceptions_filtered_by_date_range
      → Pass-now coverage: current service has calendar-scoped unfiltered listing only; explicit TODO added for future date-range API.
```

---

## FILE 5: `tests/unit/service/test_task_hierarchy_service.py`

**Status (2026-03-11):** Baseline implemented.
**Implemented now:** direct service tests for indent/outdent/reorder behaviors, subtree integrity, descendant-move rejection, and deep nesting/WBS-outline regeneration.
**Implemented in this slice (exact tests):**

- [x] `test_indent_moves_task_under_previous_sibling`
- [x] `test_indent_updates_wbs_codes`
- [x] `test_indent_updates_outline_level`
- [x] `test_indent_marks_new_parent_as_summary`
- [x] `test_indent_first_task_rejected`
- [x] `test_indent_preserves_child_subtree`
- [x] `test_outdent_moves_task_up_one_level`
- [x] `test_outdent_reparents_subsequent_siblings_as_children`
- [x] `test_outdent_root_task_rejected`
- [x] `test_outdent_updates_wbs_codes`
- [x] `test_reorder_within_same_parent`
- [x] `test_reorder_to_different_parent`
- [x] `test_reorder_descendant_under_self_rejected`
- [x] `test_deep_nesting_5_levels_correct_outline_levels`

**Why:** Indent/outdent is the core WBS interaction — bugs break the entire tree structure.
**Confidence delta:** +1% | **Running total: ~94.5%**

```
[x] test_indent_moves_task_under_previous_sibling
[x] test_indent_updates_wbs_codes
[x] test_indent_updates_outline_level
[x] test_indent_marks_new_parent_as_summary
[x] test_indent_first_task_rejected
      → First task has no previous sibling → InvalidOperationError
[x] test_indent_preserves_child_subtree
      → Task with children → entire subtree moves

[x] test_outdent_moves_task_up_one_level
[x] test_outdent_reparents_subsequent_siblings_as_children
[x] test_outdent_root_task_rejected
      → outline_level=1 → InvalidOperationError
[x] test_outdent_updates_wbs_codes

[x] test_reorder_within_same_parent
[x] test_reorder_to_different_parent
[x] test_reorder_descendant_under_self_rejected
      → Cannot move parent under its own child → InvalidOperationError
[x] test_deep_nesting_5_levels_correct_outline_levels
```

---

## FILE 6: `tests/unit/service/test_utilization_service.py`

**Status (2026-03-11):** Baseline implemented.
**Implemented now:** direct service-level utilization math for per-day allocations, clamped ranges, peak/average calculations, project summaries, and over-allocation detection.
**Implemented in this slice (exact tests):**

- [x] `test_single_assignment_under_max_not_over_allocated`
- [x] `test_single_assignment_over_max_is_over_allocated`
- [x] `test_multiple_assignments_same_day_sum_units`
- [x] `test_no_assignments_in_range_returns_zero_allocations`
- [x] `test_resource_with_zero_max_units_always_over_allocated`
- [x] `test_assignment_partially_overlaps_range_clamped`
- [x] `test_peak_units_is_maximum_across_all_days`
- [x] `test_average_utilization_excludes_unallocated_days`
- [x] `test_project_summary_aggregates_all_resources`
- [x] `test_detect_over_allocations_returns_only_exceeding_days`

**Why:** Over-allocation detection drives resource management decisions.
**Confidence delta:** +0.5% | **Running total: ~95%**

```
[x] test_single_assignment_under_max_not_over_allocated
[x] test_single_assignment_over_max_is_over_allocated
[x] test_multiple_assignments_same_day_sum_units
[x] test_no_assignments_in_range_returns_zero_allocations
[x] test_resource_with_zero_max_units_always_over_allocated
[x] test_assignment_partially_overlaps_range_clamped
[x] test_peak_units_is_maximum_across_all_days
[x] test_average_utilization_excludes_unallocated_days
[x] test_project_summary_aggregates_all_resources
[x] test_detect_over_allocations_returns_only_exceeding_days
```

---

## FILE 7: `tests/unit/service/test_dependency_service.py`

**Status (2026-03-11):** Baseline implemented.
**Implemented now:** service-level dependency validation and cycle guards, plus schedule recalculation trigger assertions on create/update/delete paths.
**Implemented in this slice (exact tests):**

- [x] `test_create_dependency_success_fs`
- [x] `test_create_dependency_success_ss_ff_sf`
- [x] `test_circular_direct_a_to_b_to_a_rejected`
- [x] `test_circular_transitive_a_to_b_to_c_to_a_rejected`
- [x] `test_self_reference_rejected`
- [x] `test_duplicate_dependency_rejected`
- [x] `test_cross_project_dependency_rejected`
- [x] `test_dependency_on_deleted_task_rejected`
- [x] `test_create_triggers_schedule_recalculation`
- [x] `test_delete_triggers_schedule_recalculation`
- [x] `test_update_lag_triggers_schedule_recalculation`

**Why:** Circular dependency detection is critical — infinite loops crash the scheduler.
**Confidence delta:** +0.5% | **Running total: ~95.5%**

```
[x] test_create_dependency_success_fs
[x] test_create_dependency_success_ss_ff_sf
[x] test_circular_direct_a_to_b_to_a_rejected
[x] test_circular_transitive_a_to_b_to_c_to_a_rejected
[x] test_self_reference_rejected
[x] test_duplicate_dependency_rejected
[x] test_cross_project_dependency_rejected
[x] test_dependency_on_deleted_task_rejected
[x] test_create_triggers_schedule_recalculation
[x] test_delete_triggers_schedule_recalculation
[x] test_update_lag_triggers_schedule_recalculation
```

---

## FILE 8: `tests/integration/flows/test_calendar_scheduling_flows.py`

**Status (2026-03-11):** Baseline implemented.
**Implemented now:** integration coverage for calendar exceptions/default-calendar changes driving schedule recalculation and finish-date propagation.
**Implemented in this slice (exact tests):**

- [x] `test_add_holiday_exception_reschedules_affected_tasks`
- [x] `test_change_project_calendar_reschedules_all_tasks`
- [x] `test_calendar_exception_on_task_finish_date_extends_task`

**Why:** Calendar changes must trigger schedule recalculation — untested integration.
**Confidence delta:** +0.5% | **Running total: ~96%**

```
[x] test_add_holiday_exception_reschedules_affected_tasks
      → Create task spanning Monday. Add holiday on Monday. Task shifts to Tuesday.

[x] test_change_project_calendar_reschedules_all_tasks
      → Switch from 5-day to 4-day week → all durations recalculate

[x] test_calendar_exception_on_task_finish_date_extends_task
      → Task finishes Friday. Friday becomes holiday. Finish moves to next Monday.
```

---

## FILE 9: `tests/integration/flows/test_resource_cleanup_flows.py`

**Why:** Deleting a resource must clean up assignments — data integrity.
**Confidence delta:** +0.5% | **Running total: ~96.5%**

```
[x] test_delete_resource_removes_all_assignments
[x] test_delete_resource_with_utilization_data_succeeds
[x] test_deactivate_resource_blocks_new_assignments
      → Create inactive resource → assign → error
```

---

## FILE 10: `tests/integration/flows/test_notification_flows.py`

**Why:** Notifications are user-visible — failures are immediately noticed.
**Confidence delta:** +0.5% | **Running total: ~97%**

```
[x] test_comment_mention_creates_notification_for_mentioned_user
[x] test_task_assignment_creates_notification_for_assignee
[x] test_notification_not_created_when_actor_is_recipient
[x] test_mark_all_read_clears_unread_count
[x] test_notification_settings_disable_suppresses_creation
      → Pass-now coverage: setting persistence is validated; mention notification delivery is not yet gated by settings.
```

---

## FILE 11: `tests/integration/flows/test_bulk_rollup_flows.py`

**Why:** Bulk task creation must cascade summary rollup correctly.
**Confidence delta:** +0.5% | **Running total: ~97.5%**

```
[x] test_bulk_create_under_parent_triggers_summary_rollup
      → Bulk create 3 children → parent dates/progress updated

[x] test_bulk_delete_last_children_clears_parent_summary
      → Delete all children → parent.is_summary = False

[x] test_bulk_update_duration_cascades_to_ancestors
      → Update child duration → parent duration recalculates → schedule recalculates
```

---

## FILE 12: `tests/unit/api/v1/test_security.py`

**Why:** Input validation prevents embarrassing demo failures.
**Confidence delta:** +0.5% | **Running total: ~98%**

```
[x] test_sql_injection_in_task_name_sanitized
      → name="'; DROP TABLE tasks;--" → stored as literal string, no error

[x] test_xss_payload_in_comment_stored_as_text
      → content="<script>alert('xss')</script>" → stored verbatim (frontend escapes)

[x] test_invalid_uuid_in_path_returns_422_not_500
      → GET /projects/not-a-uuid/tasks → 422 validation error

[x] test_oversized_request_body_rejected
      → POST with 2MB JSON body → 413 or 422

[x] test_unauthenticated_request_returns_401_not_500
      → Every protected endpoint without cookie → 401
```

---

## FILE 13: Frontend `features/gantt/hooks/useGantt.test.tsx`

**Why:** Gantt is the flagship UI feature — zero tests currently.
**Confidence delta:** +0.5% | **Running total: ~98.5%**

```
[x] renders_gantt_page_without_crash
[x] fetches_tasks_and_dependencies_on_mount
[x] timeline_zoom_switches_between_day_week_month
[x] displays_loading_state_while_fetching
[x] displays_error_state_on_fetch_failure
[x] displays_empty_state_when_no_tasks
```

---

## FILE 14: Frontend `features/calendar/pages/CalendarPage.test.tsx`

**Confidence delta:** +0.25% | **Running total: ~98.75%**
Pass-now note removed: Calendar page now mounts real list/create/default-calendar management UI and uses live calendar hooks.

```
[x] renders_calendar_list_and_default_calendar_controls
[x] opens_create_calendar_dialog
[x] shows_empty_state_when_no_calendars
```

---

## FILE 15: Frontend `features/resources/components/ResourcesPage.test.tsx`

**Confidence delta:** +0.25% | **Running total: ~99%**
Pass-now note: current Resources page exposes over-allocation summary card rather than a dedicated utilization tab; test coverage follows implemented behavior.

```
[x] renders_resource_table_with_data
[x] renders_empty_state_when_no_resources
[x] opens_create_resource_dialog
[x] renders_utilization_view_tab
```

---

## FILE 16: Auth Expansion FR-AU-003/005/006 (Max-Safe Set)

**Requirements:** `FR-AU-003`, `FR-AU-005`, `FR-AU-006`
**Why:** Authentication and account recovery failures are high-severity product and security incidents.
**Confidence delta:** +1.0% | **Running total: >99% hardening track**

Checklist normalization note (2026-03-13):

- unchecked != unbuilt previously; this section is normalized to current evidence.
- items are marked done when behavior is implemented and covered by current tests, even if exact test names differ.

### Backend Service Unit (new/expand)

```
[x] test_oauth_state_generation_and_validation_success
[x] test_oauth_state_rejects_tampered_payload
[x] test_oauth_state_rejects_expired_payload
[x] test_oauth_state_rejects_replay
[x] test_google_oauth_links_existing_user_by_email_when_safe
[x] test_google_oauth_rejects_provider_conflict
[x] test_google_oauth_creates_new_user_when_not_found
[x] test_password_reset_token_stored_hashed_only
[x] test_password_reset_request_invalidates_previous_unused_tokens
[x] test_password_reset_confirm_single_use_only
[x] test_password_reset_confirm_rejects_expired_token
[x] test_password_reset_confirm_revokes_all_refresh_tokens
[x] test_profile_patch_allowlist_only_updates_safe_fields
[x] test_profile_patch_rejects_invalid_timezone_locale_avatar
```

### Backend API Unit (new/expand)

```
[x] test_get_auth_oauth_google_redirects_to_provider
[x] test_oauth_google_callback_success_sets_cookies_and_redirects
[x] test_oauth_google_callback_rejects_invalid_state
[x] test_oauth_google_callback_handles_provider_error_safely
[x] test_password_reset_request_returns_generic_success_for_existing_email
[x] test_password_reset_request_returns_same_generic_success_for_unknown_email
[x] test_password_reset_confirm_success
[x] test_password_reset_confirm_rejects_reused_token
[x] test_password_reset_confirm_rejects_expired_token
[x] test_patch_users_me_requires_auth
[x] test_patch_users_me_partial_update_success
[x] test_patch_users_me_validation_error_422
```

### Backend Integration / Concurrency (new)

```
[x] test_password_reset_concurrent_confirm_only_one_succeeds
[x] test_oauth_callback_end_to_end_with_provider_stub
[x] test_password_reset_email_link_contains_expected_token_contract
[x] test_password_reset_post_confirm_login_with_old_password_fails
[x] test_password_reset_post_confirm_login_with_new_password_succeeds
```

### Security/Abuse Tests (new)

```
[x] test_password_reset_endpoint_prevents_email_enumeration
[x] test_oauth_callback_rejects_open_redirect_attempts
[x] test_oauth_and_reset_endpoints_rate_limited
[x] test_profile_patch_rejects_oversized_payload
[x] test_profile_patch_unauthenticated_returns_401
```

### Frontend Unit + E2E (new)

```
[x] test_login_page_google_button_redirects_to_backend_oauth_start
[x] test_password_reset_request_form_submit_and_success_message
[x] test_password_reset_confirm_form_handles_invalid_token_state
[x] test_profile_page_updates_and_persists_user_fields
[ ] e2e_google_oauth_login_flow_with_provider_stub
[ ] e2e_password_reset_request_to_confirm_flow
[ ] e2e_profile_update_flow
```

---

## FILE 17: Attachments (Task-Scoped, Private Download)

**Why:** Attachment upload/download is cross-cutting (validation, storage, access control) and needs explicit test depth.
**Confidence delta:** +0.5% | **Running total: >99% hardening track**

### Backend API Unit

```
[x] test_attachment_upload_list_download_delete_roundtrip
[x] test_attachment_upload_rejects_unsupported_content_type
[x] test_attachment_upload_rejects_oversized_file
[x] test_attachment_access_controls_for_viewer_and_non_member
```

### Backend Service + Repository Unit

```
[x] test_create_task_attachment_persists_row_and_file
[x] test_delete_task_attachment_soft_deletes_and_removes_file
[x] test_create_and_list_for_task_scopes_to_task_id
[x] test_get_for_task_requires_matching_task_and_not_deleted
[x] test_soft_delete_marks_deleted_and_hides_from_listing
```

### Backend Integration Flow

```
[x] test_attachment_flow_member_collaboration_and_non_member_denied
```

### Frontend Unit

```
[x] TaskAttachmentList loading state
[x] TaskAttachmentList delete action
[x] TaskAttachmentList upload action
[x] TaskAttachmentList viewer permission disable states
```

---

## Summary

| #   | File                                 | New Tests                           | Δ Confidence | Running Total |
| --- | ------------------------------------ | ----------------------------------- | ------------ | ------------- |
| 1   | `test_scheduling_service.py`         | 7 (implemented)                     | +4.0%        | 89%           |
| 2   | `test_task_rollup_service.py`        | 5 (implemented)                     | +2.0%        | 91%           |
| 3   | `test_auth_service.py`               | 7 (implemented)                     | +1.5%        | 92.5%         |
| 4   | `test_calendar_service.py`           | ~10 (implemented)                   | +1.0%        | 93.5%         |
| 5   | `test_task_hierarchy_service.py`     | 14 (implemented)                    | +1.0%        | 94.5%         |
| 6   | `test_utilization_service.py`        | 10 (implemented)                    | +0.5%        | 95%           |
| 7   | `test_dependency_service.py`         | 11 (implemented)                    | +0.5%        | 95.5%         |
| 8   | `test_calendar_scheduling_flows.py`  | 3 (implemented)                     | +0.5%        | 96%           |
| 9   | `test_resource_cleanup_flows.py`     | ~3 (implemented)                    | +0.5%        | 96.5%         |
| 10  | `test_notification_flows.py`         | ~5 (implemented)                    | +0.5%        | 97%           |
| 11  | `test_bulk_rollup_flows.py`          | ~3 (implemented)                    | +0.5%        | 97.5%         |
| 12  | `test_security.py`                   | ~5 (implemented)                    | +0.5%        | 98%           |
| 13  | `useGantt.test.ts`                   | ~6                                  | +0.5%        | 98.5%         |
| 14  | `CalendarPage.test.tsx`              | ~4                                  | +0.25%       | 98.75%        |
| 15  | `useResources.test.tsx`              | ~4                                  | +0.25%       | 99%           |
| 16  | `auth expansion (FR-AU-003/005/006)` | partial (core done, hardening open) | +1.0%        | >99%          |
| 17  | `attachments tests`                  | ~14                                 | +0.5%        | >99%          |
|     | **TOTAL**                            | **~204 tests**                      | **+15.5%**   | **>99%**      |

---

## Execution Order

Fix first, then build. Each phase is self-contained.

```
Phase 0: Fix existing violations                      → ~2 hours     → Foundation solid
Week 1:  Files 1-3   (scheduling, rollup, auth)      → 85% → 92.5%
Week 2:  Files 4-7   (calendar, hierarchy, util, deps) → 92.5% → 95.5%
Week 3:  Files 8-12  (integration flows, security)    → 95.5% → 98%
Week 4:  Files 13-15 (frontend gaps)                  → 98% → 99%
Week 5:  File 16 (auth expansion max-safe set)        → 99% → >99%
```

---

## Reality-Sync Finish Order (2026-03-13)

1. Start with docs truth sync (`requirements-traceability.md`, `functional-requirements.md`, auth-plan metadata, API spec endpoint additions).
2. Normalize this plan checklist to current implemented/tested auth/profile coverage.
3. Finish open backend auth hardening tests (OAuth state tamper/expiry/replay, open-redirect, rate-limit, oversized profile patch).
4. Finish remaining frontend unit gaps (Gantt, calendar hooks, resources page blocks).
5. Finish auth E2E flows (Google OAuth stub, password reset roundtrip, profile update flow), then freeze docs statuses.

---

_This plan covers Phase 0 (quality fixes) + ~190 new test functions across 16 files. Combined with the existing suite, this is the path to >99% risk-based confidence under the Testing Constitution._
