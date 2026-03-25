import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { renderHook, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { MemoryRouter } from "react-router";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { useAuthStore } from "@/features/auth/store/auth-store";
import { projectActivityKeys } from "@/features/projects/hooks/useProjectActivity";
import { projectDashboardKeys } from "@/features/projects/hooks/useProjectDashboard";
import { useProjectWebSocket } from "@/features/projects/hooks/useProjectWebSocket";
import { useProjectWebSocketStore } from "@/features/projects/store/websocket-store";
import { commentKeys } from "@/features/tasks/hooks/useComments";
import { taskKeys } from "@/features/tasks/hooks/useTasks";

class MockWebSocket {
  static instances: MockWebSocket[] = [];

  url: string;
  sent: string[] = [];
  listeners: Record<string, Array<(event?: unknown) => void>> = {
    open: [],
    message: [],
    close: [],
    error: [],
  };

  constructor(url: string) {
    this.url = url;
    MockWebSocket.instances.push(this);
  }

  addEventListener(type: string, listener: (event?: unknown) => void) {
    this.listeners[type]?.push(listener);
  }

  send(data: string) {
    this.sent.push(data);
  }

  close() {
    this.emit("close", { code: 1000 });
  }

  emit(type: string, event?: unknown) {
    for (const listener of this.listeners[type] ?? []) {
      listener(event);
    }
  }
}

function createWrapper(queryClient: QueryClient) {
  return function Wrapper({ children }: { children: ReactNode }) {
    return (
      <QueryClientProvider client={queryClient}>
        <MemoryRouter initialEntries={["/projects/project-1/tasks"]}>
          {children}
        </MemoryRouter>
      </QueryClientProvider>
    );
  };
}

describe("useProjectWebSocket", () => {
  beforeEach(() => {
    MockWebSocket.instances = [];
    vi.stubGlobal("WebSocket", MockWebSocket);
    useAuthStore.setState({
      user: {
        id: "user-1",
        email: "user@example.com",
        full_name: "Socket User",
        email_verified: true,
      },
      isAuthenticated: true,
      isInitialized: true,
    });
    useProjectWebSocketStore.setState({ projects: {} });
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    useProjectWebSocketStore.setState({ projects: {} });
  });

  it("connects, subscribes, and stores presence updates", async () => {
    const queryClient = new QueryClient();
    renderHook(() => useProjectWebSocket("project-1"), {
      wrapper: createWrapper(queryClient),
    });

    expect(MockWebSocket.instances).toHaveLength(1);
    const socket = MockWebSocket.instances[0];
    expect(socket.url).toContain("/api/v1/ws/projects/project-1");

    socket.emit("open");

    await waitFor(() => {
      expect(useProjectWebSocketStore.getState().projects["project-1"]?.status).toBe(
        "connected",
      );
    });

    expect(socket.sent).toEqual([
      JSON.stringify({
        type: "subscribe",
        channels: ["tasks", "resources", "members", "activity", "project", "comments"],
      }),
    ]);

    socket.emit("message", {
      data: JSON.stringify({
        type: "presence_update",
        project_id: "project-1",
        users: [
          {
            id: "user-2",
            full_name: "Another User",
            avatar_url: null,
            status: "viewing",
            entity_type: "project",
            entity_id: "project-1",
          },
        ],
      }),
    });

    await waitFor(() => {
      expect(useProjectWebSocketStore.getState().projects["project-1"]?.users).toHaveLength(1);
    });
  });

  it("invalidates project and task queries for entity events", async () => {
    const queryClient = new QueryClient();
    const invalidateQueries = vi.spyOn(queryClient, "invalidateQueries");

    renderHook(() => useProjectWebSocket("project-1"), {
      wrapper: createWrapper(queryClient),
    });

    const socket = MockWebSocket.instances[0];
    socket.emit("open");
    socket.emit("message", {
      data: JSON.stringify({
        type: "task_updated",
        project_id: "project-1",
        entity_type: "task",
        action: "updated",
        entity_id: "task-1",
        entity_name: "Realtime Task",
        occurred_at: "2026-03-08T12:00:00Z",
        actor: null,
        metadata: null,
      }),
    });
    socket.emit("message", {
      data: JSON.stringify({
        type: "comment_updated",
        project_id: "project-1",
        entity_type: "comment",
        action: "updated",
        entity_id: "comment-1",
        entity_name: "Realtime comment",
        occurred_at: "2026-03-08T12:00:01Z",
        actor: null,
        metadata: {
          comment_entity_type: "task",
          comment_entity_id: "task-1",
        },
      }),
    });

    await waitFor(() => {
      expect(invalidateQueries).toHaveBeenCalled();
    });

    expect(invalidateQueries).toHaveBeenCalledWith({
      queryKey: projectActivityKeys.all,
    });
    expect(invalidateQueries).toHaveBeenCalledWith({
      queryKey: projectDashboardKeys.detail("project-1"),
    });
    expect(invalidateQueries).toHaveBeenCalledWith({
      queryKey: taskKeys.list("project-1"),
    });
    expect(invalidateQueries).toHaveBeenCalledWith({
      queryKey: commentKeys.byEntity("task", "task-1"),
    });
  });

  it("does not reconnect on rerender with the same project id", () => {
    const queryClient = new QueryClient();
    const { rerender } = renderHook(
      ({ projectId }: { projectId: string }) => useProjectWebSocket(projectId),
      {
        initialProps: { projectId: "project-1" },
        wrapper: createWrapper(queryClient),
      },
    );

    expect(MockWebSocket.instances).toHaveLength(1);

    rerender({ projectId: "project-1" });

    expect(MockWebSocket.instances).toHaveLength(1);
  });
});
