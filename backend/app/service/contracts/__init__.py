"""
Service-layer contracts (API-agnostic input payloads).
"""

from app.service.contracts.assignment import AssignmentCreateInput, AssignmentPatchInput
from app.service.contracts.calendar import (
    CalendarCreateInput,
    CalendarExceptionCreateInput,
    CalendarExceptionPatchInput,
    CalendarPatchInput,
)
from app.service.contracts.dependency import DependencyCreateInput, DependencyPatchInput
from app.service.contracts.organization import (
    OrganizationCreateInput,
    OrganizationPatchInput,
)
from app.service.contracts.organization_member import (
    OrganizationMemberInviteInput,
    OrganizationMemberRolePatchInput,
)
from app.service.contracts.project_member import (
    ProjectInvitationAcceptInput,
    ProjectMemberInviteInput,
    ProjectMemberRolePatchInput,
    ProjectRoleName,
)
from app.service.contracts.resource import ResourceCreateInput, ResourcePatchInput

__all__ = [
    "AssignmentCreateInput",
    "AssignmentPatchInput",
    "CalendarCreateInput",
    "CalendarExceptionCreateInput",
    "CalendarExceptionPatchInput",
    "CalendarPatchInput",
    "DependencyCreateInput",
    "DependencyPatchInput",
    "OrganizationCreateInput",
    "OrganizationMemberInviteInput",
    "OrganizationMemberRolePatchInput",
    "OrganizationPatchInput",
    "ProjectInvitationAcceptInput",
    "ProjectMemberInviteInput",
    "ProjectMemberRolePatchInput",
    "ProjectRoleName",
    "ResourceCreateInput",
    "ResourcePatchInput",
]
