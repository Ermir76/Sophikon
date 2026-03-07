# FR-PM-005 Project Dashboard

- **Created**: 2026-03-07
- **Completed**: 2026-03-07
- **Status**: Completed
- **Priority**: Must (V1.0)

## Final Decisions

| Decision | Implemented Choice |
| --- | --- |
| Response wrapper | No `data` wrapper. The endpoint returns the raw response model. |
| Project route | `GET /api/v1/projects/{project_id}/dashboard` in `projects.py`. |
| `insights/overview` | Removed for projects. Organization insights stay in `insights.py`. |
| Risk signals | Dashboard page composes `useAiSuggestions(projectId, 5)` in the frontend. |
| Project page | `ProjectOverviewPage` stays mounted at `/projects/:projectId`. |
| Deferred fields | `schedule.baseline_finish_date`, `schedule.variance_days`, and `earned_value` are deferred to V1.1. |

## Completed Work

### Backend

- [x] Added `ProjectDashboardResponse` and supporting dashboard schemas in `backend/app/schema/insights.py`
- [x] Added `get_project_dashboard()` in `backend/app/service/insights_service.py`
- [x] Added `GET /projects/{project_id}/dashboard` in `backend/app/api/v1/endpoints/projects.py`
- [x] Removed the project-specific `GET /projects/{project_id}/insights/overview` route
- [x] Aggregated:
  - [x] task status counts
  - [x] milestone counts and upcoming milestone list
  - [x] overdue task list
  - [x] resource utilization summary
  - [x] cost totals
  - [x] critical path summary
  - [x] recent activity

### Frontend

- [x] Added `projectService.getDashboard(projectId, window?)`
- [x] Added `useProjectDashboard()`
- [x] Added `ProjectDashboard` types under `frontend/src/features/projects/types.ts`
- [x] Switched `ProjectOverviewPage` from the old project-overview insights contract to the dashboard contract
- [x] Rendered:
  - [x] overall completion
  - [x] task status breakdown
  - [x] milestone summary
  - [x] critical path summary
  - [x] resource utilization summary
  - [x] cost summary
  - [x] upcoming milestones list
  - [x] overdue tasks list
  - [x] recent activity
  - [x] AI risk widget using AI suggestions
- [x] Kept dashboard drill-downs on existing project routes only

### Tests

- [x] Backend API coverage for project dashboard auth, membership, validation, and response shape
- [x] Backend service coverage for dashboard aggregation
- [x] Frontend hook coverage for `useProjectDashboard`
- [x] Frontend page coverage for `ProjectOverviewPage`, including AI failure fallback

### Docs

- [x] Updated `docs/02-design/api-specification.md` to match the mounted V1 dashboard contract
- [x] Updated `docs/03-implementation/requirements-traceability.md`
- [x] Updated `docs/01-requirements/functional-requirements.md`

## Verification

```bash
cd backend
uv run pytest tests/api/v1/test_projects.py tests/api/v1/test_insights.py tests/test_insights_service.py

cd ../frontend
npm run test -- src/features/projects/hooks/useProjectDashboard.test.tsx src/features/projects/pages/ProjectOverviewPage.test.tsx
```

Latest result:

- Backend: `32 passed`
- Frontend: `4 passed`
