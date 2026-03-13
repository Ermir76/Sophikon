import { create } from "zustand";

import type { AiChatMessage, AiTab, PendingApproval, ToolCallStatus } from "@/features/ai/types";

interface ProjectAiPanelState {
  isOpen: boolean;
  activeTab: AiTab;
  panelSize: number;
  conversationId: string | null;
  messages: AiChatMessage[];
  pendingApproval: PendingApproval | null;
}

interface AiPanelStore {
  projects: Record<string, ProjectAiPanelState>;
  togglePanel: (projectId: string) => void;
  setPanelOpen: (projectId: string, isOpen: boolean) => void;
  setActiveTab: (projectId: string, tab: AiTab) => void;
  setPanelSize: (projectId: string, panelSize: number) => void;
  setConversationId: (projectId: string, conversationId: string | null) => void;
  appendMessage: (projectId: string, message: AiChatMessage) => void;
  appendToMessage: (projectId: string, messageId: string, delta: string) => void;
  replaceMessageContent: (
    projectId: string,
    messageId: string,
    content: string,
  ) => void;
  clearConversation: (projectId: string) => void;
  setPendingApproval: (projectId: string, approval: PendingApproval | null) => void;
  updateToolStatus: (projectId: string, messageId: string, status: ToolCallStatus) => void;
}

const DEFAULT_PROJECT_STATE: ProjectAiPanelState = {
  isOpen: false,
  activeTab: "chat",
  panelSize: 34,
  conversationId: null,
  messages: [],
  pendingApproval: null,
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
          [projectId]: {
            ...current,
            conversationId,
          },
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
            messages: [],
            pendingApproval: null,
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
          [projectId]: {
            ...current,
            pendingApproval: approval,
          },
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
            messages: current.messages.map((message) =>
              message.id === messageId ? { ...message, toolStatus: status } : message,
            ),
          },
        },
      };
    }),
}));
