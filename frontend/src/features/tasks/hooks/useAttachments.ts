import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { attachmentService } from "@/features/tasks/api/attachment.service";

export const attachmentKeys = {
  all: ["attachments"] as const,
  list: (projectId: string | undefined, taskId: string | undefined) =>
    [...attachmentKeys.all, projectId, taskId] as const,
};

export function useAttachments(projectId: string | undefined, taskId: string | undefined) {
  return useQuery({
    queryKey: attachmentKeys.list(projectId, taskId),
    queryFn: () => attachmentService.list(projectId!, taskId!),
    enabled: !!projectId && !!taskId,
  });
}

export function useUploadAttachment(projectId: string | undefined, taskId: string | undefined) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: { file: File; description?: string }) => {
      if (!projectId || !taskId) throw new Error("Missing project or task");
      return attachmentService.upload(projectId, taskId, payload);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: attachmentKeys.list(projectId, taskId) });
    },
  });
}

export function useDeleteAttachment(projectId: string | undefined, taskId: string | undefined) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (attachmentId: string) => {
      if (!projectId || !taskId) throw new Error("Missing project or task");
      return attachmentService.remove(projectId, taskId, attachmentId);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: attachmentKeys.list(projectId, taskId) });
    },
  });
}
