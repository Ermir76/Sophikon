# Frontend Architecture Improvements Plan

> **Created:** 2026-02-14
> **Scope:** All files under `frontend/src/`
> **Goal:** Address every bug, security risk, performance bottleneck, consistency issue, accessibility gap, and scalability concern identified in the frontend architecture review.

---

## Table of Contents

1. [P0 — Critical Bugs](#1-p0--critical-bugs)
2. [P1 — Security](#2-p1--security)
3. [P1 — Missing Infrastructure](#3-p1--missing-infrastructure)
4. [P2 — Data Fetching Overhaul](#4-p2--data-fetching-overhaul)
5. [P2 — Performance](#5-p2--performance)
6. [P2 — Component Architecture](#6-p2--component-architecture)
7. [P2 — Consistency & Code Quality](#7-p2--consistency--code-quality)
8. [P3 — Duplication Reduction](#8-p3--duplication-reduction)
9. [P3 — Accessibility](#9-p3--accessibility)
10. [P3 — Testing Infrastructure](#10-p3--testing-infrastructure)
11. [File-by-File Change Map](#11-file-by-file-change-map)

---

## 1. P0 — Critical Bugs

### 1.1 Fix broken 401 redirect URL — **DONE**

**File:** `src/services/api.ts:29`
**Problem:** The response interceptor redirects to `/app/login` on 401 errors, but the actual route is `/login`. Every expired-token scenario sends users to a blank 404 page.

**Fix:**

```ts
// BEFORE (broken)
window.location.href = "/app/login";

// AFTER (correct)
window.location.href = "/login";
```

**But see 1.2 — the URL fix alone is not enough.**

### 1.2 Replace hard page reload with router-based redirect — **DONE**

**File:** `src/services/api.ts:27-31`
**Problem:** Even with the correct URL, `window.location.href` causes a full browser reload, destroying all in-memory React state, unsaved form data, Zustand stores, and React context. This is a jarring UX.

**Solution:** Replace with a store-driven approach:

1. Add a `sessionExpired` flag to `auth-store.ts`.
2. In the 401 interceptor, call `useAuthStore.getState().logout()` (already done) — this clears the token and sets `isAuthenticated = false`.
3. `ProtectedRoute` already watches `isAuthenticated` and redirects to `/login` via React Router's `<Navigate>`. So simply **remove the `window.location.href` line entirely** — the existing `ProtectedRoute` guard will handle the redirect on next render.

**Final interceptor:**

```ts
api.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      useAuthStore.getState().logout();
      // ProtectedRoute will handle the redirect via React Router
    }
    return Promise.reject(error);
  },
);
```

**Optionally:** Show a "Session expired" toast before redirecting, so the user understands why they were sent back to login.

### 1.3 Add 404 catch-all route — **DONE**

**File:** `src/App.tsx`
**Problem:** No `<Route path="*">` exists. Navigating to any undefined URL renders a blank page inside the layout shell.

**Fix:** Add a catch-all at the end of the route tree:

```tsx
// After all other routes, inside ProtectedRoute:
<Route path="*" element={<NotFoundPage />} />

// Also add one for guest routes:
<Route path="*" element={<Navigate to="/login" replace />} />
```

**New file:** `src/pages/NotFoundPage.tsx` — Simple page with "Page not found" message and a "Go to Dashboard" link.

---

## 2. P1 — Security

### 2.1 Move token storage from localStorage to httpOnly cookies — **DONE**

**Files:** `src/lib/auth.ts`, `src/services/api.ts`, `src/store/auth-store.ts`, backend auth endpoints
**Problem:** JWT tokens in `localStorage` are readable by any JavaScript, including XSS payloads from third-party dependencies.

**Solution (requires backend coordination):**

1. **Backend:** Set `access_token` and `refresh_token` as `httpOnly`, `Secure`, `SameSite=Strict` cookies in the login/register/refresh response headers. Remove tokens from the JSON response body.
2. **Frontend `lib/auth.ts`:** Remove `saveAuth()`, `getAccessToken()`, `getRefreshToken()`, `clearAuth()` — cookies are now managed by the browser automatically.
3. **Frontend `services/api.ts`:** Remove the request interceptor that attaches `Authorization: Bearer`. Instead, configure axios with `withCredentials: true` so cookies are sent automatically.
4. **Frontend `store/auth-store.ts`:** The `login` action only needs to store the `user` object (still in localStorage or Zustand persist). The `isAuthenticated` flag can be derived from the presence of a user object. Token fields are removed from the store.
5. **Frontend `services/api.ts`:** The 401 interceptor only needs to clear the user from the store; the browser handles cookie expiry.

**If httpOnly cookies are not feasible short-term:**

- Store only the short-lived `access_token` in memory (Zustand store, no localStorage).
- Store the `refresh_token` in an `httpOnly` cookie (backend sets it).
- On page reload, call `/auth/refresh` to get a new `access_token` into memory.
- Implement strict CSP headers on the backend.

### 2.2 Implement token refresh flow (or remove dead code) — **DONE**

**Files:** `src/services/auth.ts:67-70`, `src/services/api.ts`, `src/lib/auth.ts`
**Problem:** `auth.refresh()` is defined but never called. The refresh token is stored in localStorage but never used. Users get silently logged out when the access token expires. The unused refresh token expands the attack surface for free.

**Option A — Implement refresh (recommended):**

Add a retry mechanism in the 401 response interceptor:

```ts
api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config;
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      try {
        const refreshToken = getRefreshToken();
        if (!refreshToken) throw new Error("No refresh token");
        const response = await auth.refresh(refreshToken);
        // Save new tokens
        useAuthStore
          .getState()
          .login(
            response.tokens.access_token,
            response.tokens.refresh_token,
            response.user,
          );
        // Retry original request with new token
        originalRequest.headers.Authorization = `Bearer ${response.tokens.access_token}`;
        return api(originalRequest);
      } catch {
        useAuthStore.getState().logout();
        return Promise.reject(error);
      }
    }
    return Promise.reject(error);
  },
);
```

**Option B — Remove dead code:**
If refresh is not needed yet, delete `auth.refresh()` from `services/auth.ts`, delete `getRefreshToken()` from `lib/auth.ts`, and stop storing the refresh token in localStorage.

### 2.3 Validate localStorage data with Zod instead of `as` casts — **DONE**

**File:** `src/lib/auth.ts:84`
**Problem:** `JSON.parse(raw) as AuthUser` trusts that whatever is in localStorage conforms to `AuthUser`. Corrupted or maliciously modified localStorage could inject unexpected properties or shapes.

**Fix:**

```ts
import { z } from "zod";

const authUserSchema = z.object({
  id: z.string(),
  email: z.string(),
  full_name: z.string(),
});

export function getUser(): AuthUser | null {
  const raw = localStorage.getItem(USER_KEY);
  if (!raw) return null;
  try {
    return authUserSchema.parse(JSON.parse(raw));
  } catch {
    clearAuth(); // Corrupted data — clear everything
    return null;
  }
}
```

### 2.4 Replace `Record<string, any>` with proper types — **DONE** — **DONE**

**File:** `src/types/organization.ts:8`
**Problem:** `settings?: Record<string, any>` bypasses TypeScript's type safety entirely.

**Fix:** Either define the actual settings shape:

```ts
export interface OrganizationSettings {
  defaultProjectCurrency?: string;
  timezone?: string;
  // ... actual fields
}
```

Or at minimum use `unknown` to force runtime checks:

```ts
settings?: Record<string, unknown>;
```

This is already done correctly in `types/project.ts:19` — make it consistent.

---

## 3. P1 — Missing Infrastructure

### 3.1 Add a top-level ErrorBoundary — **DONE**

**Problem:** Any uncaught JavaScript error in any component crashes the entire app with a white screen and no recovery path.

**New file:** `src/components/ErrorBoundary.tsx`

```tsx
import { Component, type ReactNode } from "react";

interface Props {
  children: ReactNode;
}
interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false, error: null };

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, info: React.ErrorInfo) {
    console.error("Uncaught error:", error, info);
    // Future: send to error reporting service
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex min-h-screen items-center justify-center">
          <div className="text-center space-y-4">
            <h1 className="text-2xl font-bold">Something went wrong</h1>
            <p className="text-muted-foreground">{this.state.error?.message}</p>
            <button onClick={() => window.location.reload()}>
              Reload Page
            </button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}
```

**Integration in `src/main.tsx`:**

```tsx
<StrictMode>
  <ErrorBoundary>
    <BrowserRouter>...</BrowserRouter>
  </ErrorBoundary>
</StrictMode>
```

**Optional:** Add per-route error boundaries inside `AppLayout` for more granular recovery.

### 3.2 Add loading state for initial auth hydration — **DONE**

**File:** `src/components/ProtectedRoute.tsx`
**Problem:** `ProtectedRoute` checks `isAuthenticated` synchronously. If token validation ever becomes async (e.g., checking expiry, calling `/auth/me`), there's no loading state — users see a flash of the login page before being redirected back.

**Fix:** Add an `isHydrated` or `isInitializing` flag to the auth store. Show a full-screen loader while hydrating, then redirect based on the result.

---

## 4. P2 — Data Fetching Overhaul (TanStack Query)

### 4.1 Install and configure TanStack Query — **DONE**

**Problem:** Every page manually manages `useState` + `useCallback` + `useEffect` + try/catch + loading/error state. This creates boilerplate, no caching, no deduplication, no background refetching, race conditions on rapid navigation, and stale data on org switch.

**Steps:**

1. `npm install @tanstack/react-query @tanstack/react-query-devtools`

2. **New file:** `src/lib/query-client.ts`

   ```ts
   import { QueryClient } from "@tanstack/react-query";
   export const queryClient = new QueryClient({
     defaultOptions: {
       queries: {
         staleTime: 30_000, // 30 seconds
         retry: 1,
         refetchOnWindowFocus: false,
       },
     },
   });
   ```

3. **Update `src/main.tsx`:**

   ```tsx
   import { QueryClientProvider } from "@tanstack/react-query";
   import { ReactQueryDevtools } from "@tanstack/react-query-devtools";
   import { queryClient } from "@/lib/query-client";

   // Wrap App:
   <QueryClientProvider client={queryClient}>
     <App />
     <ReactQueryDevtools />
   </QueryClientProvider>;
   ```

### 4.2 Create query hooks for each domain — **DONE**

**New file:** `src/hooks/use-projects.ts`

```ts
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { projectService } from "@/services/project";
import { useOrgStore } from "@/store/org-store";

export function useProjects() {
  const activeOrgId = useOrgStore((s) => s.activeOrgId);
  return useQuery({
    queryKey: ["projects", activeOrgId],
    queryFn: () => projectService.list(activeOrgId!),
    enabled: !!activeOrgId,
  });
}

export function useCreateProject() {
  const queryClient = useQueryClient();
  const activeOrgId = useOrgStore((s) => s.activeOrgId);
  return useMutation({
    mutationFn: (data: ProjectCreate) =>
      projectService.create(activeOrgId!, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["projects", activeOrgId] });
    },
  });
}
```

**New file:** `src/hooks/use-organizations.ts`

```ts
export function useOrganizations() {
  return useQuery({
    queryKey: ["organizations"],
    queryFn: () => organizationService.list(1, 100),
  });
}

export function useOrgMembers(orgId: string | null) {
  return useQuery({
    queryKey: ["org-members", orgId],
    queryFn: () => organizationService.listMembers(orgId!),
    enabled: !!orgId,
  });
}

export function useMyOrgRole(orgId: string | null) {
  // Ideally use a dedicated backend endpoint (see 4.4)
  const userId = useAuthStore((s) => s.user?.id);
  const { data: membersData } = useOrgMembers(orgId);
  return membersData?.items.find((m) => m.user_id === userId)?.role ?? null;
}
```

### 4.3 Simplify pages by removing manual fetch boilerplate — **DONE**

**Example — `ProjectsPage.tsx` before and after:**

```tsx
// BEFORE: 30 lines of useState/useCallback/useEffect/try-catch
const [projects, setProjects] = useState<Project[]>([]);
const [loading, setLoading] = useState(false);
const fetchProjects = useCallback(async () => { ... }, [activeOrganization]);
useEffect(() => { fetchProjects(); }, [fetchProjects]);

// AFTER: 1 line
const { data, isLoading } = useProjects();
const projects = data?.items ?? [];
```

Apply this transformation to:

- `ProjectsPage.tsx` — replace manual fetch with `useProjects()`
- `OrgMembersPage.tsx` — replace manual fetch with `useOrgMembers()`
- `OrgSettingsPage.tsx` — no data fetch to replace, but mutations should use `useMutation`

### 4.4 Reduce Zustand to client-only state — **DONE**

After TanStack Query handles all server state, the org store should only manage:

- `activeOrgId` (persisted to localStorage)
- `setActiveOrg(id)` (just sets the ID — Query handles refetching via key change)

Remove from org store:

- `organizations` array (now in Query cache)
- `activeOrganization` object (derived from Query data + `activeOrgId`)
- `currentRole` (now from `useMyOrgRole` hook)
- `isLoading`, `error` (handled by Query)
- `fetchOrgs()` (replaced by Query)
- The `useAuthStore.subscribe` side effect at the bottom

### 4.5 Add a backend `/organizations/{id}/me` endpoint — **DONE**

**Problem:** `org-store.ts` fetches the entire member list (`listMembers`) just to find the current user's role. This is an O(n) client-side scan that happens on every org switch and every app load.

**Backend fix:** Add `GET /organizations/{orgId}/me` → returns `{ role: "admin", joined_at: "..." }`.

**Frontend fix:** Replace the member-list-scan with:

```ts
export function useMyOrgRole(orgId: string | null) {
  return useQuery({
    queryKey: ["org-role", orgId],
    queryFn: () => organizationService.getMyRole(orgId!),
    enabled: !!orgId,
  });
}
```

### 4.6 Fix org switch not refreshing page data — **DONE**

**Problem:** Switching organization via `OrgSwitcher` updates the org store, but page-level data (projects, members) stays stale until the user navigates away and back.

**Fix with TanStack Query:** This is solved automatically because query keys include `activeOrgId`. When the ID changes, queries with the old key become stale and queries with the new key fire automatically.

### 4.7 Fix hard-coded pagination ceiling

**File:** `src/store/org-store.ts:33`
**Problem:** `organizationService.list(1, 100)` silently drops organizations beyond the 100th.

**Fix (with TanStack Query):** Use `useInfiniteQuery` or paginated queries. At minimum, replace the magic `100` with a proper paginated fetch that loads all pages, or add pagination UI.

---

## 5. P2 — Performance

### 5.1 Add route-level code splitting with React.lazy — **DONE**

**File:** `src/App.tsx`
**Problem:** All 11 page components are eagerly imported, shipping the entire application in a single bundle.

**Fix:**

```tsx
import { lazy, Suspense } from "react";

const LoginPage = lazy(() => import("./pages/auth/LoginPage"));
const RegisterPage = lazy(() => import("./pages/auth/RegisterPage"));
const DashboardPage = lazy(() => import("./pages/DashboardPage"));
const ProjectsPage = lazy(() => import("./pages/ProjectsPage"));
const TasksPage = lazy(() => import("./pages/TasksPage"));
const GanttPage = lazy(() => import("./pages/GanttPage"));
const ResourcesPage = lazy(() => import("./pages/ResourcesPage"));
const CalendarPage = lazy(() => import("./pages/CalendarPage"));
const ReportsPage = lazy(() => import("./pages/ReportsPage"));
const OrgSettingsPage = lazy(() => import("./pages/settings/OrgSettingsPage"));
const OrgMembersPage = lazy(() => import("./pages/settings/OrgMembersPage"));
const ProjectSettingsPage = lazy(() => import("./pages/ProjectSettingsPage"));
```

Wrap `<Outlet />` in `AppLayout` with a `<Suspense>` boundary:

```tsx
<main className="flex-1 overflow-auto">
  <Suspense fallback={<PageLoader />}>
    <Outlet />
  </Suspense>
</main>
```

**New component:** `src/components/PageLoader.tsx` — centered spinner for route transitions.

### 5.2 Fix Zustand selector misuse (prevent unnecessary re-renders) — **DONE**

**Problem:** Several components destructure from the store without a selector, subscribing to the entire state object.

**Files and fixes:**

| File                     | Before                                                                                  | After                                                                                       |
| ------------------------ | --------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------- |
| `AppSidebar.tsx:41`      | `const { currentRole } = useOrgStore();`                                                | `const currentRole = useOrgStore((s) => s.currentRole);`                                    |
| `OrgSwitcher.tsx:22-23`  | `const { organizations, activeOrganization, setActiveOrg, isLoading } = useOrgStore();` | Use individual selectors: `const organizations = useOrgStore((s) => s.organizations);` etc. |
| `ProjectsPage.tsx:64`    | `const { activeOrganization } = useOrgStore();`                                         | `const activeOrganization = useOrgStore((s) => s.activeOrganization);`                      |
| `OrgSettingsPage.tsx:42` | `const { activeOrganization, fetchOrgs } = useOrgStore();`                              | Individual selectors                                                                        |
| `OrgMembersPage.tsx:75`  | `const { activeOrganization } = useOrgStore();`                                         | `const activeOrganization = useOrgStore((s) => s.activeOrganization);`                      |

---

## 6. P2 — Component Architecture

### 6.1 Decompose OrgMembersPage (God Component) — **DONE**

**File:** `src/pages/settings/OrgMembersPage.tsx` (410 lines)
**Problem:** This single file handles data fetching, local UI state, form validation, 3 different dialogs, and the members table. It's hard to test, hard to read, and impossible to reuse parts.

**Decompose into:**

```
src/pages/settings/
  OrgMembersPage.tsx          (orchestrator — 50 lines)
  _components/
    MembersTable.tsx           (table rendering)
    InviteMemberDialog.tsx     (invite form + dialog)
    UpdateRoleDialog.tsx       (role change dialog)
    RemoveMemberAlert.tsx      (remove confirmation)
```

Each sub-component receives props and callbacks. The page component orchestrates state and passes it down.

### 6.2 Centralize role constants and permission helpers — **DONE**

**Problem:** Role strings `"owner" | "admin" | "member"` are hardcoded in multiple files: `OrgMembersPage.tsx`, `AppSidebar.tsx`, `org-store.ts`, `types/organization.ts`.

**New file:** `src/lib/roles.ts`

```ts
export const ORG_ROLES = {
  OWNER: "owner",
  ADMIN: "admin",
  MEMBER: "member",
} as const;

export type OrgRole = (typeof ORG_ROLES)[keyof typeof ORG_ROLES];

export function canManageMembers(role: OrgRole | null): boolean {
  return role === ORG_ROLES.OWNER || role === ORG_ROLES.ADMIN;
}

export function canManageSettings(role: OrgRole | null): boolean {
  return role === ORG_ROLES.OWNER || role === ORG_ROLES.ADMIN;
}

export function canDeleteOrg(role: OrgRole | null): boolean {
  return role === ORG_ROLES.OWNER;
}
```

**Update consumers:**

- `AppSidebar.tsx`: Replace `currentRole === "admin" || currentRole === "owner"` with `canManageMembers(currentRole)`
- `OrgMembersPage.tsx`: Import role constants for `<SelectItem>` values
- `types/organization.ts`: Import `OrgRole` from `lib/roles.ts` instead of defining it locally

### 6.3 Extract "no org selected" guard to layout level — **DONE**

**Problem:** Three pages repeat the identical guard:

```tsx
if (!activeOrganization) {
  return <div className="p-4">Please select an organization.</div>;
}
```

**Fix:** Handle this at the `AppLayout` level. If `activeOrgId` is null and the route requires an org context, render a prompt to select/create an organization instead of the `<Outlet />`.

Alternative: Create a wrapper component:

```tsx
// src/components/RequireOrg.tsx
export function RequireOrg({ children }: { children: ReactNode }) {
  const activeOrganization = useOrgStore((s) => s.activeOrganization);
  if (!activeOrganization) {
    return <NoOrgSelectedPlaceholder />;
  }
  return children;
}
```

---

## 7. P2 — Consistency & Code Quality

### 7.1 Unify service authoring patterns — **DONE**

**Problem:** Three different patterns exist across 3 service files:

| File                       | Pattern                                           |
| -------------------------- | ------------------------------------------------- |
| `services/auth.ts`         | Object literal, arrow functions, `.then()` chains |
| `services/organization.ts` | Object literal, `async` keyword methods           |
| `services/project.ts`      | Object literal, `async` arrow function properties |

**Standard:** Adopt the `organization.ts` pattern (explicit `async` methods with `await`) everywhere. It's the clearest and most debuggable.

**Refactor `services/auth.ts`:**

```ts
export const authService = {
  async login(data: LoginRequest): Promise<AuthResponse> {
    const response = await api.post<AuthResponse>("/auth/login", data);
    return response.data;
  },
  // ... same for register, refresh
};
```

**Refactor `services/project.ts`:** Add explicit return types to all methods.

### 7.2 Standardize import paths — use `@/` everywhere — **DONE**

**Problem:** Services use relative paths (`"../types/api"`, `"./api"`) while components use the `@/` alias.

**Files to fix:**

- `src/services/organization.ts:1` — `"../types/api"` → `"@/types/api"`
- `src/services/organization.ts:4` — `"../types/organization"` → `"@/types/organization"`
- `src/services/project.ts:2` — `"../types/project"` → `"@/types/project"`
- `src/services/project.ts:1` — `"./api"` → `"@/services/api"`
- `src/services/auth.ts:2` — `"./api"` → `"@/services/api"`

### 7.3 Fix manual query string construction in projectService — **DONE**

**File:** `src/services/project.ts:6`
**Problem:**

```ts
// BEFORE — bypasses axios URL encoding, inconsistent with other services
const response = await api.get(`/projects?organization_id=${orgId}`);

// AFTER — uses axios params like every other service method
const response = await api.get("/projects", {
  params: { organization_id: orgId },
});
```

### 7.4 Rename service exports for consistency — **DONE**

**Current:**
| File | Export name |
|------|------------|
| `services/auth.ts` | `auth` |
| `services/organization.ts` | `organizationService` |
| `services/project.ts` | `projectService` |

**Standard:** Use the `*Service` suffix consistently:

- `auth` → `authService`

Update all imports in: `LoginPage.tsx`, `RegisterPage.tsx`.

---

## 8. P3 — Duplication Reduction

### 8.1 Extract shared auth page layout — **DONE**

**Files:** `src/pages/auth/LoginPage.tsx`, `src/pages/auth/RegisterPage.tsx`
**Problem:** ~80% identical structure: outer `div` with `min-h-screen items-center justify-center`, `Card` chrome, error `Alert`, loading button pattern, error handling in `catch`.

**New file:** `src/components/auth/AuthLayout.tsx`

```tsx
export function AuthLayout({
  title,
  description,
  footer,
  children,
}: {
  title: string;
  description: string;
  footer: ReactNode;
  children: ReactNode;
}) {
  return (
    <div className="flex min-h-screen items-center justify-center bg-background p-4">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle className="text-2xl">{title}</CardTitle>
          <CardDescription>{description}</CardDescription>
        </CardHeader>
        <CardContent>{children}</CardContent>
        <CardFooter className="justify-center">{footer}</CardFooter>
      </Card>
    </div>
  );
}
```

### 8.2 Extract shared error handling for API calls — **DONE**

**Problem:** Every form submission handler has this identical catch block:

```ts
if (isAxiosError(err) && err.response?.data?.detail) {
  setError(err.response.data.detail);
} else if (err instanceof Error) {
  setError(err.message);
} else {
  setError("Something went wrong. Please try again.");
}
```

**New utility:** `src/lib/errors.ts`

```ts
import { isAxiosError } from "axios";

export function getErrorMessage(err: unknown): string {
  if (isAxiosError(err) && err.response?.data?.detail) {
    return err.response.data.detail;
  }
  if (err instanceof Error) {
    return err.message;
  }
  return "Something went wrong. Please try again.";
}
```

### 8.3 Extract `getInitials` utility — **DONE**

**File:** `src/components/layout/NavUser.tsx:38-45`
**Problem:** Inline utility function that will likely be needed elsewhere (member avatars, project cards, etc.).

**Move to:** `src/lib/utils.ts`

```ts
export function getInitials(name: string): string {
  return name
    .split(" ")
    .slice(0, 2)
    .map((n) => n[0])
    .join("")
    .toUpperCase();
}
```

---

## 9. P3 — Accessibility

### 9.1 Replace hardcoded gray colors with theme tokens — **DONE**

**Files:** `LoginPage.tsx:96`, `RegisterPage.tsx:111`
**Problem:** `bg-gray-100 dark:bg-gray-900` bypasses the CSS variable-based theme system. If the theme palette changes, these pages won't match.

**Fix:**

```tsx
// BEFORE
<div className="flex min-h-screen items-center justify-center bg-gray-100 p-4 dark:bg-gray-900">

// AFTER
<div className="flex min-h-screen items-center justify-center bg-background p-4">
```

### 9.2 Add focus management on route transitions — **DONE**

**Problem:** When navigating between pages, focus stays wherever it was. Screen reader users get no indication that content changed.

**Solution:** Add a `useEffect` in `AppLayout` that focuses the `<main>` element on pathname change:

```tsx
const mainRef = useRef<HTMLElement>(null);
const location = useLocation();

useEffect(() => {
  mainRef.current?.focus();
}, [location.pathname]);

// Add tabIndex to main:
<main ref={mainRef} tabIndex={-1} className="flex-1 overflow-auto outline-none">
```

### 9.3 Add aria-live feedback for async operations — **DONE**

**Problem:** Toast notifications from Sonner may not be announced to screen readers depending on configuration. Clipboard operations ("Copy Email" in `OrgMembersPage`) give no feedback at all.

**Fixes:**

1. Verify that Sonner's `<Toaster />` renders an `aria-live="polite"` region. If not, configure it.
2. Add a toast confirmation for clipboard copy:
   ```ts
   onClick={() => {
     if (member.user_email) {
       navigator.clipboard.writeText(member.user_email);
       toast.success("Email copied to clipboard");
     }
   }}
   ```

### 9.4 Add skip-to-content link — **DONE**

**File:** `src/components/layout/AppLayout.tsx`
**Problem:** Keyboard users must tab through the entire sidebar to reach the main content.

**Fix:** Add a visually-hidden skip link as the first focusable element:

```tsx
<a
  href="#main-content"
  className="sr-only focus:not-sr-only focus:absolute focus:z-50 focus:p-4 focus:bg-background"
>
  Skip to content
</a>
```

And add `id="main-content"` to the `<main>` element.

---

## 10. P3 — Testing Infrastructure

### 10.1 Set up Vitest + React Testing Library

**Problem:** The `tests/` directory is empty. No test runner, no test framework, no test scripts.

**Steps:**

1. Install dependencies:

   ```bash
   npm install -D vitest @testing-library/react @testing-library/jest-dom @testing-library/user-event jsdom
   ```

2. **Update `vite.config.ts`:**

   ```ts
   /// <reference types="vitest/config" />
   export default defineConfig({
     // ... existing config
     test: {
       globals: true,
       environment: "jsdom",
       setupFiles: "./tests/setup.ts",
       css: true,
     },
   });
   ```

3. **New file:** `tests/setup.ts`

   ```ts
   import "@testing-library/jest-dom/vitest";
   ```

4. **Add to `package.json` scripts:**
   ```json
   "test": "vitest",
   "test:run": "vitest run",
   "test:coverage": "vitest run --coverage"
   ```

### 10.2 Priority test targets

Write tests for these first (highest risk-to-effort ratio):

1. **Route guards:** `ProtectedRoute` and `GuestRoute` — test redirect behavior based on auth state.
2. **Auth store:** `login()` saves to localStorage, `logout()` clears, hydration from localStorage works.
3. **API interceptor:** 401 triggers logout, token is attached to requests.
4. **Form validation:** Login and register Zod schemas reject invalid input.
5. **Org store:** `setActiveOrg` updates state, `subscribe` auto-fetches on login.

---

## 11. File-by-File Change Map

Summary of every file that needs modification and what changes apply:

| File                                     | Changes                                                                                                                     |
| ---------------------------------------- | --------------------------------------------------------------------------------------------------------------------------- |
| `src/services/api.ts`                    | Fix 401 redirect (1.1, 1.2), add token refresh (2.2), add `withCredentials` if using cookies (2.1)                          |
| `src/lib/auth.ts`                        | Validate with Zod (2.3), remove token functions if using cookies (2.1)                                                      |
| `src/store/auth-store.ts`                | Remove token from state if using cookies (2.1), add `sessionExpired` flag (1.2)                                             |
| `src/store/org-store.ts`                 | Slim down to client-only state (4.4), fix selector usage, remove `subscribe` side effect                                    |
| `src/services/auth.ts`                   | Unify pattern (7.1), implement refresh or remove (2.2), rename export (7.4), fix import paths (7.2)                         |
| `src/services/organization.ts`           | Fix import paths (7.2)                                                                                                      |
| `src/services/project.ts`                | Fix query string (7.3), unify pattern (7.1), fix import paths (7.2)                                                         |
| `src/types/organization.ts`              | Fix `Record<string, any>` (2.4), import `OrgRole` from `lib/roles.ts` (6.2)                                                 |
| `src/App.tsx`                            | Add lazy imports (5.1), add 404 route (1.3)                                                                                 |
| `src/main.tsx`                           | Add `ErrorBoundary` (3.1), add `QueryClientProvider` (4.1)                                                                  |
| `src/components/layout/AppLayout.tsx`    | Add `Suspense` boundary (5.1), add skip link (9.4), add focus management (9.2)                                              |
| `src/components/layout/AppSidebar.tsx`   | Fix Zustand selector (5.2), use `canManageMembers()` (6.2)                                                                  |
| `src/components/layout/NavUser.tsx`      | Extract `getInitials` to utils (8.3)                                                                                        |
| `src/components/layout/OrgSwitcher.tsx`  | Fix Zustand selectors (5.2)                                                                                                 |
| `src/pages/auth/LoginPage.tsx`           | Use `AuthLayout` (8.1), use `getErrorMessage` (8.2), fix bg color (9.1)                                                     |
| `src/pages/auth/RegisterPage.tsx`        | Use `AuthLayout` (8.1), use `getErrorMessage` (8.2), fix bg color (9.1)                                                     |
| `src/pages/ProjectsPage.tsx`             | Use `useProjects()` hook (4.3), fix Zustand selector (5.2), remove manual fetch                                             |
| `src/pages/settings/OrgSettingsPage.tsx` | Remove org guard (6.3), fix Zustand selector (5.2)                                                                          |
| `src/pages/settings/OrgMembersPage.tsx`  | Decompose (6.1), use `useOrgMembers()` (4.3), fix Zustand selector (5.2), remove org guard (6.3), add clipboard toast (9.3) |
| `vite.config.ts`                         | Add Vitest config (10.1)                                                                                                    |
| `package.json`                           | Add test scripts (10.1), add TanStack Query (4.1), add Vitest deps (10.1)                                                   |

### New files to create

| File                                                    | Purpose                                           | Section |
| ------------------------------------------------------- | ------------------------------------------------- | ------- |
| `src/components/ErrorBoundary.tsx`                      | Top-level error boundary                          | 3.1     |
| `src/components/PageLoader.tsx`                         | Suspense fallback for lazy routes                 | 5.1     |
| `src/components/RequireOrg.tsx`                         | Org guard wrapper                                 | 6.3     |
| `src/components/auth/AuthLayout.tsx`                    | Shared auth page layout                           | 8.1     |
| `src/pages/NotFoundPage.tsx`                            | 404 page                                          | 1.3     |
| `src/lib/query-client.ts`                               | TanStack Query client config                      | 4.1     |
| `src/lib/roles.ts`                                      | Centralized role constants and permission helpers | 6.2     |
| `src/lib/errors.ts`                                     | Shared error message extraction                   | 8.2     |
| `src/hooks/use-projects.ts`                             | TanStack Query hooks for projects                 | 4.2     |
| `src/hooks/use-organizations.ts`                        | TanStack Query hooks for orgs and members         | 4.2     |
| `src/pages/settings/_components/MembersTable.tsx`       | Members table sub-component                       | 6.1     |
| `src/pages/settings/_components/InviteMemberDialog.tsx` | Invite dialog sub-component                       | 6.1     |
| `src/pages/settings/_components/UpdateRoleDialog.tsx`   | Role change dialog sub-component                  | 6.1     |
| `src/pages/settings/_components/RemoveMemberAlert.tsx`  | Remove confirmation sub-component                 | 6.1     |
| `tests/setup.ts`                                        | Vitest + RTL setup                                | 10.1    |

---

## Implementation Order

Recommended sequence to minimize merge conflicts and maximize incremental value:

1. **Phase 1 — Critical fixes** (sections 1.1, 1.2, 1.3, 3.1)
   - Fix the 401 redirect, add 404 route, add ErrorBoundary
   - Zero risk, immediate value

2. **Phase 2 — Code quality** (sections 5.2, 7.1–7.4, 8.2, 8.3, 9.1)
   - Fix Zustand selectors, unify service patterns, fix imports, extract utilities
   - Low risk, improves DX immediately

3. **Phase 3 — Performance** (section 5.1)
   - Add React.lazy code splitting
   - Low risk, measurable bundle size improvement

4. **Phase 4 — Data layer** (sections 4.1–4.7)
   - Install TanStack Query, create hooks, slim Zustand stores
   - Medium risk (largest refactor), highest long-term value

5. **Phase 5 — Component architecture** (sections 6.1–6.3, 8.1)
   - Decompose god components, extract shared layouts
   - Low risk, improves maintainability

6. **Phase 6 — Security** (sections 2.1–2.4)
   - Token storage migration (requires backend work), Zod validation
   - Medium risk, requires backend coordination

7. **Phase 7 — Testing** (sections 10.1–10.2)
   - Set up Vitest, write priority tests
   - Zero risk, ongoing effort

8. **Phase 8 — Accessibility** (sections 9.2–9.4)
   - Focus management, skip links, aria-live regions
   - Zero risk, improves compliance
