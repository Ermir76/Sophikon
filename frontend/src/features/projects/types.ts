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
}

export type ProjectActivityEntityType =
  | "project"
  | "task"
  | "resource"
  | "assignment"
  | "dependency"
  | "project_member";

export type ProjectActivityAction = "created" | "updated" | "deleted" | "restored";

export interface ProjectActivityActor {
  id: string;
  full_name?: string | null;
  avatar_url?: string | null;
}

export interface ProjectActivityChangeField {
  field: string;
  old?: unknown;
  new?: unknown;
}

export interface ProjectActivityChanges {
  fields: ProjectActivityChangeField[];
}

export interface ProjectActivityItem {
  id: string;
  user?: ProjectActivityActor | null;
  action: ProjectActivityAction;
  entity_type: ProjectActivityEntityType;
  entity_id?: string | null;
  entity_name?: string | null;
  changes?: ProjectActivityChanges | null;
  created_at: string;
}

export type ProjectMemberRole = "owner" | "manager" | "member" | "viewer";

export interface ProjectMember {
  id: string;
  project_id: string;
  user_id: string;
  role: ProjectMemberRole;
  joined_at: string;
  updated_at: string;
  user_email?: string | null;
  user_full_name?: string | null;
}

export interface ProjectInvitation {
  id: string;
  project_id: string;
  invited_by_id: string;
  role: ProjectMemberRole;
  email: string;
  message?: string | null;
  expires_at: string;
  accepted_at?: string | null;
  is_revoked: boolean;
  created_at: string;
  invited_by_email?: string | null;
  invited_by_full_name?: string | null;
}

export interface InviteProjectMemberRequest {
  email: string;
  role: ProjectMemberRole;
  message?: string;
}

export interface AcceptProjectInvitationRequest {
  token: string;
}
