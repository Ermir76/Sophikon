"""
Service contracts for organization membership use-cases.
"""

from typing import TypedDict


class OrganizationMemberInviteInput(TypedDict):
    email: str
    role: str


class OrganizationMemberRolePatchInput(TypedDict):
    role: str
