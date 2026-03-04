import { api } from "@/shared/api/api";

export interface ScheduleCalculateResponse {
    project_finish_date: string | null;
    critical_path_task_ids: string[];
    tasks_updated: number;
}

export interface CriticalPathTask {
    id: string;
    name: string;
    wbs_code: string;
    start_date: string;
    finish_date: string;
    duration: number;
    total_slack: number;
    free_slack: number;
}

export interface CriticalPathResponse {
    critical_path: CriticalPathTask[];
}

export const scheduleService = {
    calculate: async (projectId: string) => {
        const response = await api.post<ScheduleCalculateResponse>(
            `/projects/${projectId}/schedule/calculate`,
        );
        return response.data;
    },

    getCriticalPath: async (projectId: string) => {
        const response = await api.get<CriticalPathResponse>(
            `/projects/${projectId}/schedule/critical-path`,
        );
        return response.data;
    },
};
