import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { renderHook, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { useAuthStore } from "@/features/auth/store/auth-store";
import { notificationKeys } from "@/features/notifications/hooks/useNotifications";
import { useNotificationWebSocket } from "@/features/notifications/hooks/useNotificationWebSocket";
import { useNotificationWebSocketStore } from "@/features/notifications/store/notification-websocket-store";

class MockWebSocket {
  static instances: MockWebSocket[] = [];

  url: string;
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
        {children}
      </QueryClientProvider>
    );
  };
}

describe("useNotificationWebSocket", () => {
  beforeEach(() => {
    MockWebSocket.instances = [];
    vi.stubGlobal("WebSocket", MockWebSocket);
    useAuthStore.setState({
      user: {
        id: "user-1",
        email: "user@example.com",
        full_name: "Notif User",
        email_verified: true,
      },
      isAuthenticated: true,
      isInitialized: true,
    });
    useNotificationWebSocketStore.setState({
      status: "idle",
      reconnectAttempt: 0,
      unreadCount: null,
    });
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    useNotificationWebSocketStore.getState().reset();
  });

  it("connects and stores unread count from snapshot", async () => {
    const queryClient = new QueryClient();
    renderHook(() => useNotificationWebSocket(), {
      wrapper: createWrapper(queryClient),
    });

    expect(MockWebSocket.instances).toHaveLength(1);
    const socket = MockWebSocket.instances[0];
    expect(socket.url).toContain("/api/v1/ws/notifications");

    socket.emit("open");
    socket.emit("message", {
      data: JSON.stringify({
        type: "notification_snapshot",
        unread_count: 3,
      }),
    });

    await waitFor(() => {
      expect(useNotificationWebSocketStore.getState().status).toBe("connected");
      expect(useNotificationWebSocketStore.getState().unreadCount).toBe(3);
    });
  });

  it("invalidates notification queries on notification events", async () => {
    const queryClient = new QueryClient();
    const invalidateQueries = vi.spyOn(queryClient, "invalidateQueries");
    renderHook(() => useNotificationWebSocket(), {
      wrapper: createWrapper(queryClient),
    });

    const socket = MockWebSocket.instances[0];
    socket.emit("open");
    socket.emit("message", {
      data: JSON.stringify({
        type: "notification_created",
        unread_count: 4,
        notification: {
          id: "n-1",
          type: "mentioned",
          title: "Mentioned",
          is_read: false,
          created_at: "2026-03-08T12:00:00Z",
        },
      }),
    });

    await waitFor(() => {
      expect(invalidateQueries).toHaveBeenCalledWith({
        queryKey: notificationKeys.all,
      });
      expect(useNotificationWebSocketStore.getState().unreadCount).toBe(4);
    });
  });

  it("treats close code 4400 as terminal and does not schedule reconnect", async () => {
    const queryClient = new QueryClient();
    renderHook(() => useNotificationWebSocket(), {
      wrapper: createWrapper(queryClient),
    });

    const socket = MockWebSocket.instances[0];
    socket.emit("open");
    socket.emit("close", { code: 4400 });

    await waitFor(() => {
      const state = useNotificationWebSocketStore.getState();
      expect(state.status).toBe("error");
      expect(state.reconnectAttempt).toBe(0);
    });
  });
});
