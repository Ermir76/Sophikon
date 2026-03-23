import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { KanbanColumnHeader } from "./KanbanColumnHeader";
import type { KanbanColumn } from "../types";

const backlogCol: KanbanColumn = {
    id: "BACKLOG",
    label: "Backlog",
    color: "text-muted-foreground",
};

describe("KanbanColumnHeader", () => {
    it("renders column label and count", () => {
        render(<KanbanColumnHeader column={backlogCol} count={7} />);
        expect(screen.getByText("Backlog")).toBeInTheDocument();
        expect(screen.getByText("7")).toBeInTheDocument();
    });

    it("add button has correct aria-label", () => {
        render(<KanbanColumnHeader column={backlogCol} count={0} />);
        expect(screen.getByRole("button", { name: "Add task to Backlog" })).toBeInTheDocument();
    });

    it("calls onAdd when add button is clicked", async () => {
        const onAdd = vi.fn();
        render(<KanbanColumnHeader column={backlogCol} count={0} onAdd={onAdd} />);
        await userEvent.click(screen.getByRole("button", { name: "Add task to Backlog" }));
        expect(onAdd).toHaveBeenCalledOnce();
    });

    it("shows count and warning state for exceeded WIP limit", () => {
        render(<KanbanColumnHeader column={backlogCol} count={4} limit={3} isOverLimit />);
        expect(screen.getByText("4/3")).toBeInTheDocument();
        expect(screen.getByLabelText("Backlog WIP limit exceeded")).toBeInTheDocument();
    });

    it("saves WIP limit from popover", async () => {
        const onSetWipLimit = vi.fn();
        const user = userEvent.setup();

        render(
            <KanbanColumnHeader
                column={backlogCol}
                count={2}
                onSetWipLimit={onSetWipLimit}
            />,
        );

        await user.click(screen.getByRole("button", { name: "Set WIP limit for Backlog" }));
        const input = screen.getByRole("spinbutton", { name: "WIP limit value for Backlog" });
        await user.clear(input);
        await user.type(input, "5");
        await user.click(screen.getByRole("button", { name: "Save" }));

        expect(onSetWipLimit).toHaveBeenCalledWith(5);
    });

    it("clears WIP limit from popover", async () => {
        const onSetWipLimit = vi.fn();
        const user = userEvent.setup();

        render(
            <KanbanColumnHeader
                column={backlogCol}
                count={2}
                limit={4}
                onSetWipLimit={onSetWipLimit}
            />,
        );

        await user.click(screen.getByRole("button", { name: "Set WIP limit for Backlog" }));
        await user.click(screen.getByRole("button", { name: "Clear" }));

        expect(onSetWipLimit).toHaveBeenCalledWith(null);
    });
});
