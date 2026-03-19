import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { PriorityFilter, TaskStatus } from "../types";

interface KanbanState {
    /** Collapsed column IDs keyed by projectId — persisted per project */
    collapsedByProject: Record<string, TaskStatus[]>;
    searchQuery: string;
    priorityFilter: PriorityFilter;
    toggleCollapse: (projectId: string, col: TaskStatus) => void;
    setSearch: (q: string) => void;
    setPriorityFilter: (f: PriorityFilter) => void;
}

export const useKanbanStore = create<KanbanState>()(
    persist(
        (set, get) => ({
            collapsedByProject: {},
            searchQuery: "",
            priorityFilter: "all",

            toggleCollapse: (projectId, col) => {
                const current = get().collapsedByProject[projectId] ?? [];
                const next = current.includes(col)
                    ? current.filter((c) => c !== col)
                    : [...current, col];
                set({
                    collapsedByProject: {
                        ...get().collapsedByProject,
                        [projectId]: next,
                    },
                });
            },

            setSearch: (q) => set({ searchQuery: q }),

            setPriorityFilter: (f) => set({ priorityFilter: f }),
        }),
        {
            name: "sophikon-kanban-storage",
            partialize: (state) => ({ collapsedByProject: state.collapsedByProject }),
        },
    ),
);
