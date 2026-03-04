// ── Enums (matching backend app.models.enums) ──

export type ResourceType = "WORK" | "MATERIAL" | "COST";

export type CostAccrual = "START" | "END" | "PRORATED";

// ── Response ──

export interface Resource {
    id: string;
    project_id: string;
    name: string;
    initials: string | null;
    email: string | null;
    type: ResourceType;
    material_label: string | null;
    max_units: number;
    group_name: string | null;
    code: string | null;
    is_generic: boolean;
    is_active: boolean;
    standard_rate: number;
    overtime_rate: number;
    cost_per_use: number;
    accrue_at: CostAccrual;
    user_id: string | null;
    created_at: string;
    updated_at: string;
}

// ── Request ──

export interface ResourceCreate {
    name: string;
    type?: ResourceType;
    initials?: string | null;
    email?: string | null;
    material_label?: string | null;
    max_units?: number;
    group_name?: string | null;
    code?: string | null;
    is_generic?: boolean;
    standard_rate?: number;
    overtime_rate?: number;
    cost_per_use?: number;
    accrue_at?: CostAccrual;
}

export interface ResourceUpdate {
    name?: string;
    type?: ResourceType;
    initials?: string | null;
    email?: string | null;
    material_label?: string | null;
    max_units?: number;
    group_name?: string | null;
    code?: string | null;
    is_generic?: boolean;
    is_active?: boolean;
    standard_rate?: number;
    overtime_rate?: number;
    cost_per_use?: number;
    accrue_at?: CostAccrual;
}

// ── Utilization (read-only, computed) ──

export interface AssignmentAllocation {
    assignment_id: string;
    task_id: string;
    task_name: string;
    units: number;
}

export interface DailyAllocation {
    date: string;
    allocated_units: number;
    max_units: number;
    is_over_allocated: boolean;
    assignments: AssignmentAllocation[];
}

export interface ResourceUtilization {
    resource_id: string;
    resource_name: string;
    max_units: number;
    daily_allocations: DailyAllocation[];
    peak_units: number;
    average_utilization: number;
}

export interface ProjectUtilizationSummary {
    resources: ResourceUtilization[];
}

export interface OverAllocationItem {
    resource_id: string;
    resource_name: string;
    date: string;
    allocated_units: number;
    max_units: number;
    exceeds_by: number;
}

export interface OverAllocationResponse {
    items: OverAllocationItem[];
    total_count: number;
}
