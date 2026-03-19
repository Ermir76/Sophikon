import { beforeEach, describe, expect, it } from "vitest";
import { useKanbanStore } from "./kanban-store";

const PROJECT = "proj-1";

describe("useKanbanStore", () => {
    beforeEach(() => {
        useKanbanStore.setState({
            collapsedByProject: {},
            searchQuery: "",
            priorityFilter: "all",
        });
    });

    it("initial state has no collapsed columns and empty search", () => {
        const state = useKanbanStore.getState();
        expect(state.collapsedByProject).toEqual({});
        expect(state.searchQuery).toBe("");
        expect(state.priorityFilter).toBe("all");
    });

    it("toggleCollapse adds column to the project's collapsed list", () => {
        useKanbanStore.getState().toggleCollapse(PROJECT, "BACKLOG");
        expect(useKanbanStore.getState().collapsedByProject[PROJECT]).toContain("BACKLOG");
    });

    it("toggleCollapse removes column on second call", () => {
        useKanbanStore.getState().toggleCollapse(PROJECT, "TODO");
        useKanbanStore.getState().toggleCollapse(PROJECT, "TODO");
        expect(useKanbanStore.getState().collapsedByProject[PROJECT]).not.toContain("TODO");
    });

    it("toggleCollapse manages multiple columns independently", () => {
        useKanbanStore.getState().toggleCollapse(PROJECT, "BACKLOG");
        useKanbanStore.getState().toggleCollapse(PROJECT, "DONE");
        useKanbanStore.getState().toggleCollapse(PROJECT, "BACKLOG");

        const collapsed = useKanbanStore.getState().collapsedByProject[PROJECT];
        expect(collapsed).not.toContain("BACKLOG");
        expect(collapsed).toContain("DONE");
    });

    it("collapsed columns are scoped per project", () => {
        useKanbanStore.getState().toggleCollapse("proj-1", "BACKLOG");
        useKanbanStore.getState().toggleCollapse("proj-2", "DONE");

        expect(useKanbanStore.getState().collapsedByProject["proj-1"]).toContain("BACKLOG");
        expect(useKanbanStore.getState().collapsedByProject["proj-1"]).not.toContain("DONE");
        expect(useKanbanStore.getState().collapsedByProject["proj-2"]).toContain("DONE");
        expect(useKanbanStore.getState().collapsedByProject["proj-2"]).not.toContain("BACKLOG");
    });

    it("setSearch updates searchQuery", () => {
        useKanbanStore.getState().setSearch("authentication");
        expect(useKanbanStore.getState().searchQuery).toBe("authentication");
    });

    it("setPriorityFilter updates priorityFilter", () => {
        useKanbanStore.getState().setPriorityFilter("high");
        expect(useKanbanStore.getState().priorityFilter).toBe("high");
    });
});
