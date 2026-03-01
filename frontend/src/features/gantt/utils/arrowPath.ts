import type { Task } from "@/features/tasks/types";
import type { GanttConfig } from "../types";
import { dateToX, differenceInCalendarDays } from "./dateUtils";

type DepType = "FS" | "FF" | "SS" | "SF";

/**
 * Builds an SVG path string for a dependency arrow between two tasks.
 */
export function buildArrowPath(
  pred: Task,
  succ: Task,
  predIndex: number,
  succIndex: number,
  type: DepType,
  chartStartDate: Date,
  pxPerDay: number,
  config: GanttConfig,
): string {
  const predStart = dateToX(new Date(pred.start_date), chartStartDate, pxPerDay);
  const predEnd =
    predStart +
    Math.max(
      differenceInCalendarDays(new Date(pred.finish_date), new Date(pred.start_date)) * pxPerDay,
      4,
    );
  const succStart = dateToX(new Date(succ.start_date), chartStartDate, pxPerDay);
  const succEnd =
    succStart +
    Math.max(
      differenceInCalendarDays(new Date(succ.finish_date), new Date(succ.start_date)) * pxPerDay,
      4,
    );

  const predCy = predIndex * config.rowHeight + config.rowHeight / 2;
  const succCy = succIndex * config.rowHeight + config.rowHeight / 2;

  let fromX: number;
  let toX: number;

  switch (type) {
    case "FS":
      fromX = predEnd;
      toX = succStart;
      break;
    case "SS":
      fromX = predStart;
      toX = succStart;
      break;
    case "FF":
      fromX = predEnd;
      toX = succEnd;
      break;
    case "SF":
      fromX = predStart;
      toX = succEnd;
      break;
  }

  // Build L/S shaped path
  const margin = 12;
  const goingRight = type === "FS" || type === "FF";
  const arrivingLeft = type === "FS" || type === "SS";

  // Simple routing: exit horizontally, then vertically, then horizontally to target
  const exitX = goingRight ? fromX + margin : fromX - margin;
  const enterX = arrivingLeft ? toX - margin : toX + margin;

  if (predIndex === succIndex) {
    // Same row — go under
    const detourY = predCy + config.rowHeight * 0.6;
    return `M ${fromX} ${predCy} L ${exitX} ${predCy} L ${exitX} ${detourY} L ${enterX} ${detourY} L ${enterX} ${succCy} L ${toX} ${succCy}`;
  }

  // Different rows — L or S shape
  const midY = succCy;
  return `M ${fromX} ${predCy} L ${exitX} ${predCy} L ${exitX} ${midY} L ${toX} ${midY}`;
}
