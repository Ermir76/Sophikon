import { create } from "zustand";
import { persist } from "zustand/middleware";
import { DEFAULT_COLUMNS } from "../types";
import type { GanttColumn } from "../types";

interface GanttPanelStore {
  columnWidths: Record<string, number>;
  columnVisibility: Record<string, boolean>;
  setColumnWidth: (id: string, width: number) => void;
  toggleColumnVisibility: (id: string) => void;
  getColumns: () => GanttColumn[];
}

export const useGanttPanelStore = create<GanttPanelStore>()(
  persist(
    (set, get) => ({
      columnWidths: {},
      columnVisibility: {},

      setColumnWidth: (id, width) =>
        set((state) => ({ columnWidths: { ...state.columnWidths, [id]: width } })),

      toggleColumnVisibility: (id) => {
        if (id === "name") return;
        set((state) => {
          const current = state.columnVisibility[id] ?? true;
          return { columnVisibility: { ...state.columnVisibility, [id]: !current } };
        });
      },

      getColumns: () => {
        const { columnWidths, columnVisibility } = get();
        return DEFAULT_COLUMNS.map((col) => ({
          ...col,
          width: columnWidths[col.id] ?? col.width,
          visible: columnVisibility[col.id] ?? col.visible,
        }));
      },
    }),
    { name: "sophikon-gantt-panel" },
  ),
);
