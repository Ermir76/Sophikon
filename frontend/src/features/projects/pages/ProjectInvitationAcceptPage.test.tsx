import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { useEffect } from "react";
import { MemoryRouter, Route, Routes } from "react-router";
import { useNavigate } from "react-router";
import { beforeEach, describe, expect, it, vi } from "vitest";

import ProjectInvitationAcceptPage from "@/features/projects/pages/ProjectInvitationAcceptPage";

const setActiveOrg = vi.fn();

vi.mock("@/features/projects/hooks/useProjectMembers", () => ({
  useAcceptProjectInvitation: vi.fn(),
}));

vi.mock("@/features/projects/api/project.service", () => ({
  projectService: {
    get: vi.fn(),
  },
}));

vi.mock("@/features/organizations", () => ({
  useOrganizations: vi.fn(),
  useOrgStore: vi.fn(),
}));

vi.mock("sonner", () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
  },
}));

import { useAcceptProjectInvitation } from "@/features/projects/hooks/useProjectMembers";
import { projectService } from "@/features/projects/api/project.service";
import { useOrganizations, useOrgStore } from "@/features/organizations";
import { toast } from "sonner";

function ReviewModeRedirect() {
  const navigate = useNavigate();

  useEffect(() => {
    navigate("/project-invitations/accept?invitation_id=review-invite-1", {
      state: {
        review: true,
        title: "Invited to Project Alpha",
        message: "Owner invited you as a member.",
      },
      replace: true,
    });
  }, [navigate]);

  return null;
}

describe("ProjectInvitationAcceptPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(useOrganizations).mockReturnValue({
      data: {
        items: [
          {
            id: "org-1",
            name: "Invited Org",
          },
        ],
      },
    } as never);
    vi.mocked(useOrgStore).mockImplementation((selector) => selector({
      activeOrgId: "personal-org",
      setActiveOrg,
    } as never));
  });

  it("switches to the invited organization only after clicking open project", async () => {
    const user = userEvent.setup();
    const mutateAsync = vi.fn().mockResolvedValue({
      project_id: "project-1",
      member_id: "member-1",
    });
    vi.mocked(projectService.get).mockResolvedValue({
      id: "project-1",
      organization_id: "org-1",
      name: "Project 1",
    } as never);
    vi.mocked(useAcceptProjectInvitation).mockReturnValue({
      mutateAsync,
    } as never);

    render(
      <MemoryRouter initialEntries={["/project-invitations/accept?token=abc-success"]}>
        <Routes>
          <Route path="/project-invitations/accept" element={<ProjectInvitationAcceptPage />} />
          <Route path="/projects/:projectId/tasks" element={<div>PROJECT TASKS</div>} />
        </Routes>
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(screen.getByText("Invitation Accepted")).toBeInTheDocument();
      expect(
        screen.getByText("You have accepted the invitation. Go to the project page."),
      ).toBeInTheDocument();
    });
    expect(mutateAsync).toHaveBeenCalledWith({ token: "abc-success" });
    expect(projectService.get).not.toHaveBeenCalled();
    expect(setActiveOrg).not.toHaveBeenCalled();
    expect(toast.success).not.toHaveBeenCalled();

    await user.click(screen.getByRole("button", { name: "Go to Project" }));

    await waitFor(() => {
      expect(screen.getByText("PROJECT TASKS")).toBeInTheDocument();
    });
    expect(projectService.get).toHaveBeenCalledWith("project-1");
    expect(setActiveOrg).toHaveBeenCalledWith("org-1");
    expect(toast.success).toHaveBeenCalledWith(
      "Switched to Invited Org",
      {
        description: "Opening your invited project.",
      },
    );
  });

  it("shows invalid token error state", async () => {
    const user = userEvent.setup();
    const mutateAsync = vi.fn()
      .mockRejectedValueOnce(new Error("Invalid token"))
      .mockResolvedValueOnce({
        project_id: "project-1",
        member_id: "member-1",
      });
    vi.mocked(useAcceptProjectInvitation).mockReturnValue({
      mutateAsync,
    } as never);

    render(
      <MemoryRouter initialEntries={["/project-invitations/accept?token=abc-error"]}>
        <Routes>
          <Route path="/project-invitations/accept" element={<ProjectInvitationAcceptPage />} />
        </Routes>
      </MemoryRouter>,
    );

    expect(screen.getByText("Accepting your invitation...")).toBeInTheDocument();
    await waitFor(() => expect(mutateAsync).toHaveBeenCalledWith({ token: "abc-error" }));
    const tokenAlert = screen.getByRole("alert");
    expect(tokenAlert).toHaveTextContent("Invalid token");
    expect(mutateAsync).toHaveBeenCalledTimes(1);

    await user.click(screen.getByRole("button", { name: "Try Again" }));

    await waitFor(() => {
      expect(mutateAsync).toHaveBeenCalledTimes(2);
      expect(screen.getByText("Invitation Accepted")).toBeInTheDocument();
    });
  });

  it("shows a fallback open-project button when switching context fails", async () => {
    const user = userEvent.setup();
    const mutateAsync = vi.fn().mockResolvedValue({
      project_id: "project-1",
      member_id: "member-1",
    });
    vi.mocked(projectService.get).mockRejectedValue(new Error("Project lookup failed"));
    vi.mocked(useAcceptProjectInvitation).mockReturnValue({
      mutateAsync,
    } as never);

    render(
      <MemoryRouter initialEntries={["/project-invitations/accept?token=abc-fallback"]}>
        <Routes>
          <Route path="/project-invitations/accept" element={<ProjectInvitationAcceptPage />} />
        </Routes>
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(screen.getByText("Invitation Accepted")).toBeInTheDocument();
    });
    expect(screen.getByRole("button", { name: "Go to Project" })).toBeInTheDocument();
    expect(screen.queryByText("Project lookup failed")).not.toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Go to Project" }));

    await waitFor(() => {
      expect(screen.getByText("Project lookup failed")).toBeInTheDocument();
    });
    expect(screen.getByText("Project lookup failed")).toBeInTheDocument();
    expect(toast.error).toHaveBeenCalledWith("Failed to open project", {
      description: "Project lookup failed",
    });
  });

  it("shows missing invitation details with dashboard recovery action", async () => {
    const user = userEvent.setup();
    vi.mocked(useAcceptProjectInvitation).mockReturnValue({
      mutateAsync: vi.fn(),
    } as never);

    render(
      <MemoryRouter initialEntries={["/project-invitations/accept"]}>
        <Routes>
          <Route path="/project-invitations/accept" element={<ProjectInvitationAcceptPage />} />
          <Route path="/" element={<div>DASHBOARD</div>} />
        </Routes>
      </MemoryRouter>,
    );

    const missingDetailsAlert = screen.getByRole("alert");
    expect(missingDetailsAlert).toHaveTextContent("missing required details");
    await user.click(screen.getByRole("link", { name: "Back to Dashboard" }));
    expect(screen.getByText("DASHBOARD")).toBeInTheDocument();
  });

  it("accepts invitations opened from bell notifications by invitation id", async () => {
    const mutateAsync = vi.fn().mockResolvedValue({
      project_id: "project-1",
      member_id: "member-1",
    });
    vi.mocked(useAcceptProjectInvitation).mockReturnValue({
      mutateAsync,
    } as never);

    render(
      <MemoryRouter initialEntries={["/project-invitations/accept?invitation_id=invite-1"]}>
        <Routes>
          <Route path="/project-invitations/accept" element={<ProjectInvitationAcceptPage />} />
        </Routes>
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(mutateAsync).toHaveBeenCalledWith({ invitation_id: "invite-1" });
    });
    expect(screen.getByText("Invitation Accepted")).toBeInTheDocument();
  });

  it("shows review details and waits for explicit confirmation before accepting", async () => {
    const user = userEvent.setup();
    const mutateAsync = vi.fn().mockResolvedValue({
      project_id: "project-1",
      member_id: "member-1",
    });
    vi.mocked(useAcceptProjectInvitation).mockReturnValue({
      mutateAsync,
    } as never);

    render(
      <MemoryRouter initialEntries={["/review"]}>
        <Routes>
          <Route path="/review" element={<ReviewModeRedirect />} />
          <Route path="/project-invitations/accept" element={<ProjectInvitationAcceptPage />} />
        </Routes>
      </MemoryRouter>,
    );

    expect(screen.getByText("Invited to Project Alpha")).toBeInTheDocument();
    expect(screen.getByText("Owner invited you as a member.")).toBeInTheDocument();
    expect(mutateAsync).not.toHaveBeenCalled();

    await user.click(screen.getByRole("button", { name: "Accept Invitation" }));

    await waitFor(() => {
      expect(mutateAsync).toHaveBeenCalledWith({ invitation_id: "review-invite-1" });
      expect(screen.getByText("Invitation Accepted")).toBeInTheDocument();
    });
  });

  it("uses explicit cancel navigation from review mode", async () => {
    const user = userEvent.setup();
    const mutateAsync = vi.fn();
    vi.mocked(useAcceptProjectInvitation).mockReturnValue({
      mutateAsync,
    } as never);

    render(
      <MemoryRouter initialEntries={["/review"]}>
        <Routes>
          <Route path="/" element={<div>DASHBOARD</div>} />
          <Route path="/review" element={<ReviewModeRedirect />} />
          <Route path="/project-invitations/accept" element={<ProjectInvitationAcceptPage />} />
        </Routes>
      </MemoryRouter>,
    );

    expect(screen.getByText("Invited to Project Alpha")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Cancel" }));
    expect(screen.getByText("DASHBOARD")).toBeInTheDocument();
    expect(mutateAsync).not.toHaveBeenCalled();
  });

  it("renders accepted state from navigation state without re-accepting", async () => {
    const mutateAsync = vi.fn();
    vi.mocked(useAcceptProjectInvitation).mockReturnValue({
      mutateAsync,
    } as never);

    render(
      <MemoryRouter
        initialEntries={[{
          pathname: "/project-invitations/accept",
          search: "?invitation_id=invite-1",
          state: {
            acceptedInvitation: {
              project_id: "project-1",
              member_id: "member-1",
            },
          },
        }]}
      >
        <Routes>
          <Route path="/project-invitations/accept" element={<ProjectInvitationAcceptPage />} />
        </Routes>
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(screen.getByText("Invitation Accepted")).toBeInTheDocument();
    });
    expect(mutateAsync).not.toHaveBeenCalled();
  });
});
