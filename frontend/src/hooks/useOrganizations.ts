import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { organizationService } from "@/services/organization";
import type {
  OrganizationUpdate,
  InviteMemberRequest,
  UpdateMemberRoleRequest,
} from "@/types/organization";

export const orgKeys = {
  all: ["organizations"] as const,
  list: ["organizations", "list"] as const,
  detail: (orgId: string) => ["organizations", "detail", orgId] as const,
  members: (orgId: string) => ["organizations", "members", orgId] as const,
};

export function useOrganizations() {
  return useQuery({
    queryKey: orgKeys.list,
    queryFn: () => organizationService.list(1, 100), // Default pagination for now
  });
}

export function useOrganization(orgId: string) {
  return useQuery({
    queryKey: orgKeys.detail(orgId),
    queryFn: () => organizationService.get(orgId),
    enabled: !!orgId,
  });
}

export function useUpdateOrganization(orgId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: OrganizationUpdate) =>
      organizationService.update(orgId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: orgKeys.detail(orgId) });
      queryClient.invalidateQueries({ queryKey: orgKeys.list });
    },
  });
}

export function useOrgMembers(orgId: string) {
  return useQuery({
    queryKey: orgKeys.members(orgId),
    queryFn: () => organizationService.listMembers(orgId),
    enabled: !!orgId,
  });
}

export function useInviteMember(orgId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: InviteMemberRequest) =>
      organizationService.inviteMember(orgId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: orgKeys.members(orgId) });
    },
  });
}

export function useRemoveMember(orgId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (memberId: string) =>
      organizationService.removeMember(orgId, memberId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: orgKeys.members(orgId) });
    },
  });
}

export function useUpdateMemberRole(orgId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      memberId,
      data,
    }: {
      memberId: string;
      data: UpdateMemberRoleRequest;
    }) => organizationService.updateMemberRole(orgId, memberId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: orgKeys.members(orgId) });
    },
  });
}
