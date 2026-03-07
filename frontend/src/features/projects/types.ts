import type { RecentActivityItem } from "@/shared/types/insights";

export interface ProjectSettings {
  auto_calculate: boolean;
  hours_per_day: number;
  days_per_month: number;
  [key: string]: unknown;
}

export interface Project {
  id: string;
  organization_id: string;
  name: string;
  description?: string;
  start_date: string;
  finish_date?: string | null;
  schedule_from: "start" | "finish";
  status: "active" | "archived" | "completed";
  settings: ProjectSettings;
  color?: string | null;
  created_at: string;
  updated_at: string;
}

export interface ProjectCreate {
  name: string;
  description?: string;
  organization_id: string;
  start_date: string;
  schedule_from?: "start" | "finish";
  currency?: string;
  budget?: number;
  settings?: Partial<ProjectSettings>;
  color?: string | null;
}

export interface ProjectUpdate {
  name?: string;
  description?: string;
  status?: "active" | "archived" | "completed";
  settings?: Partial<ProjectSettings>;
  color?: string | null;
}

export interface ProjectDashboardSummary {
  total_tasks: number;
  completed_tasks: number;
  in_progress_tasks: number;
  not_started_tasks: number;
  overdue_tasks: number;
  milestones: number;
  milestones_completed: number;
  percent_complete: number;
}

export interface ProjectDashboardSchedule {
  start_date: string;
  finish_date?: string | null;
  duration_days?: number | null;
  days_elapsed: number;
  days_remaining?: number | null;
}

export interface ProjectDashboardResources {
  total_resources: number;
  overallocated_count: number;
}

export interface ProjectDashboardCost {
  budget?: number | null;
  total_cost: number;
  actual_cost: number;
  remaining_cost: number;
}

export interface ProjectDashboardCriticalPath {
  task_count: number;
  total_duration_days: number;
  path_length_days: number;
}

export interface UpcomingMilestone {
  task_id: string;
  name: string;
  finish_date: string;
  percent_complete: number;
}

export interface OverdueTask {
  task_id: string;
  name: string;
  finish_date: string;
  percent_complete: number;
  days_overdue: number;
}

export interface ProjectDashboard {
  summary: ProjectDashboardSummary;
  schedule: ProjectDashboardSchedule;
  resources: ProjectDashboardResources;
  cost: ProjectDashboardCost;
  critical_path: ProjectDashboardCriticalPath;
  upcoming_milestones: UpcomingMilestone[];
  overdue_tasks: OverdueTask[];
  recent_activity: RecentActivityItem[];
}
