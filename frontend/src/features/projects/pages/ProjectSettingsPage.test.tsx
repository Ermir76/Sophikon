import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router";
import { beforeEach, describe, expect, it, vi } from "vitest";

import ProjectSettingsPage from "@/features/projects/pages/ProjectSettingsPage";
const mockUpdateProjectMutateAsync = vi.fn();

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
        settings: {
          auto_calculate: true,
          hours_per_day: 8,
          hours_per_week: 40,
          days_per_month: 20,
          first_day_of_week: 1,
          status_thresholds: { IN_PROGRESS: 1, IN_REVIEW: 80, DONE: 100 },
        },
      },
      isLoading: false,
      isError: false,
      refetch: vi.fn(),
    } as never);
    vi.mocked(useUpdateProject).mockReturnValue({
      mutateAsync: mockUpdateProjectMutateAsync,
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

  it("saves review threshold in project settings payload", async () => {
    render(
      <MemoryRouter initialEntries={["/projects/project-1/settings"]}>
        <Routes>
          <Route path="/projects/:projectId/settings" element={<ProjectSettingsPage />} />
        </Routes>
      </MemoryRouter>,
    );

    const user = userEvent.setup();
    const reviewThresholdInput = screen.getByLabelText("Review Threshold (%)");
    await user.clear(reviewThresholdInput);
    await user.type(reviewThresholdInput, "85");
    await user.click(screen.getByRole("button", { name: "Save Changes" }));

    await waitFor(() => {
      expect(mockUpdateProjectMutateAsync).toHaveBeenCalledWith(
        expect.objectContaining({
          settings: {
            status_thresholds: {
              IN_REVIEW: 85,
            },
          },
        }),
      );
    });
  });
});
