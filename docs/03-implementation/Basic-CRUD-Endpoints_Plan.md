# Plan: Basic CRUD Endpoints

## Context

Week 1 Foundation task from docs/03-implementation/project-plan.md. Auth is done; the frontend team needs working CRUD APIs by Week 2 so they can build the UI. Advanced features (hierarchy, WBS generation, bulk ops, circular detection, workload calc) are deferred to later weeks.

## Scope

CRUD for 5 core entities: Projects, Tasks, Resources, Dependencies, Assignments — following the API spec in docs/02-design/api-specification.md and matching the existing auth endpoint patterns.

Files to Create (15 new, 2 modified)

1.  Shared Utilities

- backend/app/schema/common.py (NEW) — PaginatedResponse[T] generic schema (items, total, page, per_page, total_pages)

2.  Authorization Dependencies

- backend/app/api/deps.py (MODIFY) — Add:
- get_project_or_404(project_id, db, user) → loads project, checks not deleted, verifies user is owner or member via ProjectMember join with Role. Returns NamedTuple(project, role_name).
- get_task_with_project_access(task_id, db, user) → loads task, verifies its project access. For assignment endpoints that nest under /tasks/{task_id}.

3.  Projects — GET/POST /projects, GET/PATCH/DELETE /projects/{project_id}

- backend/app/schema/project.py (NEW) — ProjectCreate, ProjectUpdate, ProjectListItem, ProjectDetail
- backend/app/service/project_service.py (NEW) — list_projects (paginated, owner+member, search/status filter), create_project, update_project, soft_delete_project
- backend/app/api/v1/endpoints/projects.py (NEW) — 5 endpoints. Update restricted to owner/manager, delete to owner only.

4.  Tasks — GET/POST /projects/{project_id}/tasks, GET/PATCH/DELETE /projects/{project_id}/tasks/{task_id}

- backend/app/schema/task.py (NEW) — TaskCreate, TaskUpdate, TaskResponse
- backend/app/service/task_service.py (NEW) — list_tasks (paginated, ordered by order_index), create_task, get_task_by_id, update_task soft_delete_task
- backend/app/api/v1/endpoints/tasks.py (NEW) — 5 endpoints, all gated by get_project_or_404

5.  Resources — GET/POST /projects/{project_id}/resources, GET/PATCH/DELETE .../resources/{resource_id}

- backend/app/schema/resource.py (NEW) — ResourceCreate, ResourceUpdate, ResourceResponse
- backend/app/service/resource_service.py (NEW) — list_resources (filter by type, include_inactive), create_resource, get_resource_by_id, update_resource, delete_resource (hard delete — no soft-delete columns on Resource model)
- backend/app/api/v1/endpoints/resources.py (NEW) — 5 endpoints

6.  Dependencies — GET/POST /projects/{project_id}/dependencies, PATCH/DELETE .../dependencies/{dependency_id}

- backend/app/schema/dependency.py (NEW) — DependencyCreate, DependencyUpdate,
  DependencyResponse
- backend/app/service/dependency_service.py (NEW) — list_dependencies, create_dependency (validates both tasks exist in project, no self-ref, catches duplicate IntegrityError), get_dependency_by_id, update_dependency, delete_dependency (hard delete)
- backend/app/api/v1/endpoints/dependencies.py (NEW) — 4 endpoints

7.  Assignments — GET/POST /projects/{project_id}/tasks/{task_id}/assignments, PATCH/DELETE /api/v1/assignments/{assignment_id}

- backend/app/schema/assignment.py (NEW) — AssignmentCreate, AssignmentUpdate,
  AssignmentResponse
- backend/app/service/assignment_service.py (NEW) — list_assignments (by task), create_assignment (validates resource in same project, catches duplicate IntegrityError), get_assignment_by_id, update_assignment, delete_assignment (hard delete)
- backend/app/api/v1/endpoints/assignments.py (NEW) — Two routers: task_assignments_router (list/create nested under tasks) and assignments_router (update/delete flat). Auth checks via task→project chain.

8.  Router Registration

- backend/app/main.py (MODIFY) — Register all 7 new routers under /api/v1 prefix

## Key Patterns (matching existing auth code)

- Router → Service → DB (service handles commit())
- model_dump(exclude_unset=True) for PATCH partial updates
- from_attributes=True on response schemas
- HTTPException for errors (400, 403, 404, 409)
- All fields use Decimal in schemas where the model uses DECIMAL columns (mapped as float)

Implementation Order

1.  schema/common.py
2.  api/deps.py (add project access deps)
3.  Projects (schema → service → router)
4.  Tasks
5.  Resources
6.  Dependencies
7.  Assignments
8.  main.py router registration (incremental)

## Verification

- Start Docker DB + run uvicorn app.main:app --reload from backend/
- Hit /docs (Swagger UI) to verify all endpoints appear
- Test project create → task create → resource create → assignment create flow via Swagger
