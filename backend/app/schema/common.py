"""
Common Pydantic schemas shared across endpoints.
"""

from pydantic import BaseModel, computed_field


class PaginatedResponse[T](BaseModel):
    """Generic paginated response wrapper."""

    items: list[T]
    total: int
    page: int
    per_page: int

    @computed_field
    @property
    def total_pages(self) -> int:
        if self.per_page <= 0:
            return 0
        return (self.total + self.per_page - 1) // self.per_page
