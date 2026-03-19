export type ZoomLevel = "day" | "week" | "month";

export interface GanttColumn {
  id: string;
  label: string;
  width: number;
  minWidth: number;
  visible: boolean;
}

export const DEFAULT_COLUMNS: GanttColumn[] = [
  { id: "wbs",    label: "WBS",       width: 56,  minWidth: 40,  visible: true },
  { id: "name",   label: "Task Name", width: 200, minWidth: 120, visible: true },
  { id: "start",  label: "Start",     width: 72,  minWidth: 56,  visible: true },
  { id: "finish", label: "Finish",    width: 72,  minWidth: 56,  visible: true },
  { id: "dur",    label: "Dur.",      width: 52,  minWidth: 40,  visible: true },
  { id: "slack",  label: "Slack",     width: 52,  minWidth: 40,  visible: true },
];

export interface GanttConfig {
  rowHeight: number;
  headerHeight: number;
  barHeight: number;
  barRadius: number;
  milestoneSize: number;
}

export interface TimelineUnit {
  label: string;
  startDate: Date;
  endDate: Date;
  width: number;
  isToday?: boolean;
}

export const DEFAULT_GANTT_CONFIG: GanttConfig = {
  rowHeight: 48,
  headerHeight: 50,
  barHeight: 36,
  barRadius: 4,
  milestoneSize: 16,
};

export const ZOOM_PX_PER_DAY: Record<ZoomLevel, number> = {
  day: 100,
  week: 70,
  month: 40,
};
