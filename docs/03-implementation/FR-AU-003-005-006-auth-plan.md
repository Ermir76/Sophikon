# FR-AU-003/005/006 Authentication Expansion Plan

- **Created**: 2026-03-12
- **Status**: Planned
- **Scope**: Backend + Frontend
- **Requirements**:
  - `FR-AU-003` Login with Google OAuth (Must)
  - `FR-AU-005` Password reset via email (Should)
  - `FR-AU-006` Update profile (Should)

## Summary

Implement missing authentication/user-account capabilities without changing existing cookie-based auth behavior:

- Add Google OAuth login entry and callback flow.
- Add password-reset request + confirm flow using existing `password_reset` table.
- Add authenticated profile update endpoint and frontend form.

All new flows stay under mounted API prefix `/api/v1`.

## Current Baseline (Already in Code)

- Auth routes exist for register/login/refresh/logout/me/verify-email in `backend/app/api/v1/endpoints/auth.py`.
- `User` model already supports OAuth (`oauth_provider`, `oauth_id`) in `backend/app/models/user.py`.
- `PasswordReset` model already exists in `backend/app/models/password_reset.py`.
- Frontend auth service/pages do not yet include OAuth, password reset, or profile update actions.

## Final Decisions

| Area                            | Decision                                                                                                                                     |
| ------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------- |
| Auth session model              | Keep current cookie model (`access_token` + `refresh_token` httpOnly cookies).                                                               |
| OAuth flow                      | OAuth2 Authorization Code flow with backend callback and cookie issuance.                                                                    |
| OAuth account linking           | If Google email matches an existing local user, link account if local account has no conflicting oauth link; otherwise fail with safe error. |
| Password reset response privacy | Request endpoint always returns generic success message to prevent email enumeration.                                                        |
| Password reset token            | Random token sent by email, only SHA-256 hash stored in DB, single-use, expires in 1 hour.                                                   |
| Profile update endpoint         | `PATCH /api/v1/users/me` for `full_name`, `avatar_url`, `timezone`, `locale` (no email/password change in this slice).                       |
| Rate limiting                   | Add strict limiter rules on OAuth start/callback and password-reset endpoints.                                                               |

## Target API Surface

### FR-AU-003 Google OAuth

- `GET /api/v1/auth/oauth/google`
  - Generates `state` (+ nonce), stores signed state in short-lived cookie, redirects to Google consent page.
- `GET /api/v1/auth/oauth/google/callback`
  - Validates `state`, exchanges code for Google tokens, verifies Google identity, resolves/creates user, issues app cookies, redirects to frontend.

### FR-AU-005 Password Reset

- `POST /api/v1/auth/password-reset`
  - Body: `{ "email": "user@example.com" }`
  - Always returns `{ "message": "If the email exists, reset instructions were sent." }`
- `POST /api/v1/auth/password-reset/confirm`
  - Body: `{ "token": "...", "new_password": "..." }`
  - Validates token, password policy, rotates password hash, revokes active refresh tokens, marks reset token used.

### FR-AU-006 Update Profile

- `PATCH /api/v1/users/me`
  - Auth required.
  - Body (partial): `{ "full_name"?, "avatar_url"?, "timezone"?, "locale"? }`
  - Returns updated `UserResponse`.

## Implementation Slices

### Slice 1: Backend Foundation

- Config additions in `backend/app/core/config.py`:
  - `GOOGLE_CLIENT_ID`
  - `GOOGLE_CLIENT_SECRET`
  - `GOOGLE_REDIRECT_URI`
- Add auth schema models in `backend/app/schema/auth.py`:
  - `PasswordResetRequest`
  - `PasswordResetConfirmRequest`
  - `UpdateProfileRequest` (or in `schema/user.py` if preferred)
- Add helper utilities:
  - secure `state` generation/validation for OAuth callback
  - generic token email utility for password-reset messages

### Slice 2: FR-AU-003 Backend (Google OAuth)

- Add OAuth endpoints in `backend/app/api/v1/endpoints/auth.py`.
- Add/extend service logic in `backend/app/service/auth_service.py`:
  - find/create user by Google identity
  - link by email with conflict checks
  - issue access/refresh token pair via existing `_create_token_pair`
