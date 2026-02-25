export interface Task {
    id: string;
    project_id: string;
    name: string;
    notes?: string;
    start_date: string;
    finish_date: string;
    duration: number;
    work: number;
    percent_complete: number;
    percent_work_complete: number;
    parent_task_id?: string;
    wbs_code: string;
    outline_level: number;
    order_index: number;
    sort_order: number;
    is_summary: boolean;
    is_milestone: boolean;
    is_critical: boolean;
    effort_driven: boolean;
    priority: number;
    constraint_type: string;
    constraint_date?: string;
    deadline?: string;
    task_type: string;
    actual_start?: string;
    actual_finish?: string;
    actual_cost: number;
    total_cost: number;
    fixed_cost: number;
    total_slack: number;
    free_slack: number;
    created_at: string;
    updated_at: string;
}

export interface TaskCreate {
    name: string;
    parent_task_id?: string;
    start_date: string;
    duration?: number;
    is_milestone?: boolean;
    notes?: string;
    task_type?: "FIXED_UNITS" | "FIXED_DURATION" | "FIXED_WORK";
    effort_driven?: boolean;
    fixed_cost?: number;
    constraint_type?: string;
    constraint_date?: string;
    deadline?: string;
    priority?: number;
}

export interface TaskUpdate {
    name?: string;
    parent_task_id?: string | null;
    start_date?: string;
    finish_date?: string;
    duration?: number;
    percent_complete?: number;
    is_milestone?: boolean;
    notes?: string;
    task_type?: "FIXED_UNITS" | "FIXED_DURATION" | "FIXED_WORK";
    effort_driven?: boolean;
    fixed_cost?: number;
    priority?: number;
    constraint_type?: string;
    constraint_date?: string | null;
    deadline?: string | null;
}

export interface TaskReorder {
    after_task_id?: string | null;
    before_task_id?: string | null;
    new_parent_id?: string | null;
}

export interface TaskBulkCreate {
    tasks: TaskCreate[];
}

export interface TaskBulkUpdateItem {
    id: string;
    data: TaskUpdate;
}

export interface TaskBulkUpdate {
    tasks: TaskBulkUpdateItem[];
}

export interface TaskBulkDelete {
    task_ids: string[];
}

export interface BulkOperationError {
    index: number;
    task_id?: string;
    message: string;
}

export interface TaskBulkCreateResponse {
    tasks: Task[];
    errors: BulkOperationError[];
}

export interface BulkOperationResponse {
    succeeded: number;
    failed: number;
    errors: BulkOperationError[];
}

export interface Dependency {
    id: string;
    project_id: string;
    predecessor_id: string;
    successor_id: string;
    type: "FS" | "FF" | "SS" | "SF";
    lag: number;
    lag_format: "DURATION" | "PERCENT";
    is_disabled: boolean;
    created_at: string;
}

export interface DependencyCreate {
    predecessor_id: string;
    successor_id: string;
    type?: "FS" | "FF" | "SS" | "SF";
    lag?: number;
    lag_format?: "DURATION" | "PERCENT";
}
