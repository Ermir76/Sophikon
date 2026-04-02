# Authentication

Status: `Failed Audit`
Owner: `wwwer`
Severity summary: `P0: 1 | P1: 2 | P2: 0`

## Review State Legend

- `PASS`: reviewed and acceptable
- `FAIL`: reviewed and not acceptable
- `NOT CHECKED`: not reviewed yet
- `BLOCKED`: could not be signed off because another issue prevented meaningful verification

## Boundary Notes

Auth covers the guest-entry and session-trust surface: `/login`, `/register`, `/verify-email`, `/forgot-password`, `/reset-password`, Google OAuth start/callback, auth bootstrap in `App.tsx`, protected/guest route gating, refresh rotation, and logout from the app shell.

It does not include profile/settings edits beyond the auth/session dependencies those screens rely on.

## Critical User Promises

- A valid user can register, sign in, and reach the right destination.
- A valid session survives normal refresh/idle rotation when refresh cookies are still valid.
- Guests are kept out of protected routes and authenticated users are kept out of guest routes.
- Reset and verification links fail safely and give the user a real recovery path.

## Review Matrix

### Scope

| Item | State | Evidence / Notes |
| --- | --- | --- |
| `/login` is in scope | `PASS` | Page, hooks, and tests reviewed. |
| `/register` is in scope | `PASS` | Page, hooks, backend endpoint, and service reviewed. |
| `/verify-email` is in scope | `PASS` | Frontend page plus backend redirect flow reviewed. |
| `/forgot-password` is in scope | `PASS` | Frontend page plus backend request flow reviewed. |
| `/reset-password` is in scope | `PASS` | Frontend page plus backend confirm flow reviewed. |
| Session bootstrap and refresh flow are in scope | `PASS` | `App.tsx`, auth store, and axios refresh interceptor traced. |
| Logout flow is in scope | `PASS` | `NavUser`, auth store logout, and backend logout endpoint reviewed. |
| Google OAuth flow is in scope | `PASS` | Frontend CTA and backend start/callback flow reviewed. |

### Entry Points

| Item | State | Evidence / Notes |
| --- | --- | --- |
| Login form entry | `PASS` | `LoginPage.tsx` reviewed. |
| Register form entry | `PASS` | `RegisterPage.tsx` reviewed. |
| Google OAuth button | `PASS` | CTA reviewed in `LoginPage.tsx`; backend callback traced. |
| Email verification links | `PASS` | `/auth/verify-email` redirect and frontend status handling reviewed. |
| Password reset links | `PASS` | Reset request + confirm link contract traced. |
| Logout action from app shell | `PASS` | `NavUser.tsx` and `auth-store.ts` reviewed. |

### Happy Path

| Item | State | Evidence / Notes |
| --- | --- | --- |
| Register new user successfully | `PASS` | Backend coverage is strong in `backend/tests/unit/service/test_auth_service.py` and `backend/tests/unit/api/v1/test_auth.py`. |
| Verify email successfully | `PASS` | Backend verification flow has dedicated tests in `backend/tests/unit/api/v1/test_email_verification.py`. |
| Login with valid credentials | `PASS` | Backend service coverage exists; frontend form/hook flow reviewed. |
| Logout cleanly | `PASS` | Store clears auth and backend logout is idempotent; reviewed in `auth-store.ts` and service tests. |
| Session remains valid on refresh | `FAIL` | Blocked by `AUTH-001`: bootstrap uses `/auth/me` and clears auth instead of recovering through refresh. |
| Silent refresh works after idle period | `PASS` | Proactive interval refresh path exists in `App.tsx` and has focused frontend test coverage in `App.test.tsx`. |
| Google OAuth login lands in correct destination | `PASS` | Backend callback protects `next` and redirects safely; covered in backend API tests. |

### Validation And Failure Paths

| Item | State | Evidence / Notes |
| --- | --- | --- |
| Empty login form | `PASS` | Zod + form validation in `LoginPage.tsx`. |
| Wrong password | `PASS` | Backend rejects invalid credentials; service tests cover this. |
| Unknown email | `PASS` | Backend login rejects and reset request remains enumeration-safe. |
| Duplicate registration email | `PASS` | Backend service tests cover duplicate rejection. |
| Expired verification link | `PASS` | Backend verification tests cover expired token behavior. |
| Invalid reset token | `PASS` | Explicit invalid-token UI in `ResetPasswordPage.tsx`; basic frontend test exists. |
| Password change with wrong current password | `PASS` | Backend API and service tests cover rejection. |
| OAuth error path returns user to a clear recovery state | `PASS` | Backend redirects to `/login?oauth=error`; page shows a clear error banner. |

### Empty, Loading, And Refresh States

| Item | State | Evidence / Notes |
| --- | --- | --- |
| Loading state during auth bootstrap is acceptable | `PASS` | `ProtectedRoute` and `GuestRoute` show loading while initialization is pending. |
| Login/register submit pending state is clear | `PASS` | Submit buttons show pending labels/spinner. |
| Password reset request pending/success state is clear | `PASS` | `ForgotPasswordPage.tsx` shows spinner and success alert. |
| Verification page handles missing/invalid token clearly | `FAIL` | Error state copy exists, but the CTA is misleading; see `AUTH-003`. |

