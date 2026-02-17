export interface Project {
  id: string;
  organization_id: string;
  name: string;
  description?: string;
  status: "active" | "archived" | "completed";
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
  settings?: Record<string, unknown>;
}

export interface ProjectUpdate {
  name?: string;
  description?: string;
  status?: "active" | "archived" | "completed";
}
