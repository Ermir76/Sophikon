import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { KanbanLaneMode, KanbanWipLimits, PriorityFilter, TaskStatus } from "../types";

interface KanbanState {
    /** Collapsed column IDs keyed by projectId and persisted per project */
    collapsedByProject: Record<string, TaskStatus[]>;
    laneModeByProject: Record<string, KanbanLaneMode>;
    searchQuery: string;
    priorityFilter: PriorityFilter;
    selectedTaskId: string | null;
    detailTaskId: string | null;
    wipLimitsByProject: Record<string, KanbanWipLimits>;
    toggleCollapse: (projectId: string, col: TaskStatus) => void;
    setProjectLaneMode: (projectId: string, laneMode: KanbanLaneMode) => void;
    setSearch: (q: string) => void;
    setPriorityFilter: (f: PriorityFilter) => void;
    setSelectedTaskId: (taskId: string) => void;
    clearSelectedTaskId: () => void;
    setDetailTaskId: (taskId: string) => void;
    clearDetailTaskId: () => void;
    setProjectWipLimits: (projectId: string, limits: KanbanWipLimits) => void;
    setColumnWipLimit: (
        projectId: string,
        col: TaskStatus,
        limit: number | null,
    ) => void;
}

export const useKanbanStore = create<KanbanState>()(
    persist(
        (set, get) => ({
            collapsedByProject: {},
            laneModeByProject: {},
            searchQuery: "",
            priorityFilter: "all",
            selectedTaskId: null,
            detailTaskId: null,
            wipLimitsByProject: {},

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

            setProjectLaneMode: (projectId, laneMode) =>
                set({
                    laneModeByProject: {
                        ...get().laneModeByProject,
                        [projectId]: laneMode,
                    },
                }),

            setSearch: (q) => set({ searchQuery: q }),

            setPriorityFilter: (f) => set({ priorityFilter: f }),

            setSelectedTaskId: (taskId) => set({ selectedTaskId: taskId }),

            clearSelectedTaskId: () => set({ selectedTaskId: null }),

            setDetailTaskId: (taskId) => set({ detailTaskId: taskId }),

            clearDetailTaskId: () => set({ detailTaskId: null }),

            setProjectWipLimits: (projectId, limits) =>
                set({
                    wipLimitsByProject: {
                        ...get().wipLimitsByProject,
                        [projectId]: limits,
                    },
                }),

            setColumnWipLimit: (projectId, col, limit) => {
                const current = get().wipLimitsByProject[projectId] ?? {};
                const next = { ...current };
                if (limit === null) {
                    delete next[col];
                } else {
                    next[col] = limit;
                }
                set({
                    wipLimitsByProject: {
                        ...get().wipLimitsByProject,
                        [projectId]: next,
                    },
                });
            },
        }),
        {
            name: "sophikon-kanban-storage",
            partialize: (state) => ({
                collapsedByProject: state.collapsedByProject,
                laneModeByProject: state.laneModeByProject,
            }),
        },
    ),
);
