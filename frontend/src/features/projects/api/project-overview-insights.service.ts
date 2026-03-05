import { api } from "@/shared/api/api";
import { buildInsightsWindowParams } from "@/shared/api/insights-params";
import type {
  ProjectOverviewInsightsResponse,
  TimeWindowSelection,
} from "@/shared/types/insights";

export const projectOverviewInsightsService = {
  getByProject: async (projectId: string, window: TimeWindowSelection) => {
    const response = await api.get<ProjectOverviewInsightsResponse>(
      `/projects/${projectId}/insights/overview`,
      {
        params: buildInsightsWindowParams(window),
      },
    );
    return response.data;
  },
};