### Permissions And Roles

| Item | State | Evidence / Notes |
| --- | --- | --- |
| Protected routes reject unauthenticated users | `PASS` | Verified in `ProtectedRoute.tsx` and `ProtectedRoute.test.tsx`. |
| Guest routes redirect authenticated users away | `PASS` | Route logic reviewed in `GuestRoute.tsx`; no dedicated test yet. |
| Deactivated user behavior is clear | `BLOCKED` | Backend denies inactive users correctly, but the user-facing frontend experience was not fully traced end-to-end in this audit. |

### UX And Visual Review

| Item | State | Evidence / Notes |
| --- | --- | --- |
| Forms are readable and confidence-inspiring | `PASS` | Auth layout and form structure are generally solid. |
| Errors are understandable | `PASS` | Error alerts consistently use `getErrorMessage(error)`. |
| Success feedback is visible | `FAIL` | Verification recovery state is weak, and some happy-path feedback still needs explicit review. |
| No developer-speak leaks into auth screens | `NOT CHECKED` | Not fully audited line-by-line yet. |
| Auth pages feel credible in a demo | `BLOCKED` | `AUTH-002` and `AUTH-003` reduce demo trust until fixed. |

### Responsive Review

| Item | State | Evidence / Notes |
| --- | --- | --- |
| Auth screens checked on desktop | `NOT CHECKED` | No explicit responsive pass was done in this audit. |
| Auth screens checked on mobile | `NOT CHECKED` | No explicit responsive pass was done in this audit. |
| Form width, spacing, and keyboard flow feel reasonable | `NOT CHECKED` | Needs manual UI verification. |

### Test Coverage

| Item | State | Evidence / Notes |
| --- | --- | --- |
| Session bootstrap test coverage reviewed | `PASS` | `App.test.tsx` and `auth-store.test.ts` reviewed. |
| Login/register/reset/refresh test gaps listed | `PASS` | Main gap is expired-access + valid-refresh bootstrap on first load. |
| ProtectedRoute and GuestRoute behavior reviewed | `PASS` | Logic reviewed; `ProtectedRoute` has focused test, `GuestRoute` still lacks dedicated test evidence. |

## Issues Found

| ID | Severity | Area | Problem | Expected | Notes |
| --- | --- | --- | --- | --- | --- |
| AUTH-001 | P0 | Session bootstrap / refresh | A browser refresh after the access token expires logs the user out instead of restoring the session from the valid refresh cookie. `checkSession()` calls `/auth/me`, `/auth/me` is explicitly excluded from interceptor-driven refresh, and the store clears auth on any failure. | App bootstrap should recover with `/auth/refresh` when the refresh cookie is still valid, so session trust survives reloads and idle periods. | Traced through `frontend/src/app/App.tsx`, `frontend/src/features/auth/store/auth-store.ts`, and `frontend/src/shared/api/api.ts`. Existing frontend tests cover `checkSession` success/failure and proactive refresh, but not the expired-access + valid-refresh bootstrap case. |
| AUTH-002 | P1 | Login UX | The `Keep me logged in` checkbox is a dead control. It is rendered in the login form but is not wired to any state, request payload, cookie policy, or storage behavior. | Either implement a real persistence policy tied to this control or remove it so the screen does not make a false promise. | Found in `frontend/src/features/auth/pages/LoginPage.tsx`. |
| AUTH-003 | P1 | Verification recovery UX | The verification failure and invalid-link states tell the user to request or check email again, but the only CTA is `Go to Dashboard`, which sends guests into protected-route redirect instead of a direct recovery action. | Error states should offer a clear recovery path such as login or resend-verification entry, not a misleading dashboard CTA. | Found in `frontend/src/features/auth/pages/VerifyEmailPage.tsx`. |

## Re-Review

| Item | State | Evidence / Notes |
| --- | --- | --- |
| Register flow retested | `NOT CHECKED` | Pending fixes first. |
| Login flow retested | `NOT CHECKED` | Pending fixes first. |
| Logout flow retested | `NOT CHECKED` | Pending fixes first. |
| Password reset retested | `NOT CHECKED` | Pending fixes first. |
| Google OAuth retested | `NOT CHECKED` | Pending fixes first. |
| Silent refresh retested | `NOT CHECKED` | Pending fix for bootstrap refresh trust gap first. |

## Closure Gate

| Item | State | Evidence / Notes |
| --- | --- | --- |
| Core auth flows work without hesitation or confusion | `FAIL` | `AUTH-001`, `AUTH-002`, and `AUTH-003` prevent sign-off. |
| No open `P0` auth issues remain | `FAIL` | `AUTH-001` is still open. |
| Protected route behavior is trustworthy | `PASS` | Reviewed and supported by focused test coverage. |
| Session persistence and refresh are verified | `FAIL` | Bootstrap refresh trust is broken by `AUTH-001`. |
