import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { ReactNode } from "react";
import { MemoryRouter, Route, Routes } from "react-router";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { AiDockedPanel } from "./AiDockedPanel";
import { useAiPanelStore } from "@/features/ai/store/ai-panel-store";

const mockStreamChat = vi.fn();
const mockEstimateMutateAsync = vi.fn();
const mockSuggestionsRefetch = vi.fn();
const mockUpdateTaskMutateAsync = vi.fn();
const mockCreateDependencyMutateAsync = vi.fn();
const mockToastError = vi.fn();
const mockToastSuccess = vi.fn();
const mockToastMessage = vi.fn();

vi.mock("@/features/ai/api/ai.service", () => ({
  aiService: {
    streamChat: (...args: unknown[]) => mockStreamChat(...args),
  },
}));

vi.mock("@/features/ai/hooks/useAi", () => ({
  useAiEstimate: vi.fn(),
  useAiSuggestions: vi.fn(),
}));

vi.mock("@/features/tasks/hooks/useTasks", () => ({
  useTasks: vi.fn(),
  useUpdateTask: vi.fn(),
}));

vi.mock("@/features/tasks/hooks/useDependencies", () => ({
  useCreateDependency: vi.fn(),
}));

vi.mock("@/shared/ui/scroll-area", () => ({
  ScrollArea: ({ children, className }: { children: ReactNode; className?: string }) => (
    <div className={className}>{children}</div>
  ),
}));

vi.mock("sonner", () => ({
  toast: {
    error: (...args: unknown[]) => mockToastError(...args),
    success: (...args: unknown[]) => mockToastSuccess(...args),
    message: (...args: unknown[]) => mockToastMessage(...args),
  },
}));

import { useAiEstimate, useAiSuggestions } from "@/features/ai/hooks/useAi";
import { useCreateDependency } from "@/features/tasks/hooks/useDependencies";
import { useTasks, useUpdateTask } from "@/features/tasks/hooks/useTasks";

function renderPanel() {
  return render(
    <MemoryRouter initialEntries={["/projects/project-1/tasks"]}>
      <Routes>
        <Route
          path="/projects/:projectId/:view"
          element={<AiDockedPanel projectId="project-1" />}
        />
      </Routes>
    </MemoryRouter>,
  );
}

