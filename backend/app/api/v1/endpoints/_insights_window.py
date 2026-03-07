from datetime import date

from app.core.exceptions import ValidationError
from app.schema.insights import InsightsWindowPreset
from app.service import insights_service


def resolve_window_or_422(
    window_preset: InsightsWindowPreset,
    start_date: date | None,
    end_date: date | None,
) -> tuple[date, date]:
    try:
        return insights_service.resolve_window(window_preset, start_date, end_date)
    except ValueError as exc:
        raise ValidationError(str(exc))
