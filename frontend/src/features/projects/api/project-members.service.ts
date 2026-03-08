import { api } from "@/shared/api/api";
import type { PaginatedResponse } from "@/shared/types/api";
import type {
  AcceptProjectInvitationRequest,
  InviteProjectMemberRequest,
  ProjectInvitation,
  ProjectMember,
  ProjectMemberRole,
} from "@/features/projects/types";

interface InvitationResponse {
  invitation: ProjectInvitation;
}

export const projectMembersService = {
  async listMembers(
    projectId: string,
    page = 1,
    per_page = 20,
  ): Promise<PaginatedResponse<ProjectMember>> {
    const response = await api.get<PaginatedResponse<ProjectMember>>(
      `/projects/${projectId}/members`,
      { params: { page, per_page } },
    );
    return response.data;
  },

  async inviteMember(
    projectId: string,
    data: InviteProjectMemberRequest,
  ): Promise<ProjectInvitation> {
    const response = await api.post<InvitationResponse>(
      `/projects/${projectId}/members/invite`,
      data,
    );
    return response.data.invitation;
  },

  async listInvitations(
    projectId: string,
    page = 1,
    per_page = 20,
  ): Promise<PaginatedResponse<ProjectInvitation>> {
    const response = await api.get<PaginatedResponse<ProjectInvitation>>(
      `/projects/${projectId}/members/invitations`,
      { params: { page, per_page } },
    );
    return response.data;
  },

  async resendInvitation(
    projectId: string,
    invitationId: string,
  ): Promise<ProjectInvitation> {
    const response = await api.post<InvitationResponse>(
      `/projects/${projectId}/members/invitations/${invitationId}/resend`,
    );
    return response.data.invitation;
  },

  async revokeInvitation(projectId: string, invitationId: string): Promise<void> {
    await api.delete(`/projects/${projectId}/members/invitations/${invitationId}`);
  },

  async updateMemberRole(
    projectId: string,
    memberId: string,
    role: ProjectMemberRole,
  ): Promise<ProjectMember> {
    const response = await api.patch<ProjectMember>(
      `/projects/${projectId}/members/${memberId}`,
      { role },
    );
    return response.data;
  },

  async removeMember(projectId: string, memberId: string): Promise<void> {
    await api.delete(`/projects/${projectId}/members/${memberId}`);
  },

  async acceptInvitation(
    data: AcceptProjectInvitationRequest,
  ): Promise<{ project_id: string; member_id: string }> {
    const response = await api.post<{ project_id: string; member_id: string }>(
      "/projects/members/invitations/accept",
      data,
    );
    return response.data;
  },
};
