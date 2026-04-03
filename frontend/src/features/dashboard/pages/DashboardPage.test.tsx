import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router";
import { beforeEach, describe, expect, it, vi } from "vitest";

let mockActiveOrgId: string | null = null;

vi.mock("@/features/organizations", () => ({
  useOrgStore: vi.fn((selector: (state: { activeOrgId: string | null }) => unknown) =>
    selector({ activeOrgId: mockActiveOrgId })),
  useOrganization: vi.fn(),
  useOrganizations: vi.fn(),
}));

vi.mock("@/features/dashboard/hooks/useDashboardInsights", () => ({
  useDashboardInsights: vi.fn(),
}));

vi.mock("@/shared/hooks/useTimeWindowFilter", () => ({
  useTimeWindowFilter: vi.fn(() => ({
    window: { windowPreset: "30d" as const },
    windowPreset: "30d" as const,
    startDate: undefined,
    endDate: undefined,
    setPreset: vi.fn(),
    setCustomRange: vi.fn(),
    isCustomInvalid: false,
  })),
}));

vi.mock("@/shared/components/QueryError", () => ({
  QueryError: ({
    message,
    onRetry,
  }: {
    message: string;
    onRetry?: () => void;
  }) => (
    <div>
      <div>{message}</div>
      {onRetry ? (
        <button type="button" onClick={onRetry}>
          Retry
        </button>
      ) : null}
    </div>
  ),
}));

vi.mock("@/shared/components/layout/PageShell", () => ({
  PageShell: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}));

vi.mock("@/shared/components/layout/PageHeader", () => ({
  PageHeader: ({ title }: { title: string }) => <h1>{title}</h1>,
}));

vi.mock("@/shared/components/state/PageLoading", () => ({
  PageLoading: ({ message }: { message: string }) => <div>{message}</div>,
}));

vi.mock("@/shared/components/state/PageEmpty", () => ({
  PageEmpty: ({
    title,
    description,
  }: {
    title: string;
    description: string;
  }) => (
    <div>
      <div>{title}</div>
      <div>{description}</div>
    </div>
  ),
}));

vi.mock("@/shared/ui/time-window-filter", () => ({
  TimeWindowFilter: () => <div>Time filter</div>,
}));

vi.mock("@/shared/ui/insights-metric-card", () => ({
  InsightsMetricCard: ({
    label,
    to,
  }: {
    label: string;
    to?: string;
  }) =>
    to ? <a href={to}>{label}</a> : <div>{label}</div>,
}));

vi.mock("@/shared/ui/insights-trend-card", () => ({
  InsightsTrendCard: ({ title }: { title: string }) => <div>{title}</div>,
}));

vi.mock("@/shared/ui/insights-activity-card", () => ({
  InsightsActivityCard: ({ title }: { title: string }) => <div>{title}</div>,
}));

import DashboardPage from "@/features/dashboard/pages/DashboardPage";
import { useDashboardInsights } from "@/features/dashboard/hooks/useDashboardInsights";
import { useOrganization, useOrganizations } from "@/features/organizations";

function renderPage() {
  return render(
    <MemoryRouter>
      <DashboardPage />
    </MemoryRouter>,
  );
}

describe("DashboardPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockActiveOrgId = "org-1";

    vi.mocked(useOrganization).mockReturnValue({
      data: { id: "org-1", name: "Acme Org" },
      isLoading: false,
      isError: false,
      error: null,
    } as never);

    vi.mocked(useOrganizations).mockReturnValue({
      data: [{ id: "org-1", name: "Acme Org" }],
      isLoading: false,
      isError: false,
      error: null,
      refetch: vi.fn(),
    } as never);

    vi.mocked(useDashboardInsights).mockReturnValue({
      data: {
        kpis: {
          active_projects: 2,
          completed_projects: 1,
          task_completion_pct: 64.5,
          overdue_tasks: 3,
          critical_tasks: 1,
          overallocated_resources: 2,
        },
        project_health: [],
        trend: [],
        recent_activity: [],
      },
      isLoading: false,
      isFetching: false,
      isError: false,
      error: null,
      refetch: vi.fn(),
    } as never);
  });

  it("shows the loading state during org bootstrap when there is no active organization yet", () => {
    mockActiveOrgId = null;
    vi.mocked(useOrganization).mockReturnValue({
      data: undefined,
      isLoading: false,
      isError: false,
      error: null,
    } as never);
    vi.mocked(useOrganizations).mockReturnValue({
      data: undefined,
      isLoading: true,
      isError: false,
      error: null,
      refetch: vi.fn(),
    } as never);

    renderPage();

    expect(screen.getByText("Loading dashboard...")).toBeInTheDocument();
  });

  it("renders the org bootstrap error with retry when the organizations query fails before selection", async () => {
    const user = userEvent.setup();
    const refetchOrganizations = vi.fn();

    mockActiveOrgId = null;
    vi.mocked(useOrganization).mockReturnValue({
      data: undefined,
      isLoading: false,
      isError: false,
      error: null,
    } as never);
    vi.mocked(useOrganizations).mockReturnValue({
      data: undefined,
      isLoading: false,
      isError: true,
      error: new Error("Organizations unavailable"),
      refetch: refetchOrganizations,
    } as never);

    renderPage();

    expect(screen.getByText("Organizations unavailable")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Retry" }));
    expect(refetchOrganizations).toHaveBeenCalledOnce();
  });

  it("links all KPI cards to the projects list instead of a single project drill-down", () => {
    renderPage();

    for (const label of [
      "Active Projects",
      "Completed Projects",
      "Task Completion",
      "Overdue Tasks",
      "Critical Tasks",
      "Overallocated Resources",
    ]) {
      expect(screen.getByRole("link", { name: label })).toHaveAttribute("href", "/projects");
    }
  });
});
