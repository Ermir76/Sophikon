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
