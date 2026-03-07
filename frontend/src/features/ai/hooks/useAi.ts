import { useMutation, useQuery } from "@tanstack/react-query";

import { aiService } from "@/features/ai/api/ai.service";
import type { AiEstimateRequest } from "@/features/ai/types";

export const aiKeys = {
  all: ["ai"] as const,
  suggestions: (projectId: string | undefined, limit: number) =>
    [...aiKeys.all, "suggestions", projectId, limit] as const,
};

export function useAiEstimate(projectId: string | undefined) {
  return useMutation({
    mutationFn: (payload: AiEstimateRequest) => {
      if (!projectId) throw new Error("No project selected");
      return aiService.estimate(projectId, payload);
    },
  });
}

export function useAiSuggestions(
  projectId: string | undefined,
  limit = 5,
  enabled = true,
) {
  return useQuery({
    queryKey: aiKeys.suggestions(projectId, limit),
    queryFn: () => aiService.suggestions(projectId!, limit),
    enabled: Boolean(projectId) && enabled,
  });
}
