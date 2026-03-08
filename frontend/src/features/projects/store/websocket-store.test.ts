import { beforeEach, describe, expect, it } from "vitest";

import { useProjectWebSocketStore } from "./websocket-store";

describe("useProjectWebSocketStore", () => {
  beforeEach(() => {
    useProjectWebSocketStore.setState({ projects: {} });
  });

  it("creates project state on first update and persists all realtime fields", () => {
    const store = useProjectWebSocketStore.getState();

    store.setStatus("project-1", "connecting");
    store.setSubscribedChannels("project-1", ["tasks", "project"]);
    store.setReconnectAttempt("project-1", 2);
    store.setUsers("project-1", [
      {
        id: "user-1",
        full_name: "Socket User",
        avatar_url: null,
        status: "viewing",
        entity_type: "project",
        entity_id: "project-1",
      },
    ]);

    expect(useProjectWebSocketStore.getState().projects["project-1"]).toMatchObject({
      status: "connecting",
      subscribedChannels: ["tasks", "project"],
      reconnectAttempt: 2,
      users: [
        {
          id: "user-1",
          status: "viewing",
          entity_type: "project",
          entity_id: "project-1",
        },
      ],
    });
  });

  it("keeps websocket state isolated per project id", () => {
    const store = useProjectWebSocketStore.getState();

    store.setStatus("project-1", "connected");
    store.setStatus("project-2", "reconnecting");
    store.setReconnectAttempt("project-2", 3);

    expect(useProjectWebSocketStore.getState().projects["project-1"]).toMatchObject({
      status: "connected",
      reconnectAttempt: 0,
    });
    expect(useProjectWebSocketStore.getState().projects["project-2"]).toMatchObject({
      status: "reconnecting",
      reconnectAttempt: 3,
    });
  });

  it("clears only the requested project state", () => {
    const store = useProjectWebSocketStore.getState();

    store.setStatus("project-1", "connected");
    store.setStatus("project-2", "connected");
    store.clearProject("project-1");

    expect(useProjectWebSocketStore.getState().projects["project-1"]).toBeUndefined();
    expect(useProjectWebSocketStore.getState().projects["project-2"]).toBeDefined();
  });
});
