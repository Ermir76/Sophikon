import { create } from "zustand";

import type {
  ProjectConnectionStatus,
  ProjectPresenceUser,
  ProjectRealtimeChannel,
} from "@/features/projects/types";

interface ProjectSocketState {
  status: ProjectConnectionStatus;
  users: ProjectPresenceUser[];
  subscribedChannels: ProjectRealtimeChannel[];
  reconnectAttempt: number;
}

interface ProjectWebSocketStore {
  projects: Record<string, ProjectSocketState>;
  setStatus: (projectId: string, status: ProjectConnectionStatus) => void;
  setUsers: (projectId: string, users: ProjectPresenceUser[]) => void;
  setSubscribedChannels: (
    projectId: string,
    channels: ProjectRealtimeChannel[],
  ) => void;
  setReconnectAttempt: (projectId: string, attempt: number) => void;
  clearProject: (projectId: string) => void;
}

const DEFAULT_PROJECT_SOCKET_STATE: ProjectSocketState = {
  status: "idle",
  users: [],
  subscribedChannels: [],
  reconnectAttempt: 0,
};

function getProjectState(
  state: Record<string, ProjectSocketState>,
  projectId: string,
) {
  return state[projectId] ?? DEFAULT_PROJECT_SOCKET_STATE;
}

export const useProjectWebSocketStore = create<ProjectWebSocketStore>((set) => ({
  projects: {},

  setStatus: (projectId, status) =>
    set((state) => ({
      projects: {
        ...state.projects,
        [projectId]: {
          ...getProjectState(state.projects, projectId),
          status,
        },
      },
    })),

  setUsers: (projectId, users) =>
    set((state) => ({
      projects: {
        ...state.projects,
        [projectId]: {
          ...getProjectState(state.projects, projectId),
          users,
        },
      },
    })),

  setSubscribedChannels: (projectId, channels) =>
    set((state) => ({
      projects: {
        ...state.projects,
        [projectId]: {
          ...getProjectState(state.projects, projectId),
          subscribedChannels: channels,
        },
      },
    })),

  setReconnectAttempt: (projectId, attempt) =>
    set((state) => ({
      projects: {
        ...state.projects,
        [projectId]: {
          ...getProjectState(state.projects, projectId),
          reconnectAttempt: attempt,
        },
      },
    })),

  clearProject: (projectId) =>
    set((state) => {
      const projects = { ...state.projects };
      delete projects[projectId];
      return { projects };
    }),
}));
