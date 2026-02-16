"""
Centralized enums for database models.

All enums inherit from StrEnum for JSON serialization compatibility.
These are used in SQLAlchemy models and Pydantic schemas.
"""

from enum import StrEnum

# ============================================================================
# PROJECT
# ============================================================================


class ProjectStatus(StrEnum):
    """Project lifecycle status."""

    PLANNING = "PLANNING"
    ACTIVE = "ACTIVE"
    ON_HOLD = "ON_HOLD"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class ScheduleFrom(StrEnum):
    """Project scheduling direction."""

    START = "START"
    FINISH = "FINISH"


# ============================================================================
# TASK
# ============================================================================


class TaskType(StrEnum):
    """Task scheduling type (determines what stays fixed when adjusting)."""

    FIXED_UNITS = "FIXED_UNITS"
    FIXED_DURATION = "FIXED_DURATION"
    FIXED_WORK = "FIXED_WORK"


class ConstraintType(StrEnum):
    """Task scheduling constraints."""

    ASAP = "ASAP"  # As Soon As Possible
    ALAP = "ALAP"  # As Late As Possible
    MSO = "MSO"  # Must Start On
    MFO = "MFO"  # Must Finish On
    SNET = "SNET"  # Start No Earlier Than
    SNLT = "SNLT"  # Start No Later Than
    FNET = "FNET"  # Finish No Earlier Than
    FNLT = "FNLT"  # Finish No Later Than


class CostAccrual(StrEnum):
    """When costs are accrued."""

    START = "START"
    END = "END"
    PRORATED = "PRORATED"


# ============================================================================
# DEPENDENCY
# ============================================================================


class DependencyType(StrEnum):
    """Task dependency relationship types."""

    FS = "FS"  # Finish-to-Start
    FF = "FF"  # Finish-to-Finish
    SS = "SS"  # Start-to-Start
    SF = "SF"  # Start-to-Finish


class LagFormat(StrEnum):
    """Lag/lead time format."""

    DURATION = "DURATION"
    PERCENT = "PERCENT"


# ============================================================================
# RESOURCE
# ============================================================================


class ResourceType(StrEnum):
    """Resource types."""

    WORK = "WORK"  # People (hours)
    MATERIAL = "MATERIAL"  # Consumables (units)
    COST = "COST"  # Fixed costs


# ============================================================================
# ASSIGNMENT
# ============================================================================


class WorkContour(StrEnum):
    """Work distribution patterns over time."""

    FLAT = "FLAT"
    BACK_LOADED = "BACK_LOADED"
    FRONT_LOADED = "FRONT_LOADED"
    DOUBLE_PEAK = "DOUBLE_PEAK"
    EARLY_PEAK = "EARLY_PEAK"
    LATE_PEAK = "LATE_PEAK"
    BELL = "BELL"
    TURTLE = "TURTLE"
    CONTOURED = "CONTOURED"  # Custom pattern


class RateTable(StrEnum):
    """Cost rate tables (A-E)."""

    A = "A"
    B = "B"
    C = "C"
    D = "D"
    E = "E"


# ============================================================================
# ROLE
# ============================================================================


class RoleScope(StrEnum):
    """Role scope levels."""

    SYSTEM = "system"  # System-wide roles (admin, user)
    PROJECT = "project"  # Project-specific roles (owner, manager, member, viewer)


class OrgRole(StrEnum):
    """Organization membership roles."""

    OWNER = "owner"  # Full control, billing, can delete org
    ADMIN = "admin"  # Manage members, create projects
    MEMBER = "member"  # Access projects they're assigned to


# ============================================================================
# TIME TRACKING
# ============================================================================


class BillingStatus(StrEnum):
    """Time entry billing status."""

    UNBILLED = "UNBILLED"
    BILLED = "BILLED"
    NON_BILLABLE = "NON_BILLABLE"


class TimeEntryStatus(StrEnum):
    """Time entry approval status."""

    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


# ============================================================================
# ATTACHMENTS
# ============================================================================


class StorageProvider(StrEnum):
    """File storage providers."""

    LOCAL = "local"
    S3 = "s3"


# ============================================================================
# NOTIFICATIONS
# ============================================================================


class NotificationType(StrEnum):
    """Notification event types."""

    TASK_ASSIGNED = "task_assigned"
    TASK_UPDATED = "task_updated"
    MENTIONED = "mentioned"
    COMMENT_ADDED = "comment_added"
    DEADLINE_APPROACHING = "deadline_approaching"
    INVITATION_RECEIVED = "invitation_received"


# ============================================================================
# AI
# ============================================================================


class AIMessageRole(StrEnum):
    """AI message roles."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


# ============================================================================
# AUDIT
# ============================================================================


class AuditAction(StrEnum):
    """Audit log action types."""

    CREATED = "created"
    UPDATED = "updated"
    DELETED = "deleted"
    RESTORED = "restored"
