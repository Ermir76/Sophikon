import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("@/shared/api/api", () => ({
  api: {
    get: vi.fn(),
    post: vi.fn(),
  },
}));

vi.mock("axios", () => ({
  default: {
    create: vi.fn(() => ({
      get: vi.fn(),
      post: vi.fn(),
      interceptors: {
        request: { use: vi.fn(), eject: vi.fn() },
        response: { use: vi.fn(), eject: vi.fn() },
      },
    })),
    post: vi.fn(),
  },
}));

vi.mock("@/features/auth/store/auth-store", () => ({
  useAuthStore: {
    setState: vi.fn(),
  },
}));

vi.mock("@/features/auth/lib/auth", () => ({
  clearAuth: vi.fn(),
}));

import axios from "axios";

import { api } from "@/shared/api/api";
import { aiService } from "./ai.service";

function createStreamResponse(
  chunks: string[],
  overrides: Partial<Response> = {},
): Response {
  let index = 0;
  const encoder = new TextEncoder();
  const body = new ReadableStream<Uint8Array>({
    pull(controller) {
      if (index >= chunks.length) {
        controller.close();
        return;
      }
      controller.enqueue(encoder.encode(chunks[index]));
      index += 1;
    },
  });

  return {
    ok: true,
    status: 200,
    body,
    ...overrides,
  } as Response;
}

describe("aiService REST methods", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("resolvePlanApproval posts approved=true with no feedback", async () => {
    vi.mocked(api.post).mockResolvedValue({ data: { ok: true } } as never);

    await aiService.resolvePlanApproval("project-1", "conv-1", true);

    expect(api.post).toHaveBeenCalledWith(
      "/projects/project-1/ai/plan-approval/conv-1",
      { approved: true, feedback: null },
    );
  });

  it("resolvePlanApproval posts approved=false with feedback", async () => {
    vi.mocked(api.post).mockResolvedValue({ data: { ok: true } } as never);

    await aiService.resolvePlanApproval(
      "project-1",
      "conv-1",
      false,
      "Do it differently",
    );

    expect(api.post).toHaveBeenCalledWith(
      "/projects/project-1/ai/plan-approval/conv-1",
      { approved: false, feedback: "Do it differently" },
    );
  });

  it("getConversations returns the conversations array", async () => {
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
    vi.mocked(api.get).mockResolvedValue({ data: { conversations } } as never);

    const result = await aiService.getConversations("project-1");

    expect(api.get).toHaveBeenCalledWith(
      "/projects/project-1/ai/conversations",
    );
    expect(result).toEqual(conversations);
  });

  it("getConversation returns the full conversation detail", async () => {
    const detail = {
      id: "conv-1",
      title: "Sprint planning",
      status: "idle",
      mode: "chat",
      messages: [
        { id: "m-1", role: "user", content: "Hi", created_at: "2026-03-17T10:00:00Z" },
      ],
    };
    vi.mocked(api.get).mockResolvedValue({ data: detail } as never);

    const result = await aiService.getConversation("project-1", "conv-1");

    expect(api.get).toHaveBeenCalledWith(
      "/projects/project-1/ai/conversations/conv-1",
    );
    expect(result).toEqual(detail);
  });
});

describe("aiService.streamChat", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.stubGlobal("fetch", vi.fn());
  });

  it("refreshes the session and retries once after a 401 response", async () => {
    const onEvent = vi.fn();
    const fetchMock = vi.mocked(fetch);

    fetchMock
      .mockResolvedValueOnce({
        ok: false,
        status: 401,
        body: null,
      } as Response)
      .mockResolvedValueOnce(
        createStreamResponse([
          'data: {"type":"chunk","content":"Recovered"}\n\n',
        ]),
      );

    vi.mocked(axios.post).mockResolvedValue({} as never);

    await aiService.streamChat(
      "project-1",
      { message: "Status?" },
      onEvent,
    );

    expect(axios.post).toHaveBeenCalledWith(
      "/api/v1/auth/refresh",
      {},
      { withCredentials: true },
    );
    expect(fetchMock).toHaveBeenCalledTimes(2);
    expect(onEvent).toHaveBeenCalledWith({
      type: "chunk",
      content: "Recovered",
    });
  });

  it("emits an error event when the streaming payload is malformed", async () => {
    const onEvent = vi.fn();

    vi.mocked(fetch).mockResolvedValue(
      createStreamResponse(['data: {"type":"chunk"\n\n']),
    );

    await aiService.streamChat(
      "project-1",
      { message: "Status?" },
      onEvent,
    );

    expect(onEvent).toHaveBeenCalledWith({
      type: "error",
      error: "Malformed streaming response",
    });
  });

  it("throws when the chat stream has no response body", async () => {
    vi.mocked(fetch).mockResolvedValue({
      ok: true,
      status: 200,
      body: null,
    } as Response);

    await expect(
      aiService.streamChat("project-1", { message: "Status?" }, vi.fn()),
    ).rejects.toThrow("AI chat stream is not available");
  });
});
