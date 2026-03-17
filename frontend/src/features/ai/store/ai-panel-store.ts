import { create } from "zustand";

import type { AiChatMessage, AiTab, PendingApproval, ToolCallStatus } from "@/features/ai/types";

interface ProjectAiPanelState {
  isOpen: boolean;
  activeTab: AiTab;
  panelSize: number;
  conversationId: string | null;
  conversationStatus: string | null;
  messages: AiChatMessage[];
  pendingApproval: PendingApproval | null;
  pendingPlan: Array<{ action: string; reason: string }> | null;
  isThinking: boolean;
  reasoningText: string;
}

interface AiPanelStore {
  projects: Record<string, ProjectAiPanelState>;
  togglePanel: (projectId: string) => void;
  setPanelOpen: (projectId: string, isOpen: boolean) => void;
  setActiveTab: (projectId: string, tab: AiTab) => void;
  setPanelSize: (projectId: string, panelSize: number) => void;
  setConversationId: (projectId: string, conversationId: string | null) => void;
  setConversationStatus: (projectId: string, status: string | null) => void;
  appendMessage: (projectId: string, message: AiChatMessage) => void;
  appendToMessage: (projectId: string, messageId: string, delta: string) => void;
  replaceMessageContent: (projectId: string, messageId: string, content: string) => void;
  clearConversation: (projectId: string) => void;
  loadConversationMessages: (projectId: string, conversationId: string, messages: AiChatMessage[]) => void;
  setPendingApproval: (projectId: string, approval: PendingApproval | null) => void;
  updateToolStatus: (projectId: string, messageId: string, status: ToolCallStatus) => void;
  setToolResult: (projectId: string, messageId: string, result: string) => void;
  setPendingPlan: (projectId: string, steps: Array<{ action: string; reason: string }> | null) => void;
  setThinking: (projectId: string, value: boolean) => void;
  appendReasoningText: (projectId: string, text: string) => void;
  clearReasoningText: (projectId: string) => void;
}

const DEFAULT_PROJECT_STATE: ProjectAiPanelState = {
  isOpen: false,
  activeTab: "chat",
  panelSize: 34,
  conversationId: null,
  conversationStatus: null,
  messages: [],
  pendingApproval: null,
  pendingPlan: null,
  isThinking: false,
  reasoningText: "",
};

function getProjectState(
  state: Record<string, ProjectAiPanelState>,
  projectId: string,
): ProjectAiPanelState {
  return state[projectId] ?? DEFAULT_PROJECT_STATE;
}

function clampPanelSize(value: number): number {
  return Math.min(55, Math.max(20, value));
}

