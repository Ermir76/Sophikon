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

  it("tracks conversation status", () => {
    const store = useAiPanelStore.getState();

    store.setConversationStatus("project-1", "awaiting_plan_approval");
    expect(
      useAiPanelStore.getState().projects["project-1"]?.conversationStatus,
    ).toBe("awaiting_plan_approval");

    store.setConversationStatus("project-1", "idle");
    expect(
      useAiPanelStore.getState().projects["project-1"]?.conversationStatus,
    ).toBe("idle");
  });

  it("manages pending plan steps", () => {
    const store = useAiPanelStore.getState();
    const steps = [
      { action: "Get tasks", reason: "Need current state" },
      { action: "Update task", reason: "Fix the due date" },
    ];

    store.setPendingPlan("project-1", steps);
    expect(
      useAiPanelStore.getState().projects["project-1"]?.pendingPlan,
    ).toEqual(steps);

    store.setPendingPlan("project-1", null);
    expect(
      useAiPanelStore.getState().projects["project-1"]?.pendingPlan,
    ).toBeNull();
  });

  it("accumulates and clears reasoning text", () => {
    const store = useAiPanelStore.getState();

    store.setThinking("project-1", true);
    store.appendReasoningText("project-1", "First ");
    store.appendReasoningText("project-1", "second.");

    expect(useAiPanelStore.getState().projects["project-1"]).toMatchObject({
      isThinking: true,
      reasoningText: "First second.",
    });

    store.setThinking("project-1", false);
    store.clearReasoningText("project-1");

    expect(useAiPanelStore.getState().projects["project-1"]).toMatchObject({
      isThinking: false,
      reasoningText: "",
    });
  });

  it("sets tool result on a matching message", () => {
    const store = useAiPanelStore.getState();
    store.appendMessage("project-1", {
      id: "tool-1",
      role: "assistant",
      content: "",
      createdAt: 1,
      toolName: "get_tasks",
      toolStatus: "running",
    });

    store.setToolResult("project-1", "tool-1", '{"tasks":[]}');

    const msg = useAiPanelStore
      .getState()
      .projects["project-1"]?.messages.find((m) => m.id === "tool-1");
    expect(msg?.toolResult).toBe('{"tasks":[]}');
  });

  it("loadConversationMessages replaces messages and resets transient state", () => {
    const store = useAiPanelStore.getState();

    store.setConversationStatus("project-1", "interrupted");
    store.setPendingPlan("project-1", [{ action: "old", reason: "old" }]);
    store.setThinking("project-1", true);
    store.appendReasoningText("project-1", "stale text");

    store.loadConversationMessages("project-1", "conv-42", [
      { id: "m-1", role: "user", content: "Hi", createdAt: 1 },
    ]);

    expect(useAiPanelStore.getState().projects["project-1"]).toMatchObject({
      conversationId: "conv-42",
      messages: [{ id: "m-1", content: "Hi" }],
      pendingPlan: null,
      isThinking: false,
      reasoningText: "",
    });
  });

  it("clearConversation resets all agent state", () => {
    const store = useAiPanelStore.getState();

    store.setConversationId("project-1", "conv-1");
    store.setConversationStatus("project-1", "executing");
    store.setPendingPlan("project-1", [{ action: "do", reason: "because" }]);
    store.setThinking("project-1", true);
    store.appendReasoningText("project-1", "thinking...");
    store.appendMessage("project-1", {
      id: "m-1",
      role: "user",
      content: "hello",
      createdAt: 1,
    });

    store.clearConversation("project-1");

    expect(useAiPanelStore.getState().projects["project-1"]).toMatchObject({
      conversationId: null,
      conversationStatus: null,
      messages: [],
      pendingPlan: null,
      isThinking: false,
      reasoningText: "",
    });
  });
});
