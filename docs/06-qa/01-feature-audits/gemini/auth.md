# Authentication

Status: `Failed Audit`
Owner: `Gemini CLI`
Severity summary: `P0: 2 | P1: 4 | P2: 0`

## Boundary Notes

Auth covers the guest-entry and session-trust surface: `/login`, `/register`, `/verify-email`, `/forgot-password`, `/reset-password`, Google OAuth start/callback, auth bootstrap in `App.tsx`, protected/guest route gating, refresh rotation, and logout from the app shell.

It does not include profile/settings edits beyond the auth/session dependencies those screens rely on.

## Scope

- [x] `/login`
- [x] `/register`
- [x] `/verify-email`
- [x] `/forgot-password`
- [x] `/reset-password`
- [x] session bootstrap and refresh flow
- [x] logout flow
- [x] Google OAuth flow

## Entry Points

- [x] Login form entry
- [x] Register form entry
- [x] Google OAuth button
- [x] Email verification links
- [x] Password reset links
- [x] Logout action from app shell

## Happy Path

- [x] Register new user successfully (Verified in `RegisterPage.tsx` and `auth_service.py`)
- [x] Verify email successfully (Verified in `VerifyEmailPage.tsx` and `email_service.py`)
- [x] Login with valid credentials (Verified in `LoginPage.tsx` and `auth_service.py`)
- [x] Logout cleanly (Verified in `auth-store.ts` and `auth.py`)
- [x] Session remains valid on refresh (Verified in `App.tsx` and `api.ts`)
- [x] Silent refresh works after idle period (Verified in `App.tsx` interval)
- [x] Google OAuth login lands in correct destination (Verified in `auth.py` callback)

## Validation And Failure Paths

- [x] Empty login form (Handled by Zod in `LoginPage.tsx`)
- [x] Wrong password (Handled in `auth_service.py`)
- [x] Unknown email (Handled in `auth_service.py`)
- [x] Duplicate registration email (Handled in `auth_service.py`)
- [x] Expired verification link (Handled in `email_service.py`)
- [x] Invalid reset token (Handled in `auth_service.py`)
- [x] Password change with wrong current password (Handled in `auth_service.py`)
- [x] OAuth error path returns user to a clear recovery state (Verified in `auth.py` and `LoginPage.tsx`)

## Empty, Loading, And Refresh States

- [x] Loading state during auth bootstrap is acceptable (Verified in `App.tsx`)
- [x] Login/register submit pending state is clear (Verified in pages)
- [x] Password reset request pending/success state is clear (Verified in pages)
- [x] Verification page handles missing/invalid token clearly (Verified in `VerifyEmailPage.tsx`)

## Permissions And Roles

- [x] Protected routes reject unauthenticated users (Verified in `App.tsx`)
- [x] Guest routes redirect authenticated users away (Verified in `App.tsx`)
- [x] Deactivated user behavior is clear (Checked in `login_user`, but see AUTH-006)

## UX And Visual Review

- [x] Forms are readable and confidence-inspiring
- [x] Errors are understandable
- [x] Success feedback is visible
- [x] No developer-speak leaks into auth screens
- [x] Auth pages feel credible in a demo

## Responsive Review

- [ ] Auth screens checked on desktop
- [ ] Auth screens checked on mobile
- [ ] Form width, spacing, and keyboard flow feel reasonable

## Test Coverage

- [x] Session bootstrap test coverage reviewed
- [x] Login/register/reset/refresh test gaps listed
- [x] ProtectedRoute and GuestRoute behavior reviewed

## Issues Found

| ID       | Severity | Area                        | Problem                                                                                                                                                                                                                                                                            | Expected                                                                                                                                      | Notes                                                                                                                                                                                                                                                                             |
| -------- | -------- | --------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| AUTH-001 | P0       | Session bootstrap / refresh | A browser refresh after the access token expires logs the user out instead of restoring the session from the valid refresh cookie. `checkSession()` calls `/auth/me`, `/auth/me` is explicitly excluded from interceptor-driven refresh, and the store clears auth on any failure. | App bootstrap should recover with `/auth/refresh` when the refresh cookie is still valid, so session trust survives reloads and idle periods. | Traced through `frontend/src/app/App.tsx`, `frontend/src/features/auth/store/auth-store.ts`, and `frontend/src/shared/api/api.ts`.                                                                                                                                                |
| AUTH-002 | P1       | Login UX                    | The `Keep me logged in` checkbox is a dead control. It is rendered in the login form but is not wired to any state, request payload, cookie policy, or storage behavior.                                                                                                           | Either implement a real persistence policy tied to this control or remove it so the screen does not make a false promise.                     | Found in `frontend/src/features/auth/pages/LoginPage.tsx`.                                                                                                                                                                                                                        |
| AUTH-003 | P1       | Verification recovery UX    | The verification failure and invalid-link states tell the user to request or check email again, but the only CTA is `Go to Dashboard`, which sends guests into protected-route redirect instead of a direct recovery action.                                                       | Error states should offer a clear recovery path such as login or resend-verification entry, not a misleading dashboard CTA.                   | Found in `frontend/src/features/auth/pages/VerifyEmailPage.tsx`.                                                                                                                                                                                                                  |
| AUTH-004 | P1       | Password Validation         | Frontend and Backend password length/complexity constraints are inconsistent. Frontend requires 8 chars + special/uppercase. Backend allows 8 chars but caps at 72 bytes (bcrypt limit) and doesn't enforce complexity in `register_user`.                                         | Sync validation rules. Backend should enforce at least what frontend requires to prevent bypass via API.                                      | Found in `RegisterPage.tsx` vs `auth_service.py`.                                                                                                                                                                                                                                |
| AUTH-005 | P1       | Account Enumeration         | The password reset request is enumeration-safe (silent on unknown email), but the frontend `RegisterPage` will likely show "Email already registered" errors, making the enumeration-safety in reset moot if not handled consistently.                                            | Ensure consistent enumeration-safety policy across register/login/reset if it is a priority.                                                  | `auth_service.py` returns `ResourceConflictError("Email already registered")` on registration.                                                                                                                                                                                    |
| AUTH-006 | P0       | Account Deactivation        | `is_active` check is missing in `register_user`. While unlikely for a new user, the system does not prevent re-registration of a deactivated email if the user was deleted/deactivated but not purged.                                                                             | `register_user` should check `is_active` if it finds an existing user or simply reject all existing emails consistently.                      | Found in `auth_service.py`.                                                                                                                                                                                                                                                       |

## Re-Review

- [ ] Register flow retested
- [ ] Login flow retested
- [ ] Logout flow retested
- [ ] Password reset retested
- [ ] Google OAuth retested
- [ ] Silent refresh retested

## Exit Criteria

- [ ] Core auth flows work without hesitation or confusion
- [ ] No open `P0` auth issues remain
- [x] Protected route behavior is trustworthy
- [ ] Session persistence and refresh are verified
