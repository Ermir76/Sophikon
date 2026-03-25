import { act, renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import type { ReactNode } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import {
  projectMemberKeys,
  useAcceptProjectInvitation,
  useInviteProjectMember,
  useProjectMembers,
} from "@/features/projects/hooks/useProjectMembers";
import { orgKeys } from "@/features/organizations";
import { projectKeys } from "@/features/projects/hooks/useProjects";

vi.mock("@/features/projects/api/project-members.service", () => ({
  projectMembersService: {
    listMembers: vi.fn(),
    inviteMember: vi.fn(),
    acceptInvitation: vi.fn(),
  },
}));

import { projectMembersService } from "@/features/projects/api/project-members.service";

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });

  const wrapper = ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );

  return { queryClient, wrapper };
}

describe("useProjectMembers hooks", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("loads project members", async () => {
    vi.mocked(projectMembersService.listMembers).mockResolvedValue({
      items: [
        {
          id: "m1",
          project_id: "p1",
          user_id: "u1",
          role: "owner",
          joined_at: "2026-03-01T00:00:00Z",
          updated_at: "2026-03-01T00:00:00Z",
          user_email: "owner@example.com",
        },
      ],
      total: 1,
      page: 1,
      per_page: 20,
      total_pages: 1,
    });

    const { wrapper } = createWrapper();
    const { result } = renderHook(() => useProjectMembers("p1"), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(projectMembersService.listMembers).toHaveBeenCalledWith("p1");
  });

  it("invalidates invitations query after invite", async () => {
    vi.mocked(projectMembersService.inviteMember).mockResolvedValue({
      id: "inv1",
      project_id: "p1",
      invited_by_id: "u1",
      role: "member",
      email: "new@example.com",
      expires_at: "2026-03-12T00:00:00Z",
      accepted_at: null,
      is_revoked: false,
      created_at: "2026-03-05T00:00:00Z",
    });

    const { queryClient, wrapper } = createWrapper();
    const invalidateSpy = vi.spyOn(queryClient, "invalidateQueries");
    const { result } = renderHook(() => useInviteProjectMember("p1"), { wrapper });

    await act(async () => {
      await result.current.mutateAsync({
        email: "new@example.com",
        role: "member",
      });
    });

    expect(projectMembersService.inviteMember).toHaveBeenCalledWith("p1", {
      email: "new@example.com",
      role: "member",
    });
    expect(invalidateSpy).toHaveBeenCalledWith({
      queryKey: projectMemberKeys.invitations("p1"),
    });
  });

  it("accepts invitation token", async () => {
    vi.mocked(projectMembersService.acceptInvitation).mockResolvedValue({
      project_id: "p1",
      member_id: "m1",
    });

    const { queryClient, wrapper } = createWrapper();
    const invalidateSpy = vi.spyOn(queryClient, "invalidateQueries");
    const { result } = renderHook(() => useAcceptProjectInvitation(), { wrapper });

    await act(async () => {
      await result.current.mutateAsync({ token: "abc" });
    });

    expect(projectMembersService.acceptInvitation).toHaveBeenCalledWith({
      token: "abc",
    });
    expect(invalidateSpy).toHaveBeenCalledWith({
      queryKey: orgKeys.list,
    });
    expect(invalidateSpy).toHaveBeenCalledWith({
      queryKey: projectKeys.all,
    });
  });
});
