import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { notificationService } from "@/features/notifications/api/notification.service";
import type { NotificationSettingsUpdate } from "@/features/notifications/types";

export const notificationKeys = {
  all: ["notifications"] as const,
  list: (unreadOnly = false, page = 1, perPage = 20) =>
    [...notificationKeys.all, "list", unreadOnly, page, perPage] as const,
  settings: () => [...notificationKeys.all, "settings"] as const,
};

export function useNotifications(params?: {
  unread_only?: boolean;
  page?: number;
  per_page?: number;
}) {
  const unreadOnly = params?.unread_only ?? false;
  const page = params?.page ?? 1;
  const perPage = params?.per_page ?? 20;

  return useQuery({
    queryKey: notificationKeys.list(unreadOnly, page, perPage),
    queryFn: () =>
      notificationService.list({
        unread_only: unreadOnly,
        page,
        per_page: perPage,
      }),
  });
}

export function useMarkNotificationRead() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (notificationId: string) => notificationService.markRead(notificationId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: notificationKeys.all });
    },
  });
}

export function useMarkAllNotificationsRead() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => notificationService.markAllRead(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: notificationKeys.all });
    },
  });
}

export function useNotificationSettings() {
  return useQuery({
    queryKey: notificationKeys.settings(),
    queryFn: () => notificationService.getSettings(),
  });
}

export function useUpdateNotificationSettings() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: NotificationSettingsUpdate) =>
      notificationService.updateSettings(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: notificationKeys.settings() });
    },
  });
}