export const useAiPanelStore = create<AiPanelStore>((set) => ({
  projects: {},

  togglePanel: (projectId) =>
    set((state) => {
      const current = getProjectState(state.projects, projectId);
      return {
        projects: {
          ...state.projects,
          [projectId]: {
            ...current,
            isOpen: !current.isOpen,
          },
        },
      };
    }),

  setPanelOpen: (projectId, isOpen) =>
    set((state) => {
      const current = getProjectState(state.projects, projectId);
      return {
        projects: {
          ...state.projects,
          [projectId]: {
            ...current,
            isOpen,
          },
        },
      };
    }),

  setActiveTab: (projectId, tab) =>
    set((state) => {
      const current = getProjectState(state.projects, projectId);
      return {
        projects: {
          ...state.projects,
          [projectId]: {
            ...current,
            activeTab: tab,
          },
        },
      };
    }),

  setPanelSize: (projectId, panelSize) =>
    set((state) => {
      const current = getProjectState(state.projects, projectId);
      return {
        projects: {
          ...state.projects,
          [projectId]: {
            ...current,
            panelSize: clampPanelSize(panelSize),
          },
        },
      };
    }),

  setConversationId: (projectId, conversationId) =>
    set((state) => {
      const current = getProjectState(state.projects, projectId);
      return {
        projects: {
          ...state.projects,
          [projectId]: { ...current, conversationId },
        },
      };
    }),

  setConversationStatus: (projectId, status) =>
    set((state) => {
      const current = getProjectState(state.projects, projectId);
      return {
        projects: {
          ...state.projects,
          [projectId]: { ...current, conversationStatus: status },
        },
      };
    }),

  appendMessage: (projectId, message) =>
    set((state) => {
      const current = getProjectState(state.projects, projectId);
      return {
        projects: {
          ...state.projects,
          [projectId]: {
            ...current,
            messages: [...current.messages, message],
          },
        },
      };
    }),

  appendToMessage: (projectId, messageId, delta) =>
    set((state) => {
      const current = getProjectState(state.projects, projectId);
      return {
        projects: {
          ...state.projects,
          [projectId]: {
            ...current,
            messages: current.messages.map((message) =>
              message.id === messageId
                ? { ...message, content: message.content + delta }
                : message,
            ),
          },
        },
      };
    }),

  replaceMessageContent: (projectId, messageId, content) =>
    set((state) => {
      const current = getProjectState(state.projects, projectId);
      return {
        projects: {
          ...state.projects,
          [projectId]: {
            ...current,
            messages: current.messages.map((message) =>
              message.id === messageId ? { ...message, content } : message,
            ),
          },
        },
      };
    }),

  clearConversation: (projectId) =>
    set((state) => {
      const current = getProjectState(state.projects, projectId);
      return {
        projects: {
          ...state.projects,
          [projectId]: {
            ...current,
            conversationId: null,
            conversationStatus: null,
            messages: [],
            pendingApproval: null,
            pendingPlan: null,
            isThinking: false,
            reasoningText: "",
          },
        },
      };
    }),

  loadConversationMessages: (projectId, conversationId, messages) =>
    set((state) => {
      const current = getProjectState(state.projects, projectId);
      return {
        projects: {
          ...state.projects,
          [projectId]: {
            ...current,
            conversationId,
            messages,
            pendingApproval: null,
            pendingPlan: null,
            isThinking: false,
            reasoningText: "",
          },
        },
      };
    }),

  setPendingApproval: (projectId, approval) =>
    set((state) => {
      const current = getProjectState(state.projects, projectId);
      return {
        projects: {
          ...state.projects,
          [projectId]: { ...current, pendingApproval: approval },
        },
      };
    }),

  updateToolStatus: (projectId, messageId, status) =>
    set((state) => {
      const current = getProjectState(state.projects, projectId);
      return {
        projects: {
          ...state.projects,
          [projectId]: {
            ...current,
            messages: current.messages.map((m) =>
              m.id === messageId ? { ...m, toolStatus: status } : m,
            ),
          },
        },
      };
    }),

  setToolResult: (projectId, messageId, result) =>
    set((state) => {
      const current = getProjectState(state.projects, projectId);
      return {
        projects: {
          ...state.projects,
          [projectId]: {
            ...current,
            messages: current.messages.map((m) =>
              m.id === messageId ? { ...m, toolResult: result } : m,
            ),
          },
        },
      };
    }),

  setPendingPlan: (projectId, steps) =>
    set((state) => {
      const current = getProjectState(state.projects, projectId);
      return {
        projects: {
          ...state.projects,
          [projectId]: { ...current, pendingPlan: steps },
        },
      };
    }),

  setThinking: (projectId, value) =>
    set((state) => {
      const current = getProjectState(state.projects, projectId);
      return {
        projects: {
          ...state.projects,
          [projectId]: { ...current, isThinking: value },
        },
      };
    }),

  appendReasoningText: (projectId, text) =>
    set((state) => {
      const current = getProjectState(state.projects, projectId);
      return {
        projects: {
          ...state.projects,
          [projectId]: { ...current, reasoningText: current.reasoningText + text },
        },
      };
    }),

  clearReasoningText: (projectId) =>
    set((state) => {
      const current = getProjectState(state.projects, projectId);
      return {
        projects: {
          ...state.projects,
          [projectId]: { ...current, reasoningText: "" },
        },
      };
    }),
}));
