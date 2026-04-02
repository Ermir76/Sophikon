# ADR-011: Date vs. Datetime Parsing Rules in Frontend

**Date:** 2026-04-03
**Status:** Accepted

## Context

A critical bug was discovered in the frontend where dates presented as YYYY-MM-DD (such as task `start_date`, `finish_date`, and trend chart dates) were being shifted by one day for users in UTC-negative timezones (like the US).

The root cause is how JavaScript's native Date parser handles ISO strings:
- When given a date-only string like `"2026-04-02"`, `new Date("2026-04-02")` parses it as `2026-04-02T00:00:00Z` (UTC midnight).
- When rendered via local-time formatters (like `.toLocaleDateString()` or Gantt pixel math), this UTC time corresponds to the evening of the previous day for UTC-negative users (e.g., April 1st, 5:00 PM in PST).

This breaks any UI that relies on visualizing pure calendar days regardless of the time they were created, particularly in the Gantt chart and trend graphics.

## Decision

We are standardizing frontend date parsing to enforce a strict boundary between "calendar dates" and "exact moments in time":

1. **Date-Only Strings (Calendar Dates):** For data representing a specific calendar day without a time component (e.g., `YYYY-MM-DD` from the API for `start_date`, `finish_date`), **must always** be parsed using `parseISO` from `date-fns`.
    - `parseISO("2026-04-02")` evaluates to local midnight (`2026-04-02T00:00:00` in the user's local timezone) rather than UTC. This guarantees the calendar day remains consistent across all timezones.

2. **Full ISO Datetime Strings (Moments in Time):** For data representing an exact moment in time (e.g., `created_at`, `updated_at`, `timestamp`), which come from the backend as complete ISO 8601 strings with timezone offset data, **use the native `new Date()` construct**.
    - `new Date("2026-04-02T14:30:00Z")` correctly identifies the exact UTC time and renders it accurately to the user's local equivalent.

3. **Current Time Reference:** Using `new Date()` with no arguments to get the user's local "now" remains the correct approach for UI state logic.

## Consequences

- The Gantt rendering engine, Kanban due date displays, and dashboard trend charts will accurately plot the exact calendar day listed in the database to the matching label on the UI, regardless of the user's physical location.
- Future components must consciously differentiate between a timezone-independent "calendar day" and a timezone-encoded "moment" when selecting their parser.
