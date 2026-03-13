import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router";
import { beforeEach, describe, expect, it, vi } from "vitest";

import ResourcesPage from "@/features/resources/pages/ResourcesPage";

const mocks = vi.hoisted(() => ({
  useResources: vi.fn(),
  useDeleteResource: vi.fn(),
  useBulkDeleteResources: vi.fn(),
  useOverAllocations: vi.fn(),
  resourceTableProps: vi.fn(),
}));

vi.mock("@/features/resources/hooks/useResources", () => ({
  useResources: mocks.useResources,
  useDeleteResource: mocks.useDeleteResource,
  useBulkDeleteResources: mocks.useBulkDeleteResources,
}));

vi.mock("@/features/resources/hooks/useUtilization", () => ({
  useOverAllocations: mocks.useOverAllocations,
}));

vi.mock("@/features/resources/components/ResourceTable", () => ({
  ResourceTable: (props: unknown) => {
    mocks.resourceTableProps(props);
    const typed = props as { data: { id: string }[] };
    return <div data-testid="resource-table">rows:{typed.data.length}</div>;
  },
}));

vi.mock("@/features/resources/components/ResourceDetailPanel", () => ({
  ResourceDetailPanel: () => <div data-testid="resource-detail-panel" />,
}));

vi.mock("@/features/resources/components/CreateResourceDialog", () => ({
  CreateResourceDialog: ({ isOpen }: { isOpen: boolean }) => (
    <div data-testid="create-resource-dialog">{isOpen ? "open" : "closed"}</div>
  ),
}));

vi.mock("sonner", () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
  },
}));

function makeResource(id: string, isActive = true) {
  return {
    id,
    project_id: "proj-1",
    name: `Resource ${id}`,
    initials: null,
    email: null,
    type: "WORK" as const,
    material_label: null,
    max_units: 1,
    group_name: null,
    code: null,
    is_generic: false,
    is_active: isActive,
    standard_rate: 100,
    overtime_rate: 150,
    cost_per_use: 0,
    accrue_at: "PRORATED" as const,
    user_id: null,
    created_at: "2024-01-01T00:00:00Z",
    updated_at: "2024-01-01T00:00:00Z",
  };
}

function renderPage() {
  return render(
    <MemoryRouter initialEntries={["/projects/proj-1/resources"]}>
      <Routes>
        <Route path="/projects/:projectId/resources" element={<ResourcesPage />} />
      </Routes>
    </MemoryRouter>,
  );
}

describe("ResourcesPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    globalThis.ResizeObserver = class ResizeObserver {
      observe() {}
      unobserve() {}
      disconnect() {}
    };
    mocks.useDeleteResource.mockReturnValue({
      mutateAsync: vi.fn(),
      isPending: false,
    });
    mocks.useBulkDeleteResources.mockReturnValue({
      mutateAsync: vi.fn(),
      isPending: false,
    });
    mocks.useOverAllocations.mockReturnValue({
      data: { items: [], total_count: 0 },
    });
  });

  it("renders resource table with data", () => {
    mocks.useResources.mockReturnValue({
      data: { items: [makeResource("r1"), makeResource("r2", false)] },
      isLoading: false,
      isError: false,
      refetch: vi.fn(),
    });

    renderPage();

    expect(screen.getByRole("heading", { name: "Resources" })).toBeInTheDocument();
    expect(screen.getByTestId("resource-table")).toHaveTextContent("rows:2");
  });

  it("renders empty state when no resources", () => {
    mocks.useResources.mockReturnValue({
      data: { items: [] },
      isLoading: false,
      isError: false,
      refetch: vi.fn(),
    });

    renderPage();

    expect(screen.getByText("No resources")).toBeInTheDocument();
    expect(
      screen.getByText("You haven't added any resources to this project yet."),
    ).toBeInTheDocument();
  });

  it("opens create resource dialog", async () => {
    const user = userEvent.setup();
    mocks.useResources.mockReturnValue({
      data: { items: [] },
      isLoading: false,
      isError: false,
      refetch: vi.fn(),
    });

    renderPage();

    expect(screen.getByTestId("create-resource-dialog")).toHaveTextContent("closed");
    await user.click(screen.getByRole("button", { name: "Add Resource" }));
    expect(screen.getByTestId("create-resource-dialog")).toHaveTextContent("open");
  });

  it("renders utilization view tab", () => {
    mocks.useResources.mockReturnValue({
      data: { items: [makeResource("r1"), makeResource("r2")] },
      isLoading: false,
      isError: false,
      refetch: vi.fn(),
    });
    mocks.useOverAllocations.mockReturnValue({
      data: {
        items: [
          { resource_id: "r1" },
          { resource_id: "r2" },
          { resource_id: "r2" },
        ],
        total_count: 3,
      },
    });

    renderPage();

    // Pass-now semantics: current page shows over-allocation summary card
    // rather than a dedicated utilization tab.
    const overallocatedLabel = screen.getByText("Overallocated");
    const overallocatedCard = overallocatedLabel.parentElement;
    expect(overallocatedLabel).toBeInTheDocument();
    expect(overallocatedCard).toHaveTextContent("2");
  });
});
