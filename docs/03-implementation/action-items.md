# Action Items — Deploy-First Approach

**Date:** February 15, 2026
**Source:** All 6 corrected review documents
**Strategy:** Make what exists production-ready FIRST, then add features on a live app.

---

## Phase 1: Make It Deployable (This Week)

### Security (must fix before deploy)

- [x] **Fix org membership check on project create** — authorization bypass — 15 min
  - File: `backend/app/api/v1/endpoints/projects.py:67-74`
  - Add `get_org_membership_or_404(db, body.organization_id, user)` before creating

- [x] **Fix `org_id: str` → `org_id: UUID`** in organization endpoints — 10 min
  - File: `backend/app/api/deps.py:68` and related endpoints

- [x] **Add global exception handler** — prevents stack trace leaks in production — 15 min
  - File: `backend/app/main.py`

### Production Quality (deploy won't embarrass you)

- [x] **Fix DashboardPage** — add `isLoading` / `isError` checks — 5 min
  - File: `frontend/src/pages/DashboardPage.tsx`

- [x] **Fix generic toast errors** — use `getErrorMessage(error)` — 10 min
  - Files: `CreateProjectDialog.tsx:78`, `OrgSettingsPage.tsx:80`, `OrgMembersPage.tsx:58,73,89`

- [x] **Fix `@ts-expect-error` in api.ts** — add `RetryableRequest` interface — 5 min
  - File: `frontend/src/lib/api.ts:28`

- [x] **Replace TODO placeholder routes** with proper stub components — 5 min
  - File: `frontend/src/App.tsx` (lines 65, 83)

### Cleanup (2 minutes)

- [x] **Delete `backend/main.py`** — dead entry point

### Tooling (clean CI, clean commits)

- [x] **Fix ESLint errors** — 30 min
- [x] **Add Ruff config** to `backend/pyproject.toml` — 5 min
- [x] **Add Prettier config** — create `frontend/.prettierrc.json` — 5 min
- [x] **Fix pre-commit hooks** — install + scope + local hooks — 30 min
- [x] **Create `frontend/.env.example`** — 1 min

### Deploy

The steps before deploy are:

1. Move landing page out of docs/ into its own landing/ folder —
   it becomes a deployable artifact
2. Decide the URL structure: sophikon.eu → landing,
   app.sophikon.eu → React app, api.sophikon.eu → FastAPI (needs a
   domain — get one soon)
3. Production Docker for backend only
4. Nginx only for the backend (reverse proxy in front of FastAPI)
5. S3 bucket + CloudFront for landing, separate bucket +
   CloudFront for app
6. RDS for PostgreSQL, EC2 or ECS for backend
7. GitHub Actions CI/CD — push to main → auto deploy frontend to
   S3, auto deploy backend to EC2/ECS

- [ ] **Production Docker setup** — Dockerfile for backend + frontend, docker-compose.prod.yml
- [ ] **Nginx config** — reverse proxy, request size limits, static files
- [ ] **Environment config** — production .env, CORS origins, secret keys
- [ ] **Deploy to hosting** (Railway / Render / VPS / university server)

**Phase 1 total: ~1 day**

---

## Phase 2: Core Features (build on live app)

Each week: build feature → deploy it → teacher sees progress.

### Week 3: Task Management

- [ ] Task table view (the core of a PM app)
- [ ] Task CRUD with hierarchy
- [ ] Inline editing, drag-drop reordering
- [ ] Add project-level RBAC to sidebar as pages get content

### Week 4: Gantt Chart

- [ ] Gantt chart component (visual wow factor)
- [ ] Dependency arrows
- [ ] Timeline with zoom

### Week 5: Scheduling Engine

- [ ] Auto date calculation from dependencies
- [ ] Critical path highlighting
- [ ] Add domain exceptions before this (complex logic needs clean errors)
- [ ] Add structured logging before this (need to debug scheduling)

### Week 6+: If Time Permits

- [ ] Resource management
- [ ] AI integration MVP
- [ ] Import/export
- [ ] Pagination on assignments list

---

## Nice-to-Have (only if time)

These improve quality but don't affect the grade:

- [ ] Rate limiting (auth endpoints)
- [ ] Request ID middleware
- [ ] Mypy type checking
- [ ] pytest coverage threshold (`--cov-fail-under=80`)
- [ ] Dependency security scanning
- [ ] Accessibility audit (axe DevTools)
- [ ] E2E tests

---

## What You Already Have (deployable now)

Your teacher will see a real deployed app with:

- User registration & login (JWT + httpOnly cookies)
- Multi-tenancy (organizations)
- RBAC (org-level admin/member/viewer)
- Project CRUD scoped to organizations
- Org switcher, responsive sidebar
- Clean API with proper validation

That's already solid for a degree. Everything after Phase 1 is bonus points.

---

**All items sourced from corrected reviews. Original Kiro AI false positives excluded.**
