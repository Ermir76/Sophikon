import { api } from "@/shared/api/api";
import type {
    ProjectUtilizationSummary,
    ResourceUtilization,
    OverAllocationResponse,
} from "@/features/resources/types";

export const utilizationService = {
    getProjectUtilization: async (projectId: string, startDate: string, endDate: string) => {
        const response = await api.get<ProjectUtilizationSummary>(
            `/projects/${projectId}/utilization`,
            { params: { start_date: startDate, end_date: endDate } },
        );
        return response.data;
    },

    getResourceUtilization: async (projectId: string, resourceId: string, startDate: string, endDate: string) => {
        const response = await api.get<ResourceUtilization>(
            `/projects/${projectId}/utilization/${resourceId}`,
            { params: { start_date: startDate, end_date: endDate } },
        );
        return response.data;
    },

    getOverAllocations: async (projectId: string, startDate: string, endDate: string) => {
        const response = await api.get<OverAllocationResponse>(
            `/projects/${projectId}/utilization/over-allocations`,
            { params: { start_date: startDate, end_date: endDate } },
        );
        return response.data;
    },
};
