import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router";
import { beforeEach, describe, expect, it, vi } from "vitest";

import ProjectSettingsPage from "@/features/projects/pages/ProjectSettingsPage";

vi.mock("@/features/projects/hooks/useProjects", () => ({
  useProject: vi.fn(),
  useUpdateProject: vi.fn(),
  useDeleteProject: vi.fn(),
}));

vi.mock("@/features/projects/components/ProjectMembersTab", () => ({
  ProjectMembersTab: ({ projectId }: { projectId: string }) => (
    <div>Members panel for {projectId}</div>
  ),
}));

import {
  useDeleteProject,
  useProject,
  useUpdateProject,
} from "@/features/projects/hooks/useProjects";

describe("ProjectSettingsPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(useProject).mockReturnValue({
      data: {
        id: "project-1",
        name: "Alpha",
        description: "Desc",
        color: null,
      },
      isLoading: false,
      isError: false,
      refetch: vi.fn(),
    } as never);
    vi.mocked(useUpdateProject).mockReturnValue({
      mutateAsync: vi.fn(),
      isPending: false,
    } as never);
    vi.mocked(useDeleteProject).mockReturnValue({
      mutateAsync: vi.fn(),
      isPending: false,
    } as never);
  });

  it("renders general tab by default and shows members tab content when selected", async () => {
    render(
      <MemoryRouter initialEntries={["/projects/project-1/settings"]}>
        <Routes>
          <Route path="/projects/:projectId/settings" element={<ProjectSettingsPage />} />
        </Routes>
      </MemoryRouter>,
    );

    expect(screen.getByText("General Information")).toBeInTheDocument();
    expect(screen.queryByText("Members panel for project-1")).not.toBeInTheDocument();

    const user = userEvent.setup();
    await user.click(screen.getByRole("tab", { name: "Members" }));
    await waitFor(() => {
      expect(screen.getByText("Members panel for project-1")).toBeInTheDocument();
    });
  });
});
