"""
Compatibility re-exports for API dependencies.
"""

from .assignment import AssignmentAccess, get_assignment_with_access
from .auth import (
    authenticate_access_token,
    get_current_active_user,
    get_current_user,
    normalize_access_token,
    oauth2_scheme,
)
from .organization import (
    OrgAccess,
    check_org_role,
    get_org_access_or_404,
    get_org_membership_or_404,
)
from .project import (
    ProjectAccess,
    TaskAccess,
    check_role,
    check_role_name,
    get_project_membership_for_user,
    get_project_or_404,
    get_task_with_project_access,
)
from .ws import resolve_project_socket_context, resolve_user_socket

__all__ = [
    "AssignmentAccess",
    "authenticate_access_token",
    "check_org_role",
    "check_role",
    "check_role_name",
    "get_assignment_with_access",
    "get_current_active_user",
    "get_current_user",
    "get_org_access_or_404",
    "get_org_membership_or_404",
    "get_project_membership_for_user",
    "get_project_or_404",
    "get_task_with_project_access",
    "normalize_access_token",
    "oauth2_scheme",
    "OrgAccess",
    "ProjectAccess",
    "resolve_project_socket_context",
    "resolve_user_socket",
    "TaskAccess",
]
