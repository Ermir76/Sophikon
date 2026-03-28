import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { createElement, type ReactNode } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter, Route, Routes } from "react-router";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { AiDockedPanel } from "./AiDockedPanel";
import { useAiPanelStore } from "@/features/ai/store/ai-panel-store";

const mockStreamChat = vi.fn();
const mockEstimateMutateAsync = vi.fn();
const mockSuggestionsRefetch = vi.fn();
const mockUpdateTaskMutateAsync = vi.fn();
const mockCreateDependencyMutateAsync = vi.fn();
const mockUpdateAiPreferencesMutate = vi.fn();
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
  useApprovePlan: vi.fn(),
}));

vi.mock("@/features/ai/hooks/useConversations", () => ({
  useConversations: vi.fn(),
}));

vi.mock("@/features/tasks/hooks/useTasks", () => ({
  useTasks: vi.fn(),
  useUpdateTask: vi.fn(),
}));

vi.mock("@/features/tasks/hooks/useDependencies", () => ({
  useCreateDependency: vi.fn(),
}));

vi.mock("@/features/auth/hooks/useAuth", () => ({
  useAiPreferences: vi.fn(),
  useUpdateAiPreferences: vi.fn(),
}));

vi.mock("@/shared/ui/scroll-area", () => ({
  ScrollArea: ({ children, className }: { children: ReactNode; className?: string }) => (
    <div className={className}>{children}</div>
  ),
}));

vi.mock("@/shared/ui/select", async () => {
  const React = await import("react");
  const ctx = React.createContext<{
    value?: string;
    onValueChange?: (value: string) => void;
    disabled?: boolean;
  }>({});

  const Select = ({
    value,
    onValueChange,
    disabled,
    children,
  }: {
    value?: string;
    onValueChange?: (value: string) => void;
    disabled?: boolean;
    children: ReactNode;
  }) => (
    <ctx.Provider value={{ value, onValueChange, disabled }}>{children}</ctx.Provider>
  );

  const SelectTrigger = ({
    children,
    className,
  }: {
    children: ReactNode;
    className?: string;
  }) => <div className={className}>{children}</div>;

  const SelectValue = ({ placeholder }: { placeholder?: string }) => <span>{placeholder}</span>;

  const SelectContent = ({ children }: { children: ReactNode }) => {
    const context = React.useContext(ctx);
    const options: Array<{ value: string; label: string; disabled?: boolean }> = [];

    React.Children.forEach(children, (child) => {
      if (!React.isValidElement(child)) return;
      options.push({
        value: String(child.props.value),
        label: typeof child.props.children === "string" ? child.props.children : String(child.props.children),
        disabled: Boolean(child.props.disabled),
      });
    });

    return (
      <select
        aria-label="mock-select"
        value={context.value ?? ""}
        disabled={context.disabled}
        onChange={(event) => context.onValueChange?.(event.target.value)}
      >
        {options.map((option) => (
          <option key={option.value} value={option.value} disabled={option.disabled}>
            {option.label}
          </option>
        ))}
      </select>
    );
  };

  const SelectItem = ({
    value,
    children,
    disabled,
  }: {
    value: string;
    children: ReactNode;
    disabled?: boolean;
  }) => (
    <option value={value} disabled={disabled}>
      {children}
    </option>
  );

  return {
    Select,
    SelectTrigger,
    SelectValue,
    SelectContent,
    SelectItem,
  };
});

vi.mock("sonner", () => ({
  toast: {
    error: (...args: unknown[]) => mockToastError(...args),
    success: (...args: unknown[]) => mockToastSuccess(...args),
    message: (...args: unknown[]) => mockToastMessage(...args),
  },
}));

import { useAiEstimate, useAiSuggestions, useApprovePlan } from "@/features/ai/hooks/useAi";
import { useConversations } from "@/features/ai/hooks/useConversations";
import { useAiPreferences, useUpdateAiPreferences } from "@/features/auth/hooks/useAuth";
import { useCreateDependency } from "@/features/tasks/hooks/useDependencies";
import { useTasks, useUpdateTask } from "@/features/tasks/hooks/useTasks";

function renderPanel(options?: { isAgentEnabled?: boolean }) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  const isAgentEnabled = options?.isAgentEnabled ?? true;
  return render(
    createElement(
      QueryClientProvider,
      { client: queryClient },
      <MemoryRouter initialEntries={["/projects/project-1/tasks"]}>
        <Routes>
          <Route
            path="/projects/:projectId/:view"
            element={
              <AiDockedPanel
                projectId="project-1"
                isAgentEnabled={isAgentEnabled}
              />
            }
          />
        </Routes>
      </MemoryRouter>,
    ),
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

    vi.mocked(useAiPreferences).mockReturnValue({
      data: {
        provider: "openai",
        model: "gpt-5-mini",
        defaults: {
          provider: "openai",
          model: "gpt-5-mini",
          mode: "live",
        },
        providers: [
          {
            provider_id: "openai",
            display_name: "OpenAI",
            requires_env_key: "OPENAI_API_KEY",
            available: true,
            models: [
              { model_id: "gpt-5-mini", label: "GPT-5 mini", recommended: true },
              { model_id: "gpt-5", label: "GPT-5", recommended: false },
            ],
          },
          {
            provider_id: "gemini",
            display_name: "Google Gemini",
            requires_env_key: "GEMINI_API_KEY",
            available: false,
            models: [{ model_id: "gemini-2.5-flash", label: "Gemini 2.5 Flash", recommended: true }],
          },
        ],
        auto_approve: {},
      },
      isLoading: false,
      isError: false,
      error: null,
      refetch: vi.fn(),
    } as never);

    vi.mocked(useUpdateAiPreferences).mockReturnValue({
      mutate: mockUpdateAiPreferencesMutate,
      isPending: false,
      isError: false,
      error: null,
    } as never);

    vi.mocked(useApprovePlan).mockReturnValue({
      mutate: vi.fn(),
      isPending: false,
    } as never);

    vi.mocked(useConversations).mockReturnValue({
      data: [],
    } as never);
  });

  it("renders streamed chat messages and stores the conversation id", async () => {
    const user = userEvent.setup();
    vi.spyOn(crypto, "randomUUID")
      .mockReturnValueOnce("11111111-1111-1111-1111-111111111111")
      .mockReturnValueOnce("22222222-2222-2222-2222-222222222222");

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
      .mockReturnValueOnce("33333333-3333-3333-3333-333333333333")
      .mockReturnValueOnce("44444444-4444-4444-4444-444444444444");

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

  it("patches AI preferences when model selection changes", async () => {
    const user = userEvent.setup();
    renderPanel();

    const selects = screen.getAllByLabelText("mock-select");
    await user.selectOptions(selects[1], "gpt-5");

    expect(mockUpdateAiPreferencesMutate).toHaveBeenCalledWith(
      { model: "gpt-5" },
      expect.any(Object),
    );
  });

  it("shows disabled state when the project AI agent is disabled", async () => {
    renderPanel({ isAgentEnabled: false });

    expect(
      screen.getByText(
        "AI agent is disabled for this project. Enable it in Project Settings to continue.",
      ),
    ).toBeInTheDocument();
    expect(
      screen.getByPlaceholderText("Ask the assistant about this project..."),
    ).toBeDisabled();
    expect(screen.getByRole("button", { name: "Send" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "New" })).toBeDisabled();
  });
});
