"""
Service contracts for resource use-cases.
"""

from decimal import Decimal
from typing import TypedDict

from app.models.enums import CostAccrual, ResourceType


class ResourceCreateInput(TypedDict):
    name: str
    type: ResourceType
    initials: str | None
    email: str | None
    material_label: str | None
    max_units: Decimal
    group_name: str | None
    code: str | None
    is_generic: bool
    standard_rate: Decimal
    overtime_rate: Decimal
    cost_per_use: Decimal
    accrue_at: CostAccrual


class ResourcePatchInput(TypedDict, total=False):
    name: str
    type: ResourceType
    initials: str | None
    email: str | None
    material_label: str | None
    max_units: Decimal
    group_name: str | None
    code: str | None
    is_generic: bool
    is_active: bool
    standard_rate: Decimal
    overtime_rate: Decimal
    cost_per_use: Decimal
    accrue_at: CostAccrual
