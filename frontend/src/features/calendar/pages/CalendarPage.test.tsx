import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import CalendarPage from "@/features/calendar/pages/CalendarPage";
import { useAuthStore, type AuthState } from "@/features/auth";
import { useProjectMembers, useProject, useUpdateProject } from "@/features/projects";
import {
  useCalendarExceptions,
  useCalendars,
  useCreateCalendar,
  useCreateCalendarException,
  useDeleteCalendar,
  useDeleteCalendarException,
  useUpdateCalendar,
  useUpdateCalendarException,
} from "@/features/calendar";

vi.mock("react-router", async () => {
  const actual = await vi.importActual<typeof import("react-router")>("react-router");
  return {
    ...actual,
    useParams: () => ({ projectId: "project-1" }),
  };
});

vi.mock("@/features/auth", () => ({
  useAuthStore: vi.fn(),
}));

vi.mock("@/features/projects", () => ({
  useProjectMembers: vi.fn(),
  useProject: vi.fn(),
  useUpdateProject: vi.fn(),
}));

vi.mock("@/features/calendar", () => ({
  useCalendars: vi.fn(),
  useCalendarExceptions: vi.fn(),
  useCreateCalendar: vi.fn(),
  useUpdateCalendar: vi.fn(),
  useDeleteCalendar: vi.fn(),
  useCreateCalendarException: vi.fn(),
  useUpdateCalendarException: vi.fn(),
  useDeleteCalendarException: vi.fn(),
}));

const projectMock = {
  id: "project-1",
  owner_id: "user-1",
  default_calendar_id: null,
};

const calendarsMock = [
  {
    id: "cal-1",
    project_id: "project-1",
    base_calendar_id: null,
    name: "Standard",
    is_base: false,
    work_week: [null, null, null, null, null, null, null],
    created_at: "2026-01-01T00:00:00Z",
    updated_at: "2026-01-01T00:00:00Z",
  },
];

describe("CalendarPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(useAuthStore).mockImplementation((selector: (state: AuthState) => unknown) =>
      selector({ user: { id: "user-1" } } as AuthState),
    );
    vi.mocked(useProject).mockReturnValue({
      data: projectMock,
      isLoading: false,
    } as never);
    vi.mocked(useProjectMembers).mockReturnValue({
      data: { items: [{ user_id: "user-1", role: "owner" }] },
    } as never);
    vi.mocked(useCalendars).mockReturnValue({
      data: calendarsMock,
      isLoading: false,
      isError: false,
      refetch: vi.fn(),
    } as never);
    vi.mocked(useCalendarExceptions).mockReturnValue({
      data: [],
      isLoading: false,
    } as never);
    vi.mocked(useCreateCalendar).mockReturnValue({
      mutateAsync: vi.fn(),
      isPending: false,
    } as never);
    vi.mocked(useUpdateCalendar).mockReturnValue({
      mutateAsync: vi.fn(),
      isPending: false,
    } as never);
    vi.mocked(useDeleteCalendar).mockReturnValue({
      mutateAsync: vi.fn(),
      isPending: false,
    } as never);
    vi.mocked(useCreateCalendarException).mockReturnValue({
      mutateAsync: vi.fn(),
      isPending: false,
    } as never);
    vi.mocked(useUpdateCalendarException).mockReturnValue({
      mutateAsync: vi.fn(),
      isPending: false,
    } as never);
    vi.mocked(useDeleteCalendarException).mockReturnValue({
      mutateAsync: vi.fn(),
      isPending: false,
    } as never);
    vi.mocked(useUpdateProject).mockReturnValue({
      mutateAsync: vi.fn(),
      isPending: false,
    } as never);
  });

  it("renders calendar list and default-calendar control", () => {
    render(<CalendarPage />);

    expect(screen.getByRole("heading", { name: "Calendar" })).toBeInTheDocument();
    expect(screen.getByText("Calendars")).toBeInTheDocument();
    expect(screen.getByText("Project Default Calendar")).toBeInTheDocument();
    expect(screen.getAllByText("Standard").length).toBeGreaterThan(0);
  });

  it("opens create-calendar dialog", () => {
    render(<CalendarPage />);

    fireEvent.click(screen.getByRole("button", { name: /new calendar/i }));
    expect(screen.getByRole("heading", { name: "Create calendar" })).toBeInTheDocument();
  });

  it("shows empty state when no calendars exist", () => {
    vi.mocked(useCalendars).mockReturnValue({
      data: [],
      isLoading: false,
      isError: false,
      refetch: vi.fn(),
    } as never);

    render(<CalendarPage />);
    expect(screen.getByText("No calendars yet")).toBeInTheDocument();
  });
});
