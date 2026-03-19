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

    it("renders count of zero", () => {
        render(<KanbanColumnHeader column={backlogCol} count={0} />);
        expect(screen.getByText("0")).toBeInTheDocument();
    });
});
