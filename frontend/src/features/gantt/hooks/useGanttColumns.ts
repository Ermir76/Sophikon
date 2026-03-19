import { useGanttPanelStore } from "../store/gantt-panel-store";

export function useGanttColumns() {
  const { getColumns, setColumnWidth, toggleColumnVisibility } = useGanttPanelStore();
  const columns = getColumns();
  const visibleColumns = columns.filter((c) => c.visible);
  return { columns, visibleColumns, setColumnWidth, toggleColumnVisibility };
}
