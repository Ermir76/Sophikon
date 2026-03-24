# QA Checklist

Manual verification pass — check every domain against the running app.

**Legend:** ✅ Works | ⚠️ Works but incomplete/rough | ❌ Broken or missing

---

## Domains

1. Authentication & User Management
2. Organizations & Multi-tenancy
3. Project Management
4. Collaboration & RBAC
5. Task Management
6. Gantt
7. Kanban
8. Resources & Calendars
9. AI Features

---

## 1. Authentication & User Management

### Registration (FR-AU-001, US-13.1, US-13.2)

- [x] ✅ Go to `/register` — does the form load?
- [x] ✅ Register with a new email and password — does it succeed?
- [x] ✅ Check your inbox — did the verification email arrive?
- [x] ✅ Click the verification link — does it confirm the account?
- [x] ✅ Try to register again with the same email — does it show an error?
- [x] ✅ Submit with empty fields — does it show validation errors?

### Login (FR-AU-002)

- [x] ✅ Go to `/login` — does the form load?
- [x] ✅ Enter correct credentials — does it log you in and redirect?
- [x] ✅ Enter wrong password — does it show an error (not a crash)?
- [x] ✅ Enter an unregistered email — does it show an error?
- [x] ✅ Leave fields empty and submit — does it validate?

### Google OAuth (FR-AU-003)

- [x] ✅ Click "Login with Google" — does it redirect to Google?
- [x] ✅ Complete Google login — does it land you inside the app?

### Logout (FR-AU-004)

- [x] ✅ Click logout — are you redirected to `/login`?
- [x] ✅ Try to navigate back to a protected page — are you blocked?

### Session persistence (FR-AU-007)

- [x] ✅ Log in, close the browser tab, reopen the app — are you still logged in?
- [ ] ⏭️ Stay idle for a while, then try an action — does the session refresh silently without logging you out?

### Password reset (FR-AU-005)

- [x] ✅ Go to "Forgot password" — does the form exist?
- [x] ⚠️ Submit your email — do you receive a reset email? NOTE:I can reset with last password that i had before, should be allowed?
- [x] ✅ Click the link and set a new password — does it work?
- [x] ✅ Log in with the new password — does it succeed?

### Change password (FR-AU-011, US-13.3)

- [x] ✅ Go to Profile settings — is there a "Change password" section?
- [x] ✅ Enter current + new password — does it save? NOTE: Passoword changed successfully should be with radix?
- [x] ✅ Log out and log in with the new password — does it work?

### Profile update (FR-AU-006)

- [x] ✅ Go to Profile — can you edit your name?
- [x] ✅ Save — does it persist after a page reload?

### Avatar (FR-AU-012, US-10.1)

- [x] ✅ Upload a profile photo — does it appear? NOTE: Something went wrong
      Objects are not valid as a React child (found: object with keys {type, loc, msg, input}). If you meant to render a collection of children, use an array instead.
- [x] ✅ Remove the avatar — does it revert to initials/placeholder?

### Resend verification email (FR-AU-010)

- [x] ✅ With an unverified account, trigger "Resend verification" — does the email arrive?

### AI preferences (FR-AU-013, US-10.2)

- [x] ✅ Go to Profile → AI settings — does the section load?
- [x] ✅ Toggle an AI tool auto-approval on/off — does it save? NOTE: No confirmation that is saved, and also a stop icon pop over on the toggle for a millisecond

---

## 2. Organizations & Multi-tenancy

### Create & manage organization (FR-OR-001, FR-OR-002, FR-OR-003, US-9.1)

- [x] ✅ Open the org switcher — does your personal org appear?
- [x] ✅ Create a new organization — does it save and appear in the list?
- [x] ✅ Edit the organization name/settings — does it persist after reload?
- [x] ✅ Delete the organization — does it disappear?

### Org switcher (FR-OR-001, US-9.3)

- [x] ✅ If you have 2+ orgs — does the switcher let you switch between them?
- [x] ✅ After switching — does the app context update (projects, members)?

### Invite & manage members (FR-OR-006, FR-OR-007, FR-OR-008, US-9.2)

- [x] ✅ Go to org settings → Members — does the member list load?
- [x] ✅ Invite a new member by email — does the invite email arrive in Mailpit?
- [x] ✅ Change a member's role (admin ↔ member) — does it save? NOTE : Changing roles it gives some weird moving boxes
- [x] ✅ Remove a member — do they disappear from the list?

### Auto-created personal org on registration (ROADMAP)

- [x] ✅ Register a brand new account — is a personal org automatically created?
- [x] ✅ Does the new user land inside that org without any manual steps?

### Organization dashboard (FR-OR-010, US-9.4)

- [x] ✅ Go to the org dashboard — does it load without errors?
- [x] ✅ Are there any visible insights or metrics shown?

---
