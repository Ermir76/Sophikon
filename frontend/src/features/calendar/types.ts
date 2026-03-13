export interface WorkBreak {
  start: string;
  end: string;
}

export interface WorkDay {
  start: string;
  end: string;
  breaks: WorkBreak[];
}

export interface RecurrenceRule {
  type: string;
  month?: number | null;
  day?: number | null;
  weekday?: number | null;
  interval?: number | null;
}

export interface Calendar {
  id: string;
  project_id: string | null;
  base_calendar_id: string | null;
  name: string;
  is_base: boolean;
  work_week: Array<WorkDay | null>;
  created_at: string;
  updated_at: string;
}

export interface CalendarCreate {
  name: string;
  is_base?: boolean;
  work_week?: Array<WorkDay | null> | null;
  base_calendar_id?: string | null;
}

export interface CalendarUpdate {
  name?: string;
  is_base?: boolean;
  work_week?: Array<WorkDay | null> | null;
  base_calendar_id?: string | null;
}

export interface CalendarException {
  id: string;
  calendar_id: string;
  name: string;
  start_date: string;
  end_date: string;
  is_working: boolean;
  work_times: WorkDay | null;
  recurrence: RecurrenceRule | null;
  created_at: string;
}

export interface CalendarExceptionCreate {
  name: string;
  start_date: string;
  end_date: string;
  is_working?: boolean;
  work_times?: WorkDay | null;
  recurrence?: RecurrenceRule | null;
}

export interface CalendarExceptionUpdate {
  name?: string;
  start_date?: string;
  end_date?: string;
  is_working?: boolean;
  work_times?: WorkDay | null;
  recurrence?: RecurrenceRule | null;
}
