import { beforeEach, describe, expect, it } from "vitest";

import { useNotificationWebSocketStore } from "./notification-websocket-store";

describe("useNotificationWebSocketStore", () => {
  beforeEach(() => {
    useNotificationWebSocketStore.getState().reset();
  });

  it("starts with idle status and unknown unread count", () => {
    const state = useNotificationWebSocketStore.getState();
    expect(state.status).toBe("idle");
    expect(state.reconnectAttempt).toBe(0);
    expect(state.unreadCount).toBeNull();
  });

  it("updates websocket state fields", () => {
    const store = useNotificationWebSocketStore.getState();

    store.setStatus("reconnecting");
    store.setReconnectAttempt(2);
    store.setUnreadCount(7);

    const state = useNotificationWebSocketStore.getState();
    expect(state.status).toBe("reconnecting");
    expect(state.reconnectAttempt).toBe(2);
    expect(state.unreadCount).toBe(7);
  });

  it("resets state to defaults", () => {
    const store = useNotificationWebSocketStore.getState();
    store.setStatus("connected");
    store.setReconnectAttempt(4);
    store.setUnreadCount(3);

    store.reset();

    const state = useNotificationWebSocketStore.getState();
    expect(state.status).toBe("idle");
    expect(state.reconnectAttempt).toBe(0);
    expect(state.unreadCount).toBeNull();
  });
});
