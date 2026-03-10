"""
Service contracts for organization use-cases.
"""

from typing import TypedDict


class OrganizationCreateInput(TypedDict):
    name: str
    slug: str


class OrganizationPatchInput(TypedDict, total=False):
    name: str
    slug: str
    settings: dict[str, object]
