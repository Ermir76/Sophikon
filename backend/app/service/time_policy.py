"""
Shared time/date policy helpers.
"""

from datetime import date, datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.models.organization import Organization
from app.models.project import Project
from app.models.user import User


def _coerce_timezone(timezone_name: object) -> ZoneInfo | None:
    if not isinstance(timezone_name, str) or not timezone_name.strip():
        return None

    try:
        return ZoneInfo(timezone_name.strip())
    except ZoneInfoNotFoundError:
        return None


def resolve_business_timezone(
    *,
    project: Project | None = None,
    organization: Organization | None = None,
    user: User | None = None,
) -> ZoneInfo | None:
    """
    Resolve the effective business timezone for date-only calculations.

    Resolution order follows ADR-012:
    project -> organization -> user -> application/runtime fallback.
    """
    if project is not None:
        timezone_name = project.settings.get("timezone")
        timezone = _coerce_timezone(timezone_name)
        if timezone is not None:
            return timezone

    if organization is not None:
        timezone_name = organization.settings.get("timezone")
        timezone = _coerce_timezone(timezone_name)
        if timezone is not None:
            return timezone

    if user is not None:
        timezone = _coerce_timezone(user.timezone)
        if timezone is not None:
            return timezone

    return None


def resolve_business_day(
    *,
    now: datetime | None = None,
    project: Project | None = None,
    organization: Organization | None = None,
    user: User | None = None,
) -> date:
    """
    Resolve the effective business day for date-only logic.

    Until timezone scoping is fully modeled across the app, this preserves
    the current local/runtime day behavior when no scoped timezone is available.
    """
    timezone = resolve_business_timezone(
        project=project,
        organization=organization,
        user=user,
    )
    if timezone is None:
        return date.today() if now is None else now.date()

    reference_now = datetime.now(timezone) if now is None else now.astimezone(timezone)
    return reference_now.date()
