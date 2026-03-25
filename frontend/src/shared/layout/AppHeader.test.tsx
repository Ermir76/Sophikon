import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter, Route, Routes } from "react-router";
import { beforeEach, describe, expect, it, vi } from "vitest";

import {
  useMarkAllNotificationsRead,
  useMarkNotificationRead,
  useNotifications,
  useNotificationSettings,
  useNotificationWebSocketStore,
  useUpdateNotificationSettings,
} from "@/features/notifications";
import { useAcceptProjectInvitation } from "@/features/projects";
import { useProjectWebSocketStore } from "@/features/projects/store/websocket-store";
import { AppHeader } from "@/shared/layout/AppHeader";

vi.mock("@/shared/ui/sidebar", () => ({
  SidebarTrigger: () => <button type="button">Menu</button>,
}));

vi.mock("@/features/notifications", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/features/notifications")>();
  return {
    ...actual,
    useNotifications: vi.fn(),
    useMarkNotificationRead: vi.fn(),
    useMarkAllNotificationsRead: vi.fn(),
    useNotificationSettings: vi.fn(),
    useUpdateNotificationSettings: vi.fn(),
  };
});

vi.mock("@/features/projects", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/features/projects")>();
  return {
    ...actual,
    useAcceptProjectInvitation: vi.fn(),
  };
});

vi.mock("sonner", () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
  },
}));

