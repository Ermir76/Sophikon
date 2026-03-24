import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { KanbanHealthSummary } from "./KanbanHealthSummary";
import type { AiSuggestion } from "@/features/ai/types";

const suggestion = (overrides: Partial<AiSuggestion> = {}): AiSuggestion => ({
    id: overrides.id ?? "s1",
    type: overrides.type ?? "RISK",
    severity: overrides.severity ?? "HIGH",
    title: overrides.title ?? "Task risk",
    description: overrides.description ?? "Risk details",
    affected_task_id: Object.prototype.hasOwnProperty.call(overrides, "affected_task_id")
        ? (overrides.affected_task_id ?? null)
        : "task-1",
    suggested_action: overrides.suggested_action ?? null,
});

function renderSummary(overrides?: Partial<Parameters<typeof KanbanHealthSummary>[0]>) {
    const props: Parameters<typeof KanbanHealthSummary>[0] = {
        suggestions: [],
        hasRequested: false,
        isLoading: false,
        isError: false,
        taskNameById: { "task-1": "Build API", "task-2": "QA" },
        onRetry: vi.fn(),
        onRiskClick: vi.fn(),
        ...overrides,
    };
    return { ...render(<KanbanHealthSummary {...props} />), props };
}

describe("KanbanHealthSummary", () => {
    it("shows the initial prompt before summary is requested", () => {
        renderSummary();
        expect(screen.getByText("Run Sprint Health to generate AI risk signals for this board.")).toBeInTheDocument();
    });

    it("renders grouped HIGH/MEDIUM risk suggestions", () => {
        renderSummary({
            suggestions: [
                suggestion({ id: "s1", severity: "HIGH", title: "Blocked by dependency", affected_task_id: "task-1" }),
                suggestion({ id: "s2", severity: "MEDIUM", title: "Tight schedule", affected_task_id: "task-1" }),
                suggestion({ id: "s3", severity: "LOW", title: "Low priority drift", affected_task_id: "task-2" }),
                suggestion({ id: "s4", severity: "HIGH", title: "Cross-team risk", affected_task_id: null }),
            ],
        });

        expect(screen.getByText("Build API")).toBeInTheDocument();
        expect(screen.getByText("Project-level risks")).toBeInTheDocument();
        expect(screen.getByText("Blocked by dependency")).toBeInTheDocument();
        expect(screen.getByText("Tight schedule")).toBeInTheDocument();
        expect(screen.getByText("Cross-team risk")).toBeInTheDocument();
        expect(screen.queryByText("Low priority drift")).not.toBeInTheDocument();
    });

    it("opens affected task when a task-scoped risk is clicked", async () => {
        const user = userEvent.setup();
        const { props } = renderSummary({
            suggestions: [suggestion({ title: "Blocked by dependency", affected_task_id: "task-1" })],
        });

        await user.click(screen.getByRole("button", { name: /Blocked by dependency/i }));
        expect(props.onRiskClick).toHaveBeenCalledWith("task-1");
    });

    it("shows error state with retry", async () => {
        const user = userEvent.setup();
        const { props } = renderSummary({ isError: true, hasRequested: true });

        expect(screen.getByText("Failed to load sprint health summary.")).toBeInTheDocument();
        await user.click(screen.getByRole("button", { name: "Retry" }));
        expect(props.onRetry).toHaveBeenCalled();
    });
});
