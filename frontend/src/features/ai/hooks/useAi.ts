import { useMutation, useQuery } from "@tanstack/react-query";

import { aiService } from "@/features/ai/api/ai.service";
import type { AiEstimateRequest } from "@/features/ai/types";

export const aiKeys = {
  all: ["ai"] as const,
  suggestions: (projectId: string | undefined, limit: number) =>
    [...aiKeys.all, "suggestions", projectId, limit] as const,
  conversations: (projectId: string | undefined) =>
    [...aiKeys.all, "conversations", projectId] as const,
  conversation: (projectId: string | undefined, conversationId: string | undefined) =>
    [...aiKeys.all, "conversation", projectId, conversationId] as const,
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
    staleTime: 10 * 60 * 1000,
    refetchOnWindowFocus: false,
    refetchOnMount: false,
  });
}

export function useApprovePlan(projectId: string | undefined) {
  return useMutation({
    mutationFn: ({
      conversationId,
      approved,
      feedback,
    }: {
      conversationId: string;
      approved: boolean;
      feedback?: string;
    }) => {
      if (!projectId) throw new Error("No project selected");
      return aiService.resolvePlanApproval(projectId, conversationId, approved, feedback);
    },
  });
}
