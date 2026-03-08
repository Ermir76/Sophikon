import { api } from "@/shared/api/api";
import type {
  NotificationItem,
  NotificationListResponse,
  NotificationReadAllResponse,
  NotificationSettings,
  NotificationSettingsUpdate,
} from "@/features/notifications/types";

export const notificationService = {
  async list(params?: {
    unread_only?: boolean;
    page?: number;
    per_page?: number;
  }): Promise<NotificationListResponse> {
    const response = await api.get<NotificationListResponse>("/notifications", { params });
    return response.data;
  },

  async markRead(notificationId: string): Promise<NotificationItem> {
    const response = await api.patch<NotificationItem>(`/notifications/${notificationId}/read`);
    return response.data;
  },

  async markAllRead(): Promise<NotificationReadAllResponse> {
    const response = await api.post<NotificationReadAllResponse>("/notifications/read-all");
    return response.data;
  },

  async getSettings(): Promise<NotificationSettings> {
    const response = await api.get<NotificationSettings>("/notifications/settings");
    return response.data;
  },

  async updateSettings(data: NotificationSettingsUpdate): Promise<NotificationSettings> {
    const response = await api.patch<NotificationSettings>("/notifications/settings", data);
    return response.data;
  },
};
