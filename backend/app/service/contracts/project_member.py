"""
Service contracts for project membership and invitations.
"""

from typing import Literal, NotRequired, TypedDict

type ProjectRoleName = Literal["owner", "manager", "member", "viewer"]


class ProjectMemberInviteInput(TypedDict):
    email: str
    role: ProjectRoleName
    message: str | None


class ProjectMemberRolePatchInput(TypedDict):
    role: ProjectRoleName


class ProjectInvitationAcceptInput(TypedDict):
    token: NotRequired[str]
    invitation_id: NotRequired[str]
