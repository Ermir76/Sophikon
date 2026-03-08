import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router";
import { beforeEach, describe, expect, it, vi } from "vitest";

import ProjectInvitationAcceptPage from "@/features/projects/pages/ProjectInvitationAcceptPage";

vi.mock("@/features/projects/hooks/useProjectMembers", () => ({
  useAcceptProjectInvitation: vi.fn(),
}));

import { useAcceptProjectInvitation } from "@/features/projects/hooks/useProjectMembers";

describe("ProjectInvitationAcceptPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("shows success state and project link", () => {
    vi.mocked(useAcceptProjectInvitation).mockReturnValue({
      mutate: vi.fn(),
      isPending: false,
      isSuccess: true,
      isError: false,
      data: { project_id: "project-1", member_id: "member-1" },
    } as never);

    render(
      <MemoryRouter initialEntries={["/project-invitations/accept?token=abc"]}>
        <Routes>
          <Route path="/project-invitations/accept" element={<ProjectInvitationAcceptPage />} />
        </Routes>
      </MemoryRouter>,
    );

    expect(screen.getByText("Invitation accepted successfully.")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Open Project" })).toHaveAttribute(
      "href",
      "/projects/project-1/tasks",
    );
  });

  it("shows invalid token error state", async () => {
    const mutateSpy = vi.fn();
    vi.mocked(useAcceptProjectInvitation).mockReturnValue({
      mutate: mutateSpy,
      isPending: false,
      isSuccess: false,
      isError: true,
      error: new Error("Invalid token"),
    } as never);

    render(
      <MemoryRouter initialEntries={["/project-invitations/accept?token=abc"]}>
        <Routes>
          <Route path="/project-invitations/accept" element={<ProjectInvitationAcceptPage />} />
        </Routes>
      </MemoryRouter>,
    );

    await waitFor(() => expect(mutateSpy).toHaveBeenCalledWith({ token: "abc" }));
    expect(screen.getByText("Invalid token")).toBeInTheDocument();
  });

  it("shows missing token message", () => {
    vi.mocked(useAcceptProjectInvitation).mockReturnValue({
      mutate: vi.fn(),
      isPending: false,
      isSuccess: false,
      isError: false,
    } as never);

    render(
      <MemoryRouter initialEntries={["/project-invitations/accept"]}>
        <Routes>
          <Route path="/project-invitations/accept" element={<ProjectInvitationAcceptPage />} />
        </Routes>
      </MemoryRouter>,
    );

    expect(screen.getByText("Missing invitation token.")).toBeInTheDocument();
  });
});
