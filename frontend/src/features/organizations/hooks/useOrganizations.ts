import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { organizationService } from "@/features/organizations/api/organization.service";
import type {
  OrganizationCreate,
  OrganizationUpdate,
  InviteMemberRequest,
  UpdateMemberRoleRequest,
} from "@/features/organizations/types";

export const orgKeys = {
  all: ["organizations"] as const,
  list: ["organizations", "list"] as const,
  detail: (orgId: string | null | undefined) => ["organizations", "detail", orgId] as const,
  members: (orgId: string | null | undefined) => ["organizations", "members", orgId] as const,
  myMembership: (orgId: string | null | undefined) =>
    ["organizations", "members", "me", orgId] as const,
};

export function useOrganizations() {
  return useQuery({
    queryKey: orgKeys.list,
    queryFn: () => organizationService.list(1, 100), // Default pagination for now
  });
}

export function useOrganization(orgId?: string | null) {
  return useQuery({
    queryKey: orgKeys.detail(orgId),
    queryFn: () => organizationService.get(orgId!),
    enabled: !!orgId,
  });
}

export function useUpdateOrganization(orgId?: string | null) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: OrganizationUpdate) => {
      if (!orgId) throw new Error("No organization ID provided");
      return organizationService.update(orgId, data);
    },
    onSuccess: () => {
      if (orgId) {
        queryClient.invalidateQueries({ queryKey: orgKeys.detail(orgId) });
        queryClient.invalidateQueries({ queryKey: orgKeys.list });
      }
    },
  });
}

export function useCreateOrganization() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: OrganizationCreate) =>
      organizationService.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: orgKeys.list });
    },
  });
}

export function useDeleteOrganization() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (orgId: string) => organizationService.delete(orgId),
    onSuccess: (_, orgId) => {
      queryClient.invalidateQueries({ queryKey: orgKeys.list });
      queryClient.invalidateQueries({ queryKey: orgKeys.detail(orgId) });
    },
  });
}

export function useOrgMembers(orgId?: string | null) {
  return useQuery({
    queryKey: orgKeys.members(orgId),
    queryFn: () => organizationService.listMembers(orgId!),
    enabled: !!orgId,
  });
}

export function useInviteMember(orgId?: string | null) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: InviteMemberRequest) => {
      if (!orgId) throw new Error("No organization ID provided");
      return organizationService.inviteMember(orgId, data);
    },
    onSuccess: () => {
      if (orgId) {
        queryClient.invalidateQueries({ queryKey: orgKeys.members(orgId) });
      }
    },
  });
}

export function useRemoveMember(orgId?: string | null) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (memberId: string) => {
      if (!orgId) throw new Error("No organization ID provided");
      return organizationService.removeMember(orgId, memberId);
    },
    onSuccess: () => {
      if (orgId) {
        queryClient.invalidateQueries({ queryKey: orgKeys.members(orgId) });
      }
    },
  });
}

export function useUpdateMemberRole(orgId?: string | null) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      memberId,
      data,
    }: {
      memberId: string;
      data: UpdateMemberRoleRequest;
    }) => {
      if (!orgId) throw new Error("No organization ID provided");
      return organizationService.updateMemberRole(orgId, memberId, data);
    },
    onSuccess: () => {
      if (orgId) {
        queryClient.invalidateQueries({ queryKey: orgKeys.members(orgId) });
      }
    },
  });
}
