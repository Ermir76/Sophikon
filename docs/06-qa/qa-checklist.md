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

## 3. Project Management

### Create project (FR-PM-001, US-1.1)

- [x] ✅ Go to the projects page — does it load without errors?
- [x] ✅ Click "Create project" — does the dialog open?
- [x] ⚠️ Fill in name + description and submit — does the project appear in the list? NOTE: The date at the dialog card it is fats at 5 March, should not that date follows current day?
- [x] ✅ Submit with empty name — does it show a validation error?
- [x] ✅ Create a second project — does it appear alongside the first?

### List projects (FR-PM-004)

- [x] ✅ Do all your projects show up on the projects page?
- [x] ✅ Switch org — does the list update to show only that org's projects?
- [x] ✅ Are projects displayed in both grid and table views? Can you toggle between them?

### Project dashboard / overview (FR-PM-005, US-1.4)

- [x] ✅ Click into a project — does the overview/dashboard page load?
- [x] ✅ Are there any visible stats, metrics, or summary cards?
- [x] ✅ Does the activity feed show recent actions?
- [x] ✅ Reload the page — does everything persist?

### Edit project (FR-PM-002)

- [x] ✅ Go to project settings — does the page load?
- [x] ✅ Change the project name — does it save and persist after reload?
- [x] ✅ Change the project description — does it save?
- [x] ✅ Clear the name and try to save — does it validate?

### Delete project (FR-PM-003)

- [x] ✅ Delete a project from settings — does it disappear from the list?
- [x] ✅ After deleting, navigate to its URL directly — does it show 404 or redirect?

### Set project status (FR-PM-006 — PARTIAL, skip)

> ⏭️ Marked PARTIAL in FRs — not fully surfaced in UI. Not testable yet.

### Set default calendar (FR-PM-008 — PARTIAL, skip)

> ⏭️ Marked PARTIAL in FRs — not fully surfaced in UI. Not testable yet.

### Project members (NFR-DAT-003)

- [ ] Go to the project's Members tab — does the member list load?
- [x] ⚠️ Invite a member to the project — does it work? NOTE: Accept succeeded server-side but UI stays stuck on "Accepting invitation..." — never shows success state
- [x] ⚠️ Accept invite auto-adds user to org, but org switcher doesn't update — needs manual page refresh
- [x] ✅ Change a member's project role — does it save?
- [x] ✅ Remove a member — do they disappear?
- [x] ⚠️ As a non-member, try to access the project URL — are you blocked? NOTE : IT IS AS ERROR, should be clear that it is not part of that project anymore

### Activity feed (NFR-OBS-001)

- [x] ✅ Make a change inside the project — does it appear in the activity feed?
- [x] ✅ Is the feed showing the right user, timestamp, and action?

### Realtime updates (NFR-PERF-004)

- [x] ✅ Open the project in two browser tabs — make a change in one. Does the other tab update without refresh? NOTE: Fixed by adding ws:true to Vite proxy (#39). Works for in-project changes (tasks, comments). Org-level changes (new project) not covered — project WS is project-scoped.

---

## 4. Collaboration & RBAC

### RBAC — Viewer role (FR-CO-002, NFR-SEC-002)

- [ ] As a viewer, can you see the task list and Gantt? (should work)
- [ ] As a viewer, try to create a task — are you blocked?
- [ ] As a viewer, try to edit a task — are you blocked?
- [ ] As a viewer, try to add a comment — are you blocked?
- [ ] As a viewer, try to upload an attachment — are you blocked?
- [ ] As a viewer, try to create a dependency — are you blocked?
- [ ] As a viewer, can you view AI estimates/conversations? (should work)
- [ ] Does the UI hide buttons/actions the viewer can't perform, or do they only get errors after clicking?

### RBAC — Member role (FR-CO-002, NFR-SEC-002)

- [ ] As a member, can you create/edit tasks? (should work)
- [ ] As a member, can you add comments and @mention others? (should work)
- [ ] As a member, can you upload/delete attachments? (should work)
- [ ] As a member, try to create a dependency — are you blocked? (owner/manager only)
- [ ] As a member, try to delete a task — are you blocked? (owner/manager only)
- [ ] As a member, try to manage calendars — are you blocked? (owner/manager only)
- [ ] As a member, try to invite someone to the project — are you blocked? (owner/manager only)

### RBAC — Manager role (FR-CO-002, NFR-SEC-002)

- [ ] As a manager, can you invite members with role member or viewer? (should work)
- [ ] As a manager, try to invite someone as owner — are you blocked?
- [ ] As a manager, can you remove a member/viewer? (should work)
- [ ] As a manager, try to remove an owner — are you blocked?
- [ ] As a manager, try to change someone's role — are you blocked? (owner only)
- [ ] As a manager, can you create/manage dependencies? (should work)
- [ ] As a manager, can you manage calendars and resources? (should work)

### RBAC — Owner role (FR-CO-002, NFR-SEC-002)

- [ ] As an owner, can you change any member's role? (should work)
- [ ] As an owner, can you invite with any role including owner? (should work)
- [ ] As an owner, can you delete the project? (should work, owner only)

### Comments on tasks (FR-CO-008, US-6.3)

- [ ] Open a task detail — is there a comments section?
- [ ] Write a comment and submit — does it appear?
- [ ] Edit your own comment — does it save?
- [ ] Delete your own comment — does it disappear?
- [ ] Can you reply to a comment (threaded)? Does the thread render correctly?
- [ ] As a different user, try to edit/delete someone else's comment — are you blocked? (owner/manager can, others can't)

### @mentions (FR-CO-009, US-6.3)

- [ ] In a comment, type @ — does an autocomplete list appear with project members?
- [ ] Select a member — does the mention render as a highlighted name?
- [ ] Submit the comment — does the mentioned user receive a notification?

### File attachments (FR-CO-010)

- [ ] On a task, is there an attachments section?
- [ ] Upload a file — does it appear in the list?
- [ ] Download the attachment — does it work?
- [ ] Delete the attachment — does it disappear?
- [ ] Try uploading a very large file — does it show a size limit error?

### Notifications (FR-CO-011, FR-CO-012)

- [ ] Is there a notification bell/icon in the header?
- [ ] Trigger a notification (e.g., someone comments on your task) — does it appear?
- [ ] Click the notification — does it navigate to the right place?
- [ ] Mark a notification as read — does it update?
- [ ] Go to notification settings — can you toggle which notifications you receive?
- [ ] Change a setting and save — does it persist after reload?

### Presence (FR-CO-006)

- [ ] Open the same project in two sessions (different users) — does each user see the other as online/active?
- [ ] Is there any indicator showing who is currently viewing or editing?

### Activity log (FR-CO-007)

- [ ] Perform various actions (create task, add comment, invite member) — do they all appear in the activity log?
- [ ] Is each entry showing the correct user, action type, and timestamp?

---
