import { render, screen, fireEvent } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { KanbanToolbar } from "./KanbanToolbar";
import type { PriorityFilter } from "./KanbanToolbar";

function renderToolbar(overrides?: Partial<Parameters<typeof KanbanToolbar>[0]>) {
    const props = {
        searchQuery: "",
        onSearchChange: vi.fn(),
        priorityFilter: "all" as PriorityFilter,
        onPriorityFilterChange: vi.fn(),
        laneMode: "none" as const,
        onLaneModeChange: vi.fn(),
        ...overrides,
    };
    return { ...render(<KanbanToolbar {...props} />), props };
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
});
