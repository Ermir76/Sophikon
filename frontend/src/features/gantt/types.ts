export type ZoomLevel = "day" | "week" | "month";

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
  rowHeight: 36,
  headerHeight: 50,
  barHeight: 24,
  barRadius: 4,
  milestoneSize: 16,
};

export const ZOOM_PX_PER_DAY: Record<ZoomLevel, number> = {
  day: 40,
  week: 16,
  month: 5,
};
