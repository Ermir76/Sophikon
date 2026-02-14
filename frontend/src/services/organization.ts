import type { PaginatedResponse } from "@/types/api";

import { api } from "@/services/api";
import type {
  Organization,
  OrganizationCreate,
  OrganizationUpdate,
  OrganizationMember,
  OrgMemberInvite,
  OrgMemberRoleUpdate,
} from "@/types/organization";

export const organizationService = {
  // ── Organizations ──

  async list(
    page = 1,
    per_page = 20,
  ): Promise<PaginatedResponse<Organization>> {
    const response = await api.get<PaginatedResponse<Organization>>(
      "/organizations",
      {
        params: { page, per_page },
      },
    );
    return response.data;
  },

  async get(id: string): Promise<Organization> {
    const response = await api.get<Organization>(`/organizations/${id}`);
    return response.data;
  },

  async create(data: OrganizationCreate): Promise<Organization> {
    const response = await api.post<Organization>("/organizations", data);
    return response.data;
  },

  async update(id: string, data: OrganizationUpdate): Promise<Organization> {
    const response = await api.patch<Organization>(
      `/organizations/${id}`,
      data,
    );
    return response.data;
  },

  async delete(id: string): Promise<void> {
    await api.delete(`/organizations/${id}`);
  },

  // ── Members ──

  async listMembers(
    orgId: string,
    page = 1,
    per_page = 20,
  ): Promise<PaginatedResponse<OrganizationMember>> {
    const response = await api.get<PaginatedResponse<OrganizationMember>>(
      `/organizations/${orgId}/members`,
      {
        params: { page, per_page },
      },
    );
    return response.data;
  },

  async inviteMember(
    orgId: string,
    data: OrgMemberInvite,
  ): Promise<OrganizationMember> {
    const response = await api.post<OrganizationMember>(
      `/organizations/${orgId}/members`,
      data,
    );
    return response.data;
  },

  async updateMemberRole(
    orgId: string,
    memberId: string,
    data: OrgMemberRoleUpdate,
  ): Promise<OrganizationMember> {
    const response = await api.patch<OrganizationMember>(
      `/organizations/${orgId}/members/${memberId}`,
      data,
    );
    return response.data;
  },

  async removeMember(orgId: string, memberId: string): Promise<void> {
    await api.delete(`/organizations/${orgId}/members/${memberId}`);
  },
};
