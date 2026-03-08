import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ProjectMembersTab } from "@/features/projects/components/ProjectMembersTab";

let currentUserId = "owner-user";

vi.mock("sonner", () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
  },
}));

vi.mock("@/features/auth", () => ({
  useAuthStore: vi.fn((selector) => selector({ user: { id: currentUserId } })),
}));

vi.mock("@/features/projects/hooks/useProjectMembers", () => ({
  useProjectMembers: vi.fn(),
  useProjectInvitations: vi.fn(),
  useInviteProjectMember: vi.fn(),
  useUpdateProjectMemberRole: vi.fn(),
  useRemoveProjectMember: vi.fn(),
  useResendProjectInvitation: vi.fn(),
  useRevokeProjectInvitation: vi.fn(),
}));

import {
  useInviteProjectMember,
  useProjectInvitations,
  useProjectMembers,
  useRemoveProjectMember,
  useResendProjectInvitation,
  useRevokeProjectInvitation,
  useUpdateProjectMemberRole,
} from "@/features/projects/hooks/useProjectMembers";

describe("ProjectMembersTab", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    currentUserId = "owner-user";

    vi.mocked(useProjectMembers).mockReturnValue({
      data: {
        items: [
          {
            id: "owner-member",
            project_id: "project-1",
            user_id: "owner-user",
            role: "owner",
            joined_at: "2026-03-01T00:00:00Z",
            updated_at: "2026-03-01T00:00:00Z",
            user_email: "owner@example.com",
            user_full_name: "Owner",
          },
          {
            id: "member-1",
            project_id: "project-1",
            user_id: "member-user",
            role: "member",
            joined_at: "2026-03-01T00:00:00Z",
            updated_at: "2026-03-01T00:00:00Z",
            user_email: "member@example.com",
            user_full_name: "Member",
          },
        ],
      },
      isLoading: false,
      isError: false,
      refetch: vi.fn(),
    } as never);

    vi.mocked(useProjectInvitations).mockReturnValue({
      data: {
        items: [
          {
            id: "inv-1",
            project_id: "project-1",
            invited_by_id: "owner-user",
            role: "member",
            email: "invitee@example.com",
            expires_at: "2026-03-20T00:00:00Z",
            accepted_at: null,
            is_revoked: false,
            created_at: "2026-03-12T00:00:00Z",
          },
        ],
      },
      isLoading: false,
      isError: false,
      refetch: vi.fn(),
    } as never);

    vi.mocked(useInviteProjectMember).mockReturnValue({
      mutateAsync: vi.fn(),
      isPending: false,
    } as never);
    vi.mocked(useUpdateProjectMemberRole).mockReturnValue({
      mutateAsync: vi.fn(),
      isPending: false,
    } as never);
    vi.mocked(useRemoveProjectMember).mockReturnValue({
      mutateAsync: vi.fn(),
      isPending: false,
    } as never);
    vi.mocked(useResendProjectInvitation).mockReturnValue({
      mutateAsync: vi.fn(),
      isPending: false,
    } as never);
    vi.mocked(useRevokeProjectInvitation).mockReturnValue({
      mutateAsync: vi.fn(),
      isPending: false,
    } as never);
  });

  it("wires member and invitation actions", () => {
    const removeSpy = vi.fn().mockResolvedValue(undefined);
    const resendSpy = vi.fn().mockResolvedValue(undefined);
    const revokeSpy = vi.fn().mockResolvedValue(undefined);

    vi.mocked(useRemoveProjectMember).mockReturnValue({
      mutateAsync: removeSpy,
      isPending: false,
    } as never);
    vi.mocked(useResendProjectInvitation).mockReturnValue({
      mutateAsync: resendSpy,
      isPending: false,
    } as never);
    vi.mocked(useRevokeProjectInvitation).mockReturnValue({
      mutateAsync: revokeSpy,
      isPending: false,
    } as never);

    render(<ProjectMembersTab projectId="project-1" />);

    expect(useProjectInvitations).toHaveBeenCalledWith("project-1", true);

    fireEvent.click(screen.getByRole("button", { name: "Remove" }));
    expect(removeSpy).not.toHaveBeenCalled();

    fireEvent.click(screen.getByRole("button", { name: "Remove Member" }));
    expect(removeSpy).toHaveBeenCalledWith("member-1");

    fireEvent.click(screen.getByRole("button", { name: "Resend" }));
    expect(resendSpy).toHaveBeenCalledWith("inv-1");

    fireEvent.click(screen.getByRole("button", { name: "Revoke" }));
    expect(revokeSpy).toHaveBeenCalledWith("inv-1");
  });

  it("does not load invitations for members without invitation access", () => {
    currentUserId = "member-user";

    render(<ProjectMembersTab projectId="project-1" />);

    expect(useProjectInvitations).toHaveBeenCalledWith("project-1", false);
    expect(
      screen.getByText("Only owners and managers can view pending invitations."),
    ).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Resend" })).not.toBeInTheDocument();
  });
});
