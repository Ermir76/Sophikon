import { createElement, type ReactNode } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { renderHook, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { useAiEstimate, useAiSuggestions } from "./useAi";

vi.mock("@/features/ai/api/ai.service", () => ({
  aiService: {
    estimate: vi.fn(),
    suggestions: vi.fn(),
  },
}));

import { aiService } from "@/features/ai/api/ai.service";

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });

  return ({ children }: { children: ReactNode }) =>
    createElement(QueryClientProvider, { client: queryClient }, children);
}

describe("useAi hooks", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("useAiEstimate calls the estimate service for the active project", async () => {
    const mockResponse = {
      estimates: [
        {
          task_name: "Launch checklist",
          optimistic_minutes: 240,
          likely_minutes: 480,
          pessimistic_minutes: 720,
          recommended_minutes: 480,
          confidence: 0.7,
        },
      ],
      usage: { tokens_in: 5, tokens_out: 8 },
    };
    vi.mocked(aiService.estimate).mockResolvedValue(mockResponse as never);

    const { result } = renderHook(() => useAiEstimate("project-1"), {
      wrapper: createWrapper(),
    });

    result.current.mutate({
      task_name: "Launch checklist",
      include_reasoning: true,
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(aiService.estimate).toHaveBeenCalledWith("project-1", {
      task_name: "Launch checklist",
      include_reasoning: true,
    });
    expect(result.current.data).toEqual(mockResponse);
  });

  it("useAiEstimate surfaces an error when no project is selected", async () => {
    const { result } = renderHook(() => useAiEstimate(undefined), {
      wrapper: createWrapper(),
    });

    result.current.mutate({ task_name: "Backlog review" });

    await waitFor(() => expect(result.current.isError).toBe(true));
    expect(result.current.error?.message).toBe("No project selected");
    expect(aiService.estimate).not.toHaveBeenCalled();
  });

  it("useAiSuggestions fetches suggestions for the active project", async () => {
    const mockResponse = {
      suggestions: [
        {
          id: "s-1",
          type: "OVERDUE_TASK",
          severity: "HIGH",
          title: "Task is overdue",
          description: "Review launch plan",
        },
      ],
      usage: { tokens_in: 3, tokens_out: 4 },
    };
    vi.mocked(aiService.suggestions).mockResolvedValue(mockResponse as never);

    const { result } = renderHook(() => useAiSuggestions("project-1", 8), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(aiService.suggestions).toHaveBeenCalledWith("project-1", 8);
    expect(result.current.data).toEqual(mockResponse);
  });

  it("useAiSuggestions stays idle when disabled or missing a project", async () => {
    const { result: noProject } = renderHook(() => useAiSuggestions(undefined, 5), {
      wrapper: createWrapper(),
    });
    const { result: disabled } = renderHook(
      () => useAiSuggestions("project-1", 5, false),
      {
        wrapper: createWrapper(),
      },
    );

    expect(noProject.current.fetchStatus).toBe("idle");
    expect(disabled.current.fetchStatus).toBe("idle");
    expect(aiService.suggestions).not.toHaveBeenCalled();
  });
});