- Add provider integration helper:
  - either direct Google token+userinfo calls with `httpx`
  - or introduce `authlib` and keep provider-specific code isolated.
- Ensure callback failures redirect to frontend with error status (no raw provider errors leaked).

### Slice 3: FR-AU-005 Backend (Password Reset)

- Add service functions in `auth_service.py` (or split to `password_reset_service.py`):
  - `request_password_reset(email)`
  - `confirm_password_reset(token, new_password)`
- Reuse existing `PasswordReset` model:
  - hash token before storage/lookup
  - invalidate older unused tokens for same user when generating new one
  - set `used_at` on successful confirm
- Send reset email via `email_service.py` with frontend reset link.
- Revoke existing refresh tokens after password change.

### Slice 4: FR-AU-006 Backend (Profile Update)

- Add `backend/app/api/v1/endpoints/users.py` with `PATCH /users/me`.
- Add service function in `auth_service.py` or `user_service.py`:
  - partial update on allowed profile fields only.
- Validate:
  - `full_name` length
  - `avatar_url` URL/length
  - timezone/locale formats (basic validation now, stricter list later if needed).

### Slice 5: Frontend

- `frontend/src/features/auth/api/auth.service.ts`:
  - `startGoogleOAuth()` (window redirect to backend start endpoint)
  - `requestPasswordReset(email)`
  - `confirmPasswordReset(token, new_password)`
  - `updateProfile(patch)`
- Add pages/components:
  - Login: “Continue with Google” button
  - Password reset request page
  - Password reset confirm page (token from URL)
  - Profile settings page/form (or in existing settings surface)
- Route additions in `frontend/src/app/App.tsx`:
  - public reset routes
  - protected profile route

### Slice 6: Tests

- Backend API tests (`backend/tests/unit/api/v1/`):
  - OAuth start redirect and callback success/failure
  - password-reset request generic response and confirm semantics
  - `PATCH /users/me` auth + validation + partial update
- Backend service tests (`backend/tests/unit/service/`):
  - OAuth identity resolution/linking conflict cases
  - reset token single-use + expiry + refresh-token revocation
  - profile update field allowlist
- Frontend tests:
  - auth service methods
  - login page OAuth button behavior
  - reset and profile forms submit/error/success states

### Slice 7: Docs + Traceability

- Update `docs/03-implementation/requirements-traceability.md` statuses for FR-AU-003/005/006 after code lands.
- Update `docs/01-requirements/functional-requirements.md` status icons for completed items.
- Add release note entry in docs changelog/implementation log for new auth capabilities.

## Security and Risk Controls

- Add rate limits:
  - OAuth start/callback: conservative burst limits.
  - Password-reset request/confirm: strict limits by IP and optionally by email fingerprint.
- Use constant-time token hash comparisons where applicable.
- Never expose whether an email exists in password-reset request response.
- Revoke existing sessions after password reset.
- Log auth events with safe metadata (no tokens, no secrets).

## Acceptance Criteria

### FR-AU-003

- User can authenticate with Google and receives normal app auth cookies.
- Existing account linking is deterministic and conflict-safe.
- Callback failure paths return user-safe error outcome (frontend redirect + status).

### FR-AU-005

- User can request reset email without account enumeration leakage.
- Valid token resets password once; reused/expired token is rejected.
- Old refresh tokens are revoked after successful reset.

### FR-AU-006

- Authenticated user can update allowed profile fields via `PATCH /users/me`.
- Unauthorized request returns `401`.
- Validation errors return `422` with stable shape.

## Suggested Delivery Order

1. FR-AU-006 (smallest, fastest confidence win)
2. FR-AU-005 (uses existing DB model, medium complexity)
3. FR-AU-003 (external provider integration and callback handling)

## Out of Scope (This Plan)

- Session management UI/API (`FR-AU-008`)
- Email change workflow with re-verification
- Password change while logged in (current password challenge)
- Multi-provider OAuth (GitHub, Microsoft, etc.)
