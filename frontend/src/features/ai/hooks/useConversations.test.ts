import { createElement, type ReactNode } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { renderHook, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { useConversation, useConversations } from "./useConversations";

vi.mock("@/features/ai/api/ai.service", () => ({
  aiService: {
    getConversations: vi.fn(),
    getConversation: vi.fn(),
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

describe("useConversations", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("fetches the conversation list for a project", async () => {
    const conversations = [
      {
        id: "conv-1",
        title: "Sprint planning",
        status: "idle",
        mode: "chat",
        created_at: "2026-03-17T10:00:00Z",
        updated_at: "2026-03-17T10:05:00Z",
      },
    ];
    vi.mocked(aiService.getConversations).mockResolvedValue(
      conversations as never,
    );

    const { result } = renderHook(() => useConversations("project-1"), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(aiService.getConversations).toHaveBeenCalledWith("project-1");
    expect(result.current.data).toEqual(conversations);
  });

  it("stays idle when projectId is undefined", () => {
    const { result } = renderHook(() => useConversations(undefined), {
      wrapper: createWrapper(),
    });

    expect(result.current.fetchStatus).toBe("idle");
    expect(aiService.getConversations).not.toHaveBeenCalled();
  });
});

describe("useConversation", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("fetches a single conversation by id", async () => {
    const detail = {
      id: "conv-1",
      title: "Sprint planning",
      status: "idle",
      mode: "chat",
      messages: [
        {
          id: "m-1",
          role: "user",
          content: "Hi",
          created_at: "2026-03-17T10:00:00Z",
        },
      ],
    };
    vi.mocked(aiService.getConversation).mockResolvedValue(detail as never);

    const { result } = renderHook(
      () => useConversation("project-1", "conv-1"),
      { wrapper: createWrapper() },
    );

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(aiService.getConversation).toHaveBeenCalledWith(
      "project-1",
      "conv-1",
    );
    expect(result.current.data).toEqual(detail);
  });

  it("stays idle when projectId or conversationId is undefined", () => {
    const { result: noProject } = renderHook(
      () => useConversation(undefined, "conv-1"),
      { wrapper: createWrapper() },
    );
    const { result: noConv } = renderHook(
      () => useConversation("project-1", undefined),
      { wrapper: createWrapper() },
    );

    expect(noProject.current.fetchStatus).toBe("idle");
    expect(noConv.current.fetchStatus).toBe("idle");
    expect(aiService.getConversation).not.toHaveBeenCalled();
  });
});
