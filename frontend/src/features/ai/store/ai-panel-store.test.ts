import { beforeEach, describe, expect, it } from "vitest";

import { useAiPanelStore } from "./ai-panel-store";

describe("useAiPanelStore", () => {
  beforeEach(() => {
    useAiPanelStore.setState({ projects: {} });
  });

  it("creates project state on first toggle and updates the active tab", () => {
    const store = useAiPanelStore.getState();

    store.togglePanel("project-1");
    store.setActiveTab("project-1", "suggestions");

    expect(useAiPanelStore.getState().projects["project-1"]).toMatchObject({
      isOpen: true,
      activeTab: "suggestions",
      panelSize: 34,
      conversationId: null,
      messages: [],
    });
  });

  it("clamps panel size within the supported range", () => {
    const store = useAiPanelStore.getState();

    store.setPanelSize("project-1", 5);
    expect(useAiPanelStore.getState().projects["project-1"]?.panelSize).toBe(20);

    store.setPanelSize("project-1", 80);
    expect(useAiPanelStore.getState().projects["project-1"]?.panelSize).toBe(55);
  });

  it("appends, updates, and clears conversation messages", () => {
    const store = useAiPanelStore.getState();
    store.setConversationId("project-1", "conv-1");
    store.appendMessage("project-1", {
      id: "m-1",
      role: "assistant",
      content: "Hello",
      createdAt: 1,
    });
    store.appendToMessage("project-1", "m-1", " world");
    store.replaceMessageContent("project-1", "m-1", "Replaced");

    expect(useAiPanelStore.getState().projects["project-1"]).toMatchObject({
      conversationId: "conv-1",
      messages: [
        {
          id: "m-1",
          role: "assistant",
          content: "Replaced",
          createdAt: 1,
        },
      ],
    });

    store.clearConversation("project-1");

    expect(useAiPanelStore.getState().projects["project-1"]).toMatchObject({
      conversationId: null,
      messages: [],
    });
  });

  it("keeps project state isolated per project id", () => {
    const store = useAiPanelStore.getState();

    store.setPanelOpen("project-1", true);
    store.setPanelOpen("project-2", false);
    store.appendMessage("project-1", {
      id: "m-1",
      role: "user",
      content: "Project one",
      createdAt: 1,
    });
    store.appendMessage("project-2", {
      id: "m-2",
      role: "user",
      content: "Project two",
      createdAt: 2,
    });

    expect(useAiPanelStore.getState().projects["project-1"]).toMatchObject({
      isOpen: true,
      messages: [{ id: "m-1", content: "Project one" }],
    });
    expect(useAiPanelStore.getState().projects["project-2"]).toMatchObject({
      isOpen: false,
      messages: [{ id: "m-2", content: "Project two" }],
    });
  });
});
