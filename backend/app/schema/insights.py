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


class ProjectOverviewKpis(BaseModel):
    total_tasks: int = 0
    completion_pct: float = Field(default=0, ge=0, le=100)
    overdue_tasks: int = 0
    critical_tasks: int = 0
    total_resources: int = 0
    overallocated_resources: int = 0


class ProjectOverviewSchedule(BaseModel):
    start_date: date
    finish_date: date | None = None
    days_remaining: int | None = None
    milestones_due_soon: int = 0


class ProjectRiskItem(BaseModel):
    task_id: uuid.UUID
    name: str
    reason: str
    finish_date: date
    percent_complete: float = Field(default=0, ge=0, le=100)
    is_critical: bool


class ProjectOverviewInsightsResponse(BaseModel):
    kpis: ProjectOverviewKpis
    schedule: ProjectOverviewSchedule
    trend: list[TrendPoint]
    risk_items: list[ProjectRiskItem]
    recent_activity: list[RecentActivityItem]
