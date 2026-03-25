import { render, screen } from "@testing-library/react";
import type { ReactNode } from "react";
import { MemoryRouter, Route, Routes } from "react-router";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ProjectLayout } from "./ProjectLayout";
import { useAiPanelStore } from "@/features/ai/store/ai-panel-store";
import { useProject } from "@/features/projects/hooks/useProjects";
import { useProjectWebSocket } from "@/features/projects/hooks/useProjectWebSocket";

vi.mock("@/features/ai", async () => {
  const actual = await vi.importActual<typeof import("@/features/ai")>(
    "@/features/ai",
  );

  return {
    ...actual,
    AiDockedPanel: ({ mode = "docked" }: { mode?: "docked" | "drawer" }) => (
      <div>AI PANEL {mode}</div>
    ),
  };
});

vi.mock("@/shared/hooks/use-mobile", () => ({
  useIsMobile: vi.fn(),
}));

vi.mock("@/shared/ui/resizable", () => ({
  ResizablePanelGroup: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  ResizablePanel: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  ResizableHandle: () => <div>HANDLE</div>,
}));

vi.mock("@/shared/ui/drawer", () => ({
  Drawer: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  DrawerContent: ({ children }: { children: ReactNode }) => <div>{children}</div>,
}));

vi.mock("@/features/projects/hooks/useProjectWebSocket", () => ({
  useProjectWebSocket: vi.fn(),
}));

vi.mock("@/features/projects/hooks/useProjects", () => ({
  useProject: vi.fn(),
}));

import { useIsMobile } from "@/shared/hooks/use-mobile";

function renderLayout() {
  return render(
    <MemoryRouter initialEntries={["/projects/project-1/tasks"]}>
      <Routes>
        <Route path="/projects/:projectId" element={<ProjectLayout />}>
          <Route path=":view" element={<div>PROJECT CONTENT</div>} />
        </Route>
      </Routes>
    </MemoryRouter>,
  );
}

describe("ProjectLayout", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useAiPanelStore.setState({ projects: {} });
    vi.mocked(useIsMobile).mockReturnValue(false);
    vi.mocked(useProject).mockReturnValue({
      error: null,
    } as never);
  });

  it("renders only the project outlet when the AI panel is closed", () => {
    renderLayout();

    expect(screen.getByText("PROJECT CONTENT")).toBeInTheDocument();
    expect(screen.queryByText("AI PANEL docked")).not.toBeInTheDocument();
    expect(useProjectWebSocket).toHaveBeenCalledWith("project-1");
  });

  it("renders the docked AI panel when the project panel state is open", () => {
    useAiPanelStore.getState().setPanelOpen("project-1", true);

    renderLayout();

    expect(screen.getByText("PROJECT CONTENT")).toBeInTheDocument();
    expect(screen.getByText("AI PANEL docked")).toBeInTheDocument();
  });

  it("renders a clear message when the user no longer has project access", () => {
    vi.mocked(useProject).mockReturnValue({
      error: {
        isAxiosError: true,
        response: { status: 403 },
      },
    } as never);

    renderLayout();

    expect(screen.getByText("You no longer have access to this project.")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Back to Projects" })).toHaveAttribute(
      "href",
      "/projects",
    );
  });
});
