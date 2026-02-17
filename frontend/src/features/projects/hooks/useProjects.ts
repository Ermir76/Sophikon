import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { projectService } from "@/features/projects/api/project.service";
import { useOrgStore } from "@/features/organizations/store/org-store";
import type { ProjectCreate, ProjectUpdate } from "@/features/projects/types";

export const projectKeys = {
  all: ["projects"] as const,
  list: (orgId: string) => [...projectKeys.all, "list", orgId] as const,
  detail: (projectId: string) =>
    [...projectKeys.all, "detail", projectId] as const,
};

export function useProjects() {
  const activeOrgId = useOrgStore((state) => state.activeOrgId);

  return useQuery({
    queryKey: projectKeys.list(activeOrgId || ""),
    queryFn: () => projectService.list(activeOrgId!),
    enabled: !!activeOrgId,
  });
}

export function useProject(projectId: string) {
  return useQuery({
    queryKey: projectKeys.detail(projectId),
    queryFn: () => projectService.get(projectId),
    enabled: !!projectId,
  });
}

export function useCreateProject() {
  const queryClient = useQueryClient();
  const activeOrgId = useOrgStore((state) => state.activeOrgId);

  return useMutation({
    mutationFn: (data: Omit<ProjectCreate, "organization_id">) => {
      if (!activeOrgId) throw new Error("No active organization");
      return projectService.create(activeOrgId, data);
    },
    onSuccess: () => {
      if (activeOrgId) {
        queryClient.invalidateQueries({
          queryKey: projectKeys.list(activeOrgId),
        });
      }
    },
  });
}

export function useUpdateProject(projectId: string) {
  const queryClient = useQueryClient();
  const activeOrgId = useOrgStore((state) => state.activeOrgId);

  return useMutation({
    mutationFn: (data: ProjectUpdate) => projectService.update(projectId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: projectKeys.detail(projectId),
      });
      if (activeOrgId) {
        queryClient.invalidateQueries({
          queryKey: projectKeys.list(activeOrgId),
        });
      }
    },
  });
}

export function useDeleteProject(projectId: string) {
  const queryClient = useQueryClient();
  const activeOrgId = useOrgStore((state) => state.activeOrgId);

  return useMutation({
    mutationFn: () => projectService.delete(projectId),
    onSuccess: () => {
      if (activeOrgId) {
        queryClient.invalidateQueries({
          queryKey: projectKeys.list(activeOrgId),
        });
      }
    },
  });
}
