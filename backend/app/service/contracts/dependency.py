"""
Service contracts for dependency use-cases.
"""

from typing import TypedDict
from uuid import UUID

from app.models.enums import DependencyType, LagFormat


class DependencyCreateInput(TypedDict):
    predecessor_id: UUID
    successor_id: UUID
    type: DependencyType
    lag: int
    lag_format: LagFormat


class DependencyPatchInput(TypedDict, total=False):
    type: DependencyType
    lag: int
    lag_format: LagFormat
    is_disabled: bool
