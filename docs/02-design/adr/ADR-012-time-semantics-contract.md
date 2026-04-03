# ADR-012: Time Semantics Contract

**Date:** 2026-04-03
**Status:** Accepted

## Context

Sophikon has accumulated multiple time-related behaviors across backend services, frontend parsing, dashboards, scheduling, and the calendar module.

The main source of confusion is that the application currently mixes three different concepts:

1. **Exact moments in time**
   - Example: `created_at`, `updated_at`, notification timestamps, audit events
   - These represent one real instant in the world

2. **Calendar dates**
   - Example: task `start_date`, `finish_date`, dashboard trend day buckets, due dates
   - These represent a day on a business calendar, not a shared instant

3. **Work-calendar rules**
   - Example: working week definitions, holidays, working exceptions
   - These define when work is allowed; they are not meetings or events

Without an explicit contract, implementations drift:
- some code treats date-only values like UTC moments
- some code computes `today` using server-local date
- some code computes `today` using UTC date
- frontend bugs appear when date-only values are parsed as timestamps
- the current `calendar` feature can be misunderstood as a meeting/event calendar even though it is a work-calendar system

This ADR defines the time contract for the whole application.

## Decision

### 1. Exact Moments Use UTC Semantics

Any value representing one real instant in time must use UTC semantics end to end.

Examples:
- `created_at`
- `updated_at`
- activity feed timestamps
- notification timestamps
- websocket event timestamps
- future meeting/event `starts_at` / `ends_at`

Rules:
- Database stores these as timezone-aware timestamps
- Backend treats them as UTC moments
- API returns full ISO 8601 datetime strings with offset or `Z`
- Frontend parses these as moments in time
- Frontend renders them in the viewer's local timezone

This is the correct model for "the same thing happened at one real moment."

### 2. Date-Only Fields Use Calendar-Day Semantics

Any value represented as `YYYY-MM-DD` is a calendar date, not a timestamp.

Examples:
- project `start_date`
- task `start_date`
- task `finish_date`
- assignment `start_date`
- assignment `finish_date`
- dashboard trend bucket dates
- date filters such as `7d`, `30d`, `90d`, custom date ranges

Rules:
- Database stores these as `date`, not timestamp
- Backend must never reinterpret them as UTC-midnight timestamps
- API returns them as plain `YYYY-MM-DD`
- Frontend must treat them as calendar dates, not exact moments

This is the correct model for "this belongs to this day on the calendar."

### 3. Work Calendars Are Not Event Calendars

The current `calendar` feature in Sophikon is a **work calendar**.

It defines:
- working days
- working hours
- holidays
- working-day exceptions

It does **not** define:
- shared meeting events
- attendee-based scheduling
- timezone-aware event start/end timestamps

Rules:
- Work calendars define availability rules for planning and scheduling
- Work calendars are used by task/resource scheduling logic
- Work calendars must not be treated as meeting/event records
- If Sophikon adds true meetings/events later, that must be a separate model with timestamp semantics

### 4. Backend "Today" Must Be Explicit and Centralized

The backend must not use ad hoc day-boundary logic for business-date calculations.

Forbidden pattern:
- random direct calls to `date.today()` or `datetime.now(...).date()` inside unrelated business logic

Required pattern:
- date-based business logic must use one explicit helper/policy for resolving the effective business day

Examples of affected logic:
- overdue detection
- dashboard windows
- days remaining / days elapsed
- schedule status calculations
- date-range reporting

### 5. Business-Day Timezone Policy

For date-only business logic, Sophikon uses **business-day semantics**, not raw UTC-day semantics.

The effective business day should be resolved using the most relevant scope:

1. project timezone
2. organization timezone
3. user timezone
4. application default timezone
5. UTC fallback

Interpretation:
- project-scoped planning logic should prefer project timezone
- organization-scoped dashboards should prefer organization timezone
- user-scoped personal views may use user timezone when no stronger scope exists

If a required scope timezone does not yet exist in the data model, the implementation must use the nearest approved fallback consistently through a shared helper.

### 6. Current Practical Rule Until Full Timezone Scoping Exists

Until Sophikon has fully modeled project and organization timezone settings in scheduling logic:

- exact timestamps continue using UTC end to end
- date-only values remain date-only
- frontend must follow ADR-011 for parsing date-only strings
- backend date-based calculations must be centralized behind a helper instead of scattered `today` calls
- no feature may silently choose a different date boundary from neighboring features without an explicit documented reason

This prevents further drift while allowing phased cleanup.

### 7. Frontend Parsing Contract

Frontend parsing must follow this split:

- Date-only strings (`YYYY-MM-DD`) -> parse as calendar dates using `parseISO`
- Full datetime strings (`2026-04-05T03:00:00Z`) -> parse as exact moments using `new Date(...)`

This ADR adopts and extends [ADR-011-date-parsing-rules.md](C:/Users/wwwer/source/repos/sophikon/docs/02-design/adr/ADR-011-date-parsing-rules.md).

### 8. Future Meeting / Event Model

If Sophikon adds a real meeting/event calendar, it must use timestamp semantics.

Required fields would look like:
- `starts_at`
- `ends_at`
- optional `source_timezone` or organizer timezone metadata

Behavior:
- organizer enters local time
- backend converts to UTC for storage
- all viewers see their local equivalent time

Example:
- organizer in Stockholm creates event: `2026-04-05 05:00`
- backend stores UTC moment
- user in Los Angeles sees the same event on the previous local evening if that is the correct local equivalent

This is correct for meetings and incorrect for date-only due dates.

## Consequences

- Sophikon now has one explicit distinction between timestamp semantics and calendar-day semantics
- The current `calendar` feature is formally documented as a work-calendar system
- Frontend date parsing and backend date logic are no longer allowed to drift independently
- Future scheduling logic must resolve "today" through a shared business-day policy
- Future meeting/event functionality must be modeled separately from work-calendar rules

## Implementation Guidance

Immediate priorities:

1. Replace scattered backend day-boundary calls with a shared helper for business-day resolution
2. Keep date-only API contracts as `YYYY-MM-DD`
3. Keep timestamp API contracts as full ISO datetime strings
4. Treat the current calendar module as scheduling availability infrastructure, not as an event system
5. Review dashboard, task, gantt, resource, and reporting logic for alignment with this contract

## Non-Goals

This ADR does not:
- force immediate timezone-model rollout across every feature
- define the final UX for timezone selection
- introduce a full event/calendar product surface

It defines the semantic contract so future implementation stops drifting.
