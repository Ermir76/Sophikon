"""
Pydantic schemas for Dashboard/Overview insights endpoints.
"""

import uuid
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.models.enums import ProjectStatus

InsightsWindowPreset = Literal["7d", "30d", "90d", "custom"]
RiskLevel = Literal["low", "medium", "high"]
ActivityEntityType = Literal["project", "task", "resource"]
ActivityAction = Literal["created", "updated"]


class TrendPoint(BaseModel):
    date: date
    completed_tasks: int = 0
    created_tasks: int = 0
    overdue_tasks: int = 0


class RecentActivityItem(BaseModel):
    entity_type: ActivityEntityType
    entity_id: uuid.UUID
    entity_name: str
    action: ActivityAction
    timestamp: datetime
    project_id: uuid.UUID | None = None
    project_name: str | None = None


class DashboardKpis(BaseModel):
    active_projects: int = 0
    completed_projects: int = 0
    task_completion_pct: float = Field(default=0, ge=0, le=100)
    overdue_tasks: int = 0
    critical_tasks: int = 0
    overallocated_resources: int = 0


class ProjectHealthItem(BaseModel):
    project_id: uuid.UUID
    name: str
    status: ProjectStatus
    completion_pct: float = Field(default=0, ge=0, le=100)
    overdue_tasks: int = 0
    critical_tasks: int = 0
    risk_score: float = Field(default=0, ge=0, le=100)
    risk_level: RiskLevel = "low"


class DashboardInsightsResponse(BaseModel):
    kpis: DashboardKpis
    project_health: list[ProjectHealthItem]
    trend: list[TrendPoint]
    recent_activity: list[RecentActivityItem]


class ProjectDashboardSummary(BaseModel):
    total_tasks: int = 0
    completed_tasks: int = 0
    in_progress_tasks: int = 0
    not_started_tasks: int = 0
    overdue_tasks: int = 0
    milestones: int = 0
    milestones_completed: int = 0
    percent_complete: float = Field(default=0, ge=0, le=100)


class ProjectDashboardSchedule(BaseModel):
    start_date: date
    finish_date: date | None = None
    duration_days: int | None = None
    days_elapsed: int = 0
    days_remaining: int | None = None


class ProjectDashboardResources(BaseModel):
    total_resources: int = 0
    overallocated_count: int = 0


class ProjectDashboardCost(BaseModel):
    budget: float | None = None
    total_cost: float = 0
    actual_cost: float = 0
    remaining_cost: float = 0


class ProjectDashboardCriticalPath(BaseModel):
    task_count: int = 0
    total_duration_days: int = 0
    path_length_days: int = 0


class UpcomingMilestone(BaseModel):
    task_id: uuid.UUID
    name: str
    finish_date: date
    percent_complete: float = Field(default=0, ge=0, le=100)


class OverdueTask(BaseModel):
    task_id: uuid.UUID
    name: str
    finish_date: date
    percent_complete: float = Field(default=0, ge=0, le=100)
    days_overdue: int = 0


class ProjectDashboardResponse(BaseModel):
    summary: ProjectDashboardSummary
    schedule: ProjectDashboardSchedule
    resources: ProjectDashboardResources
    cost: ProjectDashboardCost
    critical_path: ProjectDashboardCriticalPath
    upcoming_milestones: list[UpcomingMilestone]
    overdue_tasks: list[OverdueTask]
    recent_activity: list[RecentActivityItem]
