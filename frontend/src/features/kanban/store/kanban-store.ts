import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { PriorityFilter, TaskStatus } from "../types";

interface KanbanState {
    /** Collapsed column IDs keyed by projectId and persisted per project */
    collapsedByProject: Record<string, TaskStatus[]>;
    searchQuery: string;
    priorityFilter: PriorityFilter;
    selectedTaskId: string | null;
    toggleCollapse: (projectId: string, col: TaskStatus) => void;
    setSearch: (q: string) => void;
    setPriorityFilter: (f: PriorityFilter) => void;
    setSelectedTaskId: (taskId: string) => void;
    clearSelectedTaskId: () => void;
}

export const useKanbanStore = create<KanbanState>()(
    persist(
        (set, get) => ({
            collapsedByProject: {},
            searchQuery: "",
            priorityFilter: "all",
            selectedTaskId: null,

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

            setSelectedTaskId: (taskId) => set({ selectedTaskId: taskId }),

            clearSelectedTaskId: () => set({ selectedTaskId: null }),
        }),
        {
            name: "sophikon-kanban-storage",
            partialize: (state) => ({ collapsedByProject: state.collapsedByProject }),
        },
    ),
);
