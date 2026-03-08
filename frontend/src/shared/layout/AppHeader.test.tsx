import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { useProjectWebSocketStore } from "@/features/projects/store/websocket-store";
import { AppHeader } from "@/shared/layout/AppHeader";

vi.mock("@/shared/ui/sidebar", () => ({
  SidebarTrigger: () => <button type="button">Menu</button>,
}));

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
});
