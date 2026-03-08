import { act, renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import type { ReactNode } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import {
  notificationKeys,
  useMarkAllNotificationsRead,
  useMarkNotificationRead,
  useNotifications,
  useUpdateNotificationSettings,
} from "@/features/notifications/hooks/useNotifications";

vi.mock("@/features/notifications/api/notification.service", () => ({
  notificationService: {
    list: vi.fn(),
    markRead: vi.fn(),
    markAllRead: vi.fn(),
    updateSettings: vi.fn(),
  },
}));

import { notificationService } from "@/features/notifications/api/notification.service";

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

  const wrapper = ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );

  return { queryClient, wrapper };
}

describe("useNotifications hooks", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("loads notifications list", async () => {
    vi.mocked(notificationService.list).mockResolvedValue({
      items: [],
      total: 0,
      page: 1,
      per_page: 20,
      total_pages: 0,
      unread_count: 0,
    });

    const { wrapper } = createWrapper();
    const { result } = renderHook(() => useNotifications(), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(notificationService.list).toHaveBeenCalledWith({
      unread_only: false,
      page: 1,
      per_page: 20,
    });
  });

  it("invalidates notification queries after mark-read and mark-all", async () => {
    vi.mocked(notificationService.markRead).mockResolvedValue({
      id: "n-1",
      type: "mentioned",
      title: "Mentioned",
      message: null,
      entity_type: "comment",
      entity_id: "c-1",
      actor: null,
      is_read: true,
      read_at: "2026-03-08T12:00:00Z",
      created_at: "2026-03-08T11:59:00Z",
    });
    vi.mocked(notificationService.markAllRead).mockResolvedValue({
      updated_count: 3,
      unread_count: 0,
    });

    const { queryClient, wrapper } = createWrapper();
    const invalidateSpy = vi.spyOn(queryClient, "invalidateQueries");
    const { result: markReadResult } = renderHook(() => useMarkNotificationRead(), {
      wrapper,
    });
    const { result: markAllResult } = renderHook(() => useMarkAllNotificationsRead(), {
      wrapper,
    });

    await act(async () => {
      await markReadResult.current.mutateAsync("n-1");
      await markAllResult.current.mutateAsync();
    });

    expect(notificationService.markRead).toHaveBeenCalledWith("n-1");
    expect(notificationService.markAllRead).toHaveBeenCalled();
    expect(invalidateSpy).toHaveBeenCalledWith({ queryKey: notificationKeys.all });
  });

  it("invalidates settings query after update", async () => {
    vi.mocked(notificationService.updateSettings).mockResolvedValue({
      email_task_assigned: true,
      email_mentioned: false,
      email_deadline_approaching: true,
      push_enabled: true,
    });

    const { queryClient, wrapper } = createWrapper();
    const invalidateSpy = vi.spyOn(queryClient, "invalidateQueries");
    const { result } = renderHook(() => useUpdateNotificationSettings(), { wrapper });

    await act(async () => {
      await result.current.mutateAsync({
        email_mentioned: false,
        push_enabled: true,
      });
    });

    expect(invalidateSpy).toHaveBeenCalledWith({
      queryKey: notificationKeys.settings(),
    });
  });
});
