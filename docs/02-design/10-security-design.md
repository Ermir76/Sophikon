# Security Design

**Version:** 1.0
**Date:** 2026-02-06

---

## Authentication

**Passwords** — hashed with bcrypt. Never stored or logged in plain text.

**Access token** — JWT, `HS256`, claims: `sub`, `exp`, `iat`, `type=access`. Short-lived.

**Refresh token** — opaque random token (`secrets.token_hex(32)`). DB stores only its SHA-256 hash. On refresh, the token rotates and the previous one is revoked. If a rotated token is reused, all active tokens for that user are revoked immediately.

---

## Token Transport

Both tokens travel as HttpOnly cookies (`SameSite=Lax`, `secure` in production):

- Access token: path `/api`
- Refresh token: path `/api/v1/auth`

API auth also accepts an OAuth2 bearer header as fallback. WebSocket auth accepts token from query param, cookie, or `Authorization` header.

---

## Authorization

All endpoints require authentication. Authorization is enforced at the dependency layer, never in service logic.

| Scope        | Dependency                | Roles                                  |
| ------------ | ------------------------- | -------------------------------------- |
| User         | `get_current_active_user` | active/inactive check                  |
| Project      | `get_project_or_404`      | `owner`, `manager`, `member`, `viewer` |
| Organization | `get_org_access_or_404`   | `owner`, `admin`, `member`             |

---

## Rate Limiting

SlowAPI with Redis backend. Global default: `60/minute`. Auth and profile endpoints have stricter per-endpoint limits. Exceeded limits return `429` with `RATE_LIMIT_EXCEEDED`.

CSRF: no explicit token — mitigated by `SameSite=Lax`, path-scoped cookies, and authenticated deps on all state-changing endpoints.

---

## Additional Controls

- **OAuth** — signed state token with nonce and expiry, constant-time comparison, redirect paths normalized to local-relative only
- **Account enumeration** — password reset returns generic success for unknown emails
- **File uploads** — MIME allowlist, strict size limits, private storage path, directory traversal prevention
- **Error responses** — stack traces logged server-side only, clients receive generic `INTERNAL_ERROR`
