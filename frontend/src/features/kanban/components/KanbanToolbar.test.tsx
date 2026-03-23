import { render, screen, fireEvent } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { KanbanToolbar } from "./KanbanToolbar";
import type { PriorityFilter } from "./KanbanToolbar";
import { TooltipProvider } from "@/shared/ui/tooltip";

function renderToolbar(overrides?: Partial<Parameters<typeof KanbanToolbar>[0]>) {
    const props = {
        searchQuery: "",
        onSearchChange: vi.fn(),
        priorityFilter: "all" as PriorityFilter,
        onPriorityFilterChange: vi.fn(),
        laneMode: "none" as const,
        onLaneModeChange: vi.fn(),
        selectionMode: false,
        selectedCount: 0,
        bulkMoveTarget: "TODO" as const,
        isBulkMovePending: false,
        onSelectionModeChange: vi.fn(),
        onBulkMoveTargetChange: vi.fn(),
        onBulkMove: vi.fn(),
        onClearSelection: vi.fn(),
        ...overrides,
    };
    return { ...render(<TooltipProvider><KanbanToolbar {...props} /></TooltipProvider>), props };
}

describe("KanbanToolbar", () => {
    it("renders search input with current value", () => {
        renderToolbar({ searchQuery: "auth" });
        expect(screen.getByPlaceholderText("Search tasks...")).toHaveValue("auth");
    });

    it("calls onSearchChange when user types", () => {
        const { props } = renderToolbar();
        const input = screen.getByPlaceholderText("Search tasks...");
        fireEvent.change(input, { target: { value: "deploy" } });
        expect(props.onSearchChange).toHaveBeenCalledWith("deploy");
    });

    it("renders priority and lane mode select triggers", () => {
        renderToolbar();
        expect(screen.getAllByRole("combobox")).toHaveLength(2);
    });

    it("renders keyboard shortcuts help control", () => {
        renderToolbar();
        expect(screen.getByRole("button", { name: "Keyboard shortcuts help" })).toBeInTheDocument();
    });

    it("calls onSelectionModeChange when toggle button is clicked", () => {
        const { props } = renderToolbar();
        fireEvent.click(screen.getByRole("button", { name: "Toggle bulk selection mode" }));
        expect(props.onSelectionModeChange).toHaveBeenCalledWith(true);
    });

    it("renders bulk controls when selection mode is enabled", () => {
        renderToolbar({ selectionMode: true, selectedCount: 2 });
        expect(screen.getByText("2 selected")).toBeInTheDocument();
        expect(screen.getByRole("button", { name: "Move selected" })).toBeInTheDocument();
        expect(screen.getByRole("button", { name: "Clear" })).toBeInTheDocument();
    });
});