function renderHeader(pathname: string) {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[pathname]}>
        <AppHeader />
        <Routes>
          <Route path="/project-invitations/accept" element={<div>INVITE ACCEPT PAGE</div>} />
          <Route path="*" element={null} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("AppHeader", () => {
  beforeEach(() => {
    useProjectWebSocketStore.setState({ projects: {} });
    useNotificationWebSocketStore.setState({
      status: "idle",
      reconnectAttempt: 0,
      unreadCount: null,
    });
    vi.mocked(useNotifications).mockReturnValue({
      data: {
        items: [],
        total: 0,
        page: 1,
        per_page: 20,
        total_pages: 0,
        unread_count: 2,
      },
      isLoading: false,
      isError: false,
    } as never);
    vi.mocked(useMarkNotificationRead).mockReturnValue({
      mutate: vi.fn(),
      isPending: false,
    } as never);
    vi.mocked(useMarkAllNotificationsRead).mockReturnValue({
      mutate: vi.fn(),
      isPending: false,
    } as never);
    vi.mocked(useNotificationSettings).mockReturnValue({
      data: {
        email_task_assigned: true,
        email_mentioned: true,
        email_deadline_approaching: true,
        push_enabled: false,
      },
      isLoading: false,
      isError: false,
    } as never);
    vi.mocked(useUpdateNotificationSettings).mockReturnValue({
      mutate: vi.fn(),
      isPending: false,
    } as never);
    vi.mocked(useAcceptProjectInvitation).mockReturnValue({
      mutateAsync: vi.fn(),
      isPending: false,
    } as never);
  });

  it("shows live presence avatars on project routes", () => {
    useProjectWebSocketStore.setState({
      projects: {
        "project-1": {
          status: "connected",
          reconnectAttempt: 0,
          subscribedChannels: ["tasks", "resources", "members", "activity", "project"],
          users: [
            {
              id: "user-1",
              full_name: "Jane Doe",
              avatar_url: null,
              status: "viewing",
              entity_type: "project",
              entity_id: "project-1",
            },
            {
              id: "user-2",
              full_name: "John Smith",
              avatar_url: null,
              status: "viewing",
              entity_type: "project",
              entity_id: "project-1",
            },
            {
              id: "user-3",
              full_name: "Ada Lovelace",
              avatar_url: null,
              status: "editing",
              entity_type: "task",
              entity_id: "task-1",
            },
            {
              id: "user-4",
              full_name: "Alan Turing",
              avatar_url: null,
              status: "viewing",
              entity_type: "project",
              entity_id: "project-1",
            },
            {
              id: "user-5",
              full_name: "Grace Hopper",
              avatar_url: null,
              status: "viewing",
              entity_type: "project",
              entity_id: "project-1",
            },
          ],
        },
      },
    });

    renderHeader("/projects/project-1/tasks");

    expect(screen.getByText("Live")).toBeInTheDocument();
    expect(screen.getByText("JD")).toBeInTheDocument();
    expect(screen.getByText("JS")).toBeInTheDocument();
    expect(screen.getByText("+1")).toBeInTheDocument();
  });

  it("does not show presence outside project routes", () => {
    renderHeader("/");

    expect(screen.queryByText("Live")).not.toBeInTheDocument();
  });

  it("shows notifications button with unread badge", () => {
    renderHeader("/");
    expect(screen.getByRole("button", { name: "Notifications" })).toBeInTheDocument();
    expect(screen.getByText("2")).toBeInTheDocument();
  });

  it("prefers websocket unread count over query unread count", () => {
    useNotificationWebSocketStore.setState({
      status: "connected",
      reconnectAttempt: 0,
      unreadCount: 5,
    });

    renderHeader("/");
    expect(screen.getByText("5")).toBeInTheDocument();
  });

  it("opens the invitation accept page from an invitation notification", async () => {
    const user = userEvent.setup();
    const markRead = vi.fn();

    vi.mocked(useNotifications).mockReturnValue({
      data: {
        items: [
          {
            id: "notification-1",
            type: "invitation_received",
            title: "Invited to Project Alpha",
            message: "Owner invited you.",
            entity_type: "project_invitation",
            entity_id: "invitation-1",
            is_read: false,
            created_at: new Date().toISOString(),
          },
        ],
        total: 1,
        page: 1,
        per_page: 20,
        total_pages: 1,
        unread_count: 1,
      },
      isLoading: false,
      isError: false,
    } as never);
    vi.mocked(useMarkNotificationRead).mockReturnValue({
      mutate: markRead,
      isPending: false,
    } as never);

    renderHeader("/");

    await user.click(screen.getByRole("button", { name: "Notifications" }));
    await user.click(screen.getByRole("button", { name: "Invited to Project Alpha" }));

    expect(markRead).toHaveBeenCalledWith("notification-1");
    expect(screen.getByText("INVITE ACCEPT PAGE")).toBeInTheDocument();
  });

  it("accepts an invitation directly from the notification card", async () => {
    const user = userEvent.setup();
    const markRead = vi.fn();
    const mutateAsync = vi.fn().mockResolvedValue({
      project_id: "project-1",
      member_id: "member-1",
    });

    vi.mocked(useNotifications).mockReturnValue({
      data: {
        items: [
          {
            id: "notification-1",
            type: "invitation_received",
            title: "Invited to Project Alpha",
            message: "Owner invited you.",
            entity_type: "project_invitation",
            entity_id: "invitation-1",
            is_read: false,
            created_at: new Date().toISOString(),
          },
        ],
        total: 1,
        page: 1,
        per_page: 20,
        total_pages: 1,
        unread_count: 1,
      },
      isLoading: false,
      isError: false,
    } as never);
    vi.mocked(useMarkNotificationRead).mockReturnValue({
      mutate: markRead,
      isPending: false,
    } as never);
    vi.mocked(useAcceptProjectInvitation).mockReturnValue({
      mutateAsync,
      isPending: false,
    } as never);

    renderHeader("/");

    await user.click(screen.getByRole("button", { name: "Notifications" }));
    await user.click(screen.getByRole("button", { name: "Accept" }));

    expect(mutateAsync).toHaveBeenCalledWith({ invitation_id: "invitation-1" });
    expect(markRead).toHaveBeenCalledWith("notification-1");
    await waitFor(() => {
      expect(screen.getByText("INVITE ACCEPT PAGE")).toBeInTheDocument();
    });
  });

  it("hides an invitation notification after successful inline acceptance", async () => {
    const user = userEvent.setup();
    const mutateAsync = vi.fn().mockResolvedValue({
      project_id: "project-1",
      member_id: "member-1",
    });

    vi.mocked(useNotifications).mockReturnValue({
      data: {
        items: [
          {
            id: "notification-1",
            type: "invitation_received",
            title: "Invited to Project Alpha",
            message: "Owner invited you.",
            entity_type: "project_invitation",
            entity_id: "invitation-1",
            is_read: false,
            created_at: new Date().toISOString(),
          },
        ],
        total: 1,
        page: 1,
        per_page: 20,
        total_pages: 1,
        unread_count: 1,
      },
      isLoading: false,
      isError: false,
    } as never);
    vi.mocked(useAcceptProjectInvitation).mockReturnValue({
      mutateAsync,
      isPending: false,
    } as never);

    renderHeader("/");

    await user.click(screen.getByRole("button", { name: "Notifications" }));
    await user.click(screen.getByRole("button", { name: "Accept" }));

    await waitFor(() => {
      expect(screen.queryByText("Invited to Project Alpha")).not.toBeInTheDocument();
      expect(screen.getByText("No notifications yet.")).toBeInTheDocument();
    });
  });

  it("hides stale invitation notifications after a terminal accept error", async () => {
    const user = userEvent.setup();
    const mutateAsync = vi.fn().mockRejectedValue(new Error("Invitation already accepted"));

    vi.mocked(useNotifications).mockReturnValue({
      data: {
        items: [
          {
            id: "notification-1",
            type: "invitation_received",
            title: "Invited to Project Alpha",
            message: "Owner invited you.",
            entity_type: "project_invitation",
            entity_id: "invitation-1",
            is_read: false,
            created_at: new Date().toISOString(),
          },
        ],
        total: 1,
        page: 1,
        per_page: 20,
        total_pages: 1,
        unread_count: 1,
      },
      isLoading: false,
      isError: false,
    } as never);
    vi.mocked(useAcceptProjectInvitation).mockReturnValue({
      mutateAsync,
      isPending: false,
    } as never);

    renderHeader("/");

    await user.click(screen.getByRole("button", { name: "Notifications" }));
    await user.click(screen.getByRole("button", { name: "Accept" }));

    await waitFor(() => {
      expect(screen.queryByText("Invited to Project Alpha")).not.toBeInTheDocument();
      expect(screen.getByText("No notifications yet.")).toBeInTheDocument();
    });
  });

  it("hides the message preview on invitation notifications", async () => {
    const user = userEvent.setup();

    vi.mocked(useNotifications).mockReturnValue({
      data: {
        items: [
          {
            id: "notification-1",
            type: "invitation_received",
            title: "Invited to Project Alpha",
            message: "Owner invited you.",
            entity_type: "project_invitation",
            entity_id: "invitation-1",
            is_read: false,
            created_at: new Date().toISOString(),
          },
        ],
        total: 1,
        page: 1,
        per_page: 20,
        total_pages: 1,
        unread_count: 1,
      },
      isLoading: false,
      isError: false,
    } as never);

    renderHeader("/");

    await user.click(screen.getByRole("button", { name: "Notifications" }));

    expect(screen.queryByText("Owner invited you.")).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Review" })).toBeInTheDocument();
  });
});
