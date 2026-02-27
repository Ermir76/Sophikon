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
