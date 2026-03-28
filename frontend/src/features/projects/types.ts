import type { TaskStatus } from "@/features/tasks";

export interface ProjectSettings {
  status_thresholds?: {
    IN_PROGRESS?: number;
    IN_REVIEW?: number;
    DONE?: number;
  };
  agent_enabled?: boolean;
  auto_calculate: boolean;
  hours_per_day: number;
  hours_per_week?: number;
  days_per_month: number;
  first_day_of_week?: number;
  default_task_type?: "FIXED_UNITS" | "FIXED_DURATION" | "FIXED_WORK";
  new_tasks_effort_driven?: boolean;
  kanban_wip_limits?: Partial<Record<TaskStatus, number>>;
  [key: string]: unknown;
}

export interface Project {
  id: string;
  owner_id?: string;
  organization_id: string;
  name: string;
  description?: string;
  start_date: string;
  finish_date?: string | null;
  default_calendar_id?: string | null;
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
  default_calendar_id?: string | null;
  color?: string | null;
}

export interface ProjectUpdate {
  name?: string;
  description?: string;
  status?: "active" | "archived" | "completed";
  settings?: Partial<ProjectSettings>;
  default_calendar_id?: string | null;
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
  | "project_member"
  | "comment";

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

export type ProjectRealtimeChannel =
  | "tasks"
  | "resources"
  | "members"
  | "activity"
  | "project"
  | "comments";

export type ProjectPresenceStatus = "viewing" | "editing";

export type ProjectPresenceEntityType =
  | "project"
  | "task"
  | "resource"
  | "assignment"
  | "dependency"
  | "project_member";

export type ProjectConnectionStatus =
  | "idle"
  | "connecting"
  | "connected"
  | "reconnecting"
  | "error";

export interface ProjectPresenceUser {
  id: string;
  full_name?: string | null;
  avatar_url?: string | null;
  status: ProjectPresenceStatus;
  entity_type: ProjectPresenceEntityType;
  entity_id?: string | null;
}

export interface ProjectRealtimeActor {
  id: string;
  full_name?: string | null;
  avatar_url?: string | null;
}

export interface ProjectPresenceSnapshotMessage {
  type: "presence_snapshot";
  project_id: string;
  users: ProjectPresenceUser[];
}

export interface ProjectPresenceUpdateMessage {
  type: "presence_update";
  project_id: string;
  users: ProjectPresenceUser[];
}

export interface ProjectRealtimeEventMessage {
  type:
    | "project_created"
    | "project_updated"
    | "project_deleted"
    | "task_created"
    | "task_updated"
    | "task_deleted"
    | "resource_created"
    | "resource_updated"
    | "resource_deleted"
    | "assignment_created"
    | "assignment_deleted"
    | "dependency_created"
    | "dependency_deleted"
    | "project_member_created"
    | "project_member_updated"
    | "project_member_deleted"
    | "comment_created"
    | "comment_updated"
    | "comment_deleted"
    | "activity_logged";
  project_id: string;
  actor?: ProjectRealtimeActor | null;
  entity_type: ProjectActivityEntityType;
  action: ProjectActivityAction;
  entity_id?: string | null;
  entity_name?: string | null;
  occurred_at: string;
  metadata?: Record<string, unknown> | null;
}

export interface ProjectRealtimeErrorMessage {
  type: "error";
  code: string;
  message: string;
}

export type ProjectWebSocketMessage =
  | ProjectPresenceSnapshotMessage
  | ProjectPresenceUpdateMessage
  | ProjectRealtimeEventMessage
  | ProjectRealtimeErrorMessage;

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
  token?: string;
  invitation_id?: string;
}
