# ADR-009: Pass Invitation Details via Route State for Review Page

- Status: [CONFIRMED]
- Date: 2026-03-25

## Context

The project invitation accept page (`ProjectInvitationAcceptPage`) serves two entry points: email links (`?token=xxx`) and in-app notification buttons (`?invitation_id=xxx`). The page currently auto-accepts on mount and shows no invitation details (project name, role, inviter, message) — making the "Review" button on notifications useless.

To support a proper review-before-accept flow, the page needs invitation details. Two options were considered:

- **Option A (Route State):** Pass invitation data from the notification dropdown via React Router `state` when navigating. No backend changes. Data is lost on page refresh.
- **Option B (GET Endpoint):** Add a `GET /api/v1/projects/members/invitations/{id}` endpoint to fetch invitation details by token or invitation_id. Works for all entry points including email. Requires backend work.

## Decision

**Option A — Route State.** The notification dropdown already has the invitation data (project name, role, inviter, message) from the notification record. Passing it via route state is zero backend work and covers the primary use case (in-app review).

For email links, where no route state exists, the page falls back to a minimal view showing only the accept action — acceptable because the email body itself contains the invitation context.

## Consequences

- **Pro:** No backend changes. Immediate fix for the broken "Review" UX.
- **Pro:** Keeps the accept page stateless from the backend's perspective.
- **Con:** Page refresh or direct URL navigation loses the invitation details — falls back to minimal view.
- **Con:** Email link flow cannot show the invitation message (email template also doesn't include it today).
- **Future:** A GET endpoint for invitation details (Option B) should be added when the email flow is enhanced to also show a review page. Tracked in `docs/ROADMAP.md` under Considered.
