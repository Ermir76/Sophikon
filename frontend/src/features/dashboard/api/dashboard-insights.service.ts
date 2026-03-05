import { api } from "@/shared/api/api";
import { buildInsightsWindowParams } from "@/shared/api/insights-params";
import type {
  DashboardInsightsResponse,
  TimeWindowSelection,
} from "@/shared/types/insights";

export const dashboardInsightsService = {
  getByOrganization: async (
    organizationId: string,
    window: TimeWindowSelection,
  ) => {
    const response = await api.get<DashboardInsightsResponse>(
      `/organizations/${organizationId}/insights/dashboard`,
      {
        params: buildInsightsWindowParams(window),
      },
    );
    return response.data;
  },
};