describe("AiDockedPanel", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useAiPanelStore.setState({ projects: {} });

    vi.mocked(useTasks).mockReturnValue({
      data: {
        items: [
          { id: "task-1", name: "QA regression pass" },
          { id: "task-2", name: "Production release" },
        ],
      },
    } as never);

    vi.mocked(useAiEstimate).mockReturnValue({
      mutateAsync: mockEstimateMutateAsync,
      isPending: false,
    } as never);

    vi.mocked(useAiSuggestions).mockReturnValue({
      data: { suggestions: [] },
      isLoading: false,
      refetch: mockSuggestionsRefetch,
    } as never);

    vi.mocked(useUpdateTask).mockReturnValue({
      mutateAsync: mockUpdateTaskMutateAsync,
      isPending: false,
    } as never);

    vi.mocked(useCreateDependency).mockReturnValue({
      mutateAsync: mockCreateDependencyMutateAsync,
      isPending: false,
    } as never);
  });

  it("renders streamed chat messages and stores the conversation id", async () => {
    const user = userEvent.setup();
    vi.spyOn(crypto, "randomUUID")
      .mockReturnValueOnce("user-message-1")
      .mockReturnValueOnce("assistant-message-1");

    mockStreamChat.mockImplementation(
      async (
        projectId: string,
        body: { message: string },
        onEvent: (event: Record<string, unknown>) => void,
      ) => {
        expect(projectId).toBe("project-1");
        expect(body.message).toBe("What is the project status?");
        onEvent({ type: "start", conversation_id: "conv-1" });
        onEvent({ type: "chunk", content: "Project " });
        onEvent({ type: "chunk", content: "summary" });
        onEvent({ type: "done", message_id: "msg-1" });
      },
    );

    renderPanel();

    await user.type(
      screen.getByPlaceholderText("Ask the assistant about this project..."),
      "What is the project status?",
    );
    await user.click(screen.getByRole("button", { name: "Send" }));

    await waitFor(() => {
      expect(mockStreamChat).toHaveBeenCalledTimes(1);
    });
    await waitFor(() => {
      expect(screen.getByText("Project summary")).toBeInTheDocument();
    });

    expect(screen.getByText("What is the project status?")).toBeInTheDocument();
    expect(useAiPanelStore.getState().projects["project-1"]?.conversationId).toBe(
      "conv-1",
    );
  });

  it("shows a fallback assistant message when the stream returns no chunks", async () => {
    const user = userEvent.setup();
    vi.spyOn(crypto, "randomUUID")
      .mockReturnValueOnce("user-message-2")
      .mockReturnValueOnce("assistant-message-2");

    mockStreamChat.mockResolvedValue(undefined);

    renderPanel();

    await user.type(
      screen.getByPlaceholderText("Ask the assistant about this project..."),
      "Any update?",
    );
    await user.click(screen.getByRole("button", { name: "Send" }));

    await waitFor(() => {
      expect(
        screen.getByText("No response generated for this prompt."),
      ).toBeInTheDocument();
    });
  });

  it("runs estimates for selected tasks and applies the recommended duration", async () => {
    const user = userEvent.setup();

    mockEstimateMutateAsync.mockResolvedValue({
      estimates: [
        {
          task_id: "task-1",
          task_name: "QA regression pass",
          optimistic_minutes: 480,
          likely_minutes: 960,
          pessimistic_minutes: 1440,
          recommended_minutes: 960,
          confidence: 0.72,
          reasoning: "Estimated from comparable rollout work.",
        },
      ],
      usage: { tokens_in: 4, tokens_out: 6 },
    });

    renderPanel();

    await user.click(screen.getByRole("tab", { name: "Estimate" }));
    await user.click(screen.getByLabelText("QA regression pass"));
    await user.click(screen.getByRole("button", { name: "Run Estimate" }));

    await waitFor(() => {
      expect(mockEstimateMutateAsync).toHaveBeenCalledWith({
        task_ids: ["task-1"],
        task_name: undefined,
        task_description: undefined,
        include_reasoning: true,
        ui_context: {
          current_view: "tasks",
          selected_task_ids: ["task-1"],
        },
      });
    });

    expect(
      screen.getByText("Estimated from comparable rollout work."),
    ).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Apply 2d" }));

    expect(mockUpdateTaskMutateAsync).toHaveBeenCalledWith({
      taskId: "task-1",
      data: { duration: 960 },
    });
    expect(mockToastSuccess).toHaveBeenCalledWith(
      "Task duration updated from AI estimate",
    );
  });

  it("applies dependency suggestions and refreshes the suggestions list", async () => {
    const user = userEvent.setup();

    vi.mocked(useAiSuggestions).mockReturnValue({
      data: {
        suggestions: [
          {
            id: "suggestion-1",
            type: "MISSING_DEPENDENCY",
            severity: "MEDIUM",
            title: "Possible missing dependency",
            description: "Release should depend on QA.",
            suggested_action: {
              type: "ADD_DEPENDENCY",
              payload: {
                predecessor_id: "task-1",
                successor_id: "task-2",
                dependency_type: "FS",
              },
            },
          },
        ],
      },
      isLoading: false,
      refetch: mockSuggestionsRefetch,
    } as never);

    useAiPanelStore.getState().setActiveTab("project-1", "suggestions");

    renderPanel();

    await user.click(screen.getByRole("button", { name: "Apply" }));

    expect(mockCreateDependencyMutateAsync).toHaveBeenCalledWith({
      predecessor_id: "task-1",
      successor_id: "task-2",
      type: "FS",
    });
    expect(mockToastSuccess).toHaveBeenCalledWith("Suggestion applied");
    expect(mockSuggestionsRefetch).toHaveBeenCalledTimes(1);
  });
});
