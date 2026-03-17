import { useQuery } from "@tanstack/react-query";

import { aiService } from "@/features/ai/api/ai.service";
import { aiKeys } from "@/features/ai/hooks/useAi";

export function useConversations(projectId: string | undefined) {
  return useQuery({
    queryKey: aiKeys.conversations(projectId),
    queryFn: () => aiService.getConversations(projectId!),
    enabled: Boolean(projectId),
    staleTime: 30 * 1000,
    refetchOnWindowFocus: false,
  });
}

export function useConversation(
  projectId: string | undefined,
  conversationId: string | undefined,
) {
  return useQuery({
    queryKey: aiKeys.conversation(projectId, conversationId),
    queryFn: () => aiService.getConversation(projectId!, conversationId!),
    enabled: Boolean(projectId) && Boolean(conversationId),
    staleTime: 60 * 1000,
    refetchOnWindowFocus: false,
  });
}
