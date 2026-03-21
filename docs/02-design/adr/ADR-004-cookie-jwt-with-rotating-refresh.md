# ADR-004: Cookie-Based JWT Access + Rotating Refresh Tokens

- Status: [CONFIRMED]
- Date: 2026-03-20

## Context

The platform needs browser-friendly auth with short-lived access credentials and revocable long-lived sessions.

## Decision

Use:
- JWT access token (short-lived) in HttpOnly cookie
- Opaque refresh token (DB-hashed) in HttpOnly cookie
- Rotation on refresh with reuse detection and token-family revocation

## Evidence

- Crypto/token helpers: `backend/app/core/security.py`
- Auth endpoints/cookie policy: `backend/app/api/v1/endpoints/auth.py`
- Refresh rotation/reuse handling: `backend/app/service/auth_service.py`
- Rate-limit integration: `backend/app/core/rate_limit.py`
- Git history signals:
  - `0c35d1f fix(security): harden auth, config validation, and API before deployment`
  - `d087568 feat(auth,e2e): ... configurable rate limits`

## Consequences

- Browser clients get automatic cookie-based session behavior.
- Stolen rotated refresh tokens can trigger family revocation.
- Backend must maintain refresh-token persistence and revocation metadata.
