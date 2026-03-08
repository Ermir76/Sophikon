import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import { beforeEach, describe, expect, it, vi } from "vitest";

import {
  useMarkAllNotificationsRead,
  useMarkNotificationRead,
  useNotifications,
  useNotificationSettings,
  useNotificationWebSocketStore,
  useUpdateNotificationSettings,
} from "@/features/notifications";
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

function renderHeader(pathname: string) {
  return render(
    <MemoryRouter initialEntries={[pathname]}>
      <AppHeader />
    </MemoryRouter>,
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
});
