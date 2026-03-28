import { api } from "@/shared/api/api";
import axios from "axios";
import { useAuthStore } from "@/features/auth";
import type {
  AiChatEvent,
  AiChatRequest,
  AiEstimateRequest,
  AiEstimateResponse,
  AiSuggestionsResponse,
  ConversationDetail,
  ConversationSummary,
} from "@/features/ai/types";

const API_PREFIX = "/api/v1";

async function openChatStream(
  projectId: string,
  body: AiChatRequest,
): Promise<Response> {
  return fetch(`${API_PREFIX}/projects/${projectId}/ai/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    credentials: "include",
    body: JSON.stringify(body),
  });
}

async function refreshSession(): Promise<void> {
  try {
    await axios.post(
      `${API_PREFIX}/auth/refresh`,
      {},
      { withCredentials: true },
    );
  } catch (error) {
    const { clearAuth } = await import("@/features/auth/lib/auth");
    clearAuth();
    useAuthStore.setState({
      user: null,
      isAuthenticated: false,
      isInitialized: true,
    });
    throw error;
  }
}

async function readChatErrorMessage(response: Response): Promise<string> {
  const fallback = `AI chat failed with status ${response.status}`;
  try {
    const payload = await response.json();
    if (payload && typeof payload === "object") {
      const errorNode = (payload as { error?: unknown }).error;
      if (errorNode && typeof errorNode === "object") {
        const message = (errorNode as { message?: unknown }).message;
        if (typeof message === "string" && message.trim()) {
          return message;
        }
      }
      const detail = (payload as { detail?: unknown }).detail;
      if (typeof detail === "string" && detail.trim()) {
        return detail;
      }
    }
  } catch {
    // ignore parse errors and use fallback
  }
  return fallback;
}

export const aiService = {
  async streamChat(
    projectId: string,
    body: AiChatRequest,
    onEvent: (event: AiChatEvent) => void,
  ): Promise<void> {
    let response = await openChatStream(projectId, body);
    if (response.status === 401) {
      await refreshSession();
      response = await openChatStream(projectId, body);
    }

    if (!response.ok) {
      throw new Error(await readChatErrorMessage(response));
    }

    if (!response.body) {
      throw new Error("AI chat stream is not available");
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder("utf-8");
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) {
        break;
      }

      buffer += decoder.decode(value, { stream: true });
      const blocks = buffer.split("\n\n");
      buffer = blocks.pop() ?? "";

      for (const block of blocks) {
        const dataLines = block
          .split("\n")
          .map((line) => line.trim())
          .filter((line) => line.startsWith("data:"));

        if (!dataLines.length) {
          continue;
        }

        const payload = dataLines
          .map((line) => line.replace(/^data:\s?/, ""))
          .join("");
        if (!payload) {
          continue;
        }

        try {
          const event = JSON.parse(payload) as AiChatEvent;
          onEvent(event);
        } catch {
          onEvent({ type: "error", message: "Malformed streaming response" });
        }
      }
    }
  },

  async estimate(projectId: string, data: AiEstimateRequest): Promise<AiEstimateResponse> {
    const response = await api.post<AiEstimateResponse>(
      `/projects/${projectId}/ai/estimate`,
      data,
    );
    return response.data;
  },

  async suggestions(projectId: string, limit = 5): Promise<AiSuggestionsResponse> {
    const response = await api.get<AiSuggestionsResponse>(
      `/projects/${projectId}/ai/suggestions`,
      { params: { limit } },
    );
    return response.data;
  },

  async resolveApproval(projectId: string, approvalId: string, approved: boolean): Promise<void> {
    await api.post(`/projects/${projectId}/ai/approvals/${approvalId}`, { approved });
  },

  async resolvePlanApproval(
    projectId: string,
    conversationId: string,
    approved: boolean,
    feedback?: string,
  ): Promise<void> {
    await api.post(`/projects/${projectId}/ai/plan-approval/${conversationId}`, {
      approved,
      feedback: feedback ?? null,
    });
  },

  async getConversations(projectId: string): Promise<ConversationSummary[]> {
    const response = await api.get<{ conversations: ConversationSummary[] }>(
      `/projects/${projectId}/ai/conversations`,
    );
    return response.data.conversations;
  },

  async getConversation(projectId: string, conversationId: string): Promise<ConversationDetail> {
    const response = await api.get<ConversationDetail>(
      `/projects/${projectId}/ai/conversations/${conversationId}`,
    );
    return response.data;
  },
};
