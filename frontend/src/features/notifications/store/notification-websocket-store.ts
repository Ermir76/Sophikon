import { create } from "zustand";

import type { NotificationConnectionStatus } from "@/features/notifications/types";

interface NotificationWebSocketStore {
  status: NotificationConnectionStatus;
  reconnectAttempt: number;
  unreadCount: number | null;
  setStatus: (status: NotificationConnectionStatus) => void;
  setReconnectAttempt: (attempt: number) => void;
  setUnreadCount: (count: number | null) => void;
  reset: () => void;
}

const DEFAULT_STATE = {
  status: "idle" as NotificationConnectionStatus,
  reconnectAttempt: 0,
  unreadCount: null,
};

export const useNotificationWebSocketStore = create<NotificationWebSocketStore>((set) => ({
  ...DEFAULT_STATE,

  setStatus: (status) => set({ status }),
  setReconnectAttempt: (reconnectAttempt) => set({ reconnectAttempt }),
  setUnreadCount: (unreadCount) => set({ unreadCount }),
  reset: () => set(DEFAULT_STATE),
}));
