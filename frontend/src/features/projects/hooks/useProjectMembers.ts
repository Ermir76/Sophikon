import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { projectMembersService } from "@/features/projects/api/project-members.service";
import type {
  AcceptProjectInvitationRequest,
  InviteProjectMemberRequest,
  ProjectMemberRole,
} from "@/features/projects/types";

export const projectMemberKeys = {
  all: ["project-members"] as const,
  members: (projectId: string | null | undefined) =>
    [...projectMemberKeys.all, "members", projectId] as const,
  invitations: (projectId: string | null | undefined) =>
    [...projectMemberKeys.all, "invitations", projectId] as const,
};

export function useProjectMembers(projectId?: string | null) {
  return useQuery({
    queryKey: projectMemberKeys.members(projectId),
    queryFn: () => projectMembersService.listMembers(projectId!),
    enabled: !!projectId,
  });
}

export function useProjectInvitations(
  projectId?: string | null,
  enabled = true,
) {
  return useQuery({
    queryKey: projectMemberKeys.invitations(projectId),
    queryFn: () => projectMembersService.listInvitations(projectId!),
    enabled: !!projectId && enabled,
  });
}

export function useInviteProjectMember(projectId?: string | null) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: InviteProjectMemberRequest) => {
      if (!projectId) throw new Error("No project ID provided");
      return projectMembersService.inviteMember(projectId, data);
    },
    onSuccess: () => {
      if (!projectId) return;
      queryClient.invalidateQueries({ queryKey: projectMemberKeys.invitations(projectId) });
    },
  });
}

export function useResendProjectInvitation(projectId?: string | null) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (invitationId: string) => {
      if (!projectId) throw new Error("No project ID provided");
      return projectMembersService.resendInvitation(projectId, invitationId);
    },
    onSuccess: () => {
      if (!projectId) return;
      queryClient.invalidateQueries({ queryKey: projectMemberKeys.invitations(projectId) });
    },
  });
}

export function useRevokeProjectInvitation(projectId?: string | null) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (invitationId: string) => {
      if (!projectId) throw new Error("No project ID provided");
      return projectMembersService.revokeInvitation(projectId, invitationId);
    },
    onSuccess: () => {
      if (!projectId) return;
      queryClient.invalidateQueries({ queryKey: projectMemberKeys.invitations(projectId) });
    },
  });
}

export function useUpdateProjectMemberRole(projectId?: string | null) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ memberId, role }: { memberId: string; role: ProjectMemberRole }) => {
      if (!projectId) throw new Error("No project ID provided");
      return projectMembersService.updateMemberRole(projectId, memberId, role);
    },
    onSuccess: () => {
      if (!projectId) return;
      queryClient.invalidateQueries({ queryKey: projectMemberKeys.members(projectId) });
    },
  });
}

export function useRemoveProjectMember(projectId?: string | null) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (memberId: string) => {
      if (!projectId) throw new Error("No project ID provided");
      return projectMembersService.removeMember(projectId, memberId);
    },
    onSuccess: () => {
      if (!projectId) return;
      queryClient.invalidateQueries({ queryKey: projectMemberKeys.members(projectId) });
    },
  });
}

export function useAcceptProjectInvitation() {
  return useMutation({
    mutationFn: (data: AcceptProjectInvitationRequest) =>
      projectMembersService.acceptInvitation(data),
  });
}
