export type TimeWindowPreset = "7d" | "30d" | "90d" | "custom";

export interface TimeWindowSelection {
  windowPreset: TimeWindowPreset;
  startDate?: string;
  endDate?: string;
}

export type RiskLevel = "low" | "medium" | "high";
export type ActivityEntityType = "project" | "task" | "resource";
export type ActivityAction = "created" | "updated";

export interface TrendPoint {
  date: string;
  completed_tasks: number;
  created_tasks: number;
  overdue_tasks: number;
}

export interface RecentActivityItem {
  entity_type: ActivityEntityType;
  entity_id: string;
  entity_name: string;
  action: ActivityAction;
  timestamp: string;
  project_id?: string | null;
  project_name?: string | null;
}

export interface DashboardKpis {
  active_projects: number;
  completed_projects: number;
  task_completion_pct: number;
  overdue_tasks: number;
  critical_tasks: number;
  overallocated_resources: number;
}

export interface ProjectHealthItem {
  project_id: string;
  name: string;
  status: string;
  completion_pct: number;
  overdue_tasks: number;
  critical_tasks: number;
  risk_score: number;
  risk_level: RiskLevel;
}

export interface DashboardInsightsResponse {
  kpis: DashboardKpis;
  project_health: ProjectHealthItem[];
  trend: TrendPoint[];
  recent_activity: RecentActivityItem[];
}

export interface ProjectOverviewKpis {
  total_tasks: number;
  completion_pct: number;
  overdue_tasks: number;
  critical_tasks: number;
  total_resources: number;
  overallocated_resources: number;
}

export interface ProjectOverviewSchedule {
  start_date: string;
  finish_date?: string | null;
  days_remaining?: number | null;
  milestones_due_soon: number;
}

export interface ProjectRiskItem {
  task_id: string;
  name: string;
  reason: string;
  finish_date: string;
  percent_complete: number;
  is_critical: boolean;
}

export interface ProjectOverviewInsightsResponse {
  kpis: ProjectOverviewKpis;
  schedule: ProjectOverviewSchedule;
  trend: TrendPoint[];
  risk_items: ProjectRiskItem[];
  recent_activity: RecentActivityItem[];
}
