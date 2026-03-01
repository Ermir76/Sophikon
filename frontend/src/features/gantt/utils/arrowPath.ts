import type { Task } from "@/features/tasks/types";
import type { GanttConfig } from "../types";
import { dateToX, differenceInCalendarDays } from "./dateUtils";

type DepType = "FS" | "FF" | "SS" | "SF";

/**
 * Turn a series of waypoints into a path string with rounded corners.
 * Each corner gets a quadratic Bézier with radius `r`.
 */
function roundedPolyline(pts: [number, number][], r: number): string {
  if (pts.length < 2) return "";
  const parts: string[] = [`M ${pts[0][0]} ${pts[0][1]}`];

  for (let i = 1; i < pts.length - 1; i++) {
    const [px, py] = pts[i - 1];
    const [cx, cy] = pts[i];
    const [nx, ny] = pts[i + 1];

    // Vectors into and out of the corner
    const dxIn = cx - px, dyIn = cy - py;
    const dxOut = nx - cx, dyOut = ny - cy;
    const lenIn = Math.hypot(dxIn, dyIn);
    const lenOut = Math.hypot(dxOut, dyOut);

    if (lenIn === 0 || lenOut === 0) {
      parts.push(`L ${cx} ${cy}`);
      continue;
    }

    const cr = Math.min(r, lenIn / 2, lenOut / 2);

    // Point where curve starts (on incoming segment)
    const sx = cx - (dxIn / lenIn) * cr;
    const sy = cy - (dyIn / lenIn) * cr;
    // Point where curve ends (on outgoing segment)
    const ex = cx + (dxOut / lenOut) * cr;
    const ey = cy + (dyOut / lenOut) * cr;

    parts.push(`L ${sx} ${sy}`);
    parts.push(`Q ${cx} ${cy} ${ex} ${ey}`);
  }

  const last = pts[pts.length - 1];
  parts.push(`L ${last[0]} ${last[1]}`);
  return parts.join(" ");
}

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

  const margin = 20;
  const r = 6; // corner radius
  const goingRight = type === "FS" || type === "FF";
  const arrivingLeft = type === "FS" || type === "SS";

  const exitX = goingRight ? fromX + margin : fromX - margin;
  const enterX = arrivingLeft ? toX - margin : toX + margin;

  let pts: [number, number][];

  if (predIndex === succIndex) {
    // Same row — detour under
    const detourY = predCy + config.rowHeight * 0.6;
    pts = [
      [fromX, predCy],
      [exitX, predCy],
      [exitX, detourY],
      [enterX, detourY],
      [enterX, succCy],
      [toX, succCy],
    ];
  } else {
    const needsS = arrivingLeft ? exitX > enterX : exitX < enterX;

    if (needsS) {
      const midY = (predCy + succCy) / 2;
      pts = [
        [fromX, predCy],
        [exitX, predCy],
        [exitX, midY],
        [enterX, midY],
        [enterX, succCy],
        [toX, succCy],
      ];
    } else {
      pts = [
        [fromX, predCy],
        [exitX, predCy],
        [exitX, succCy],
        [toX, succCy],
      ];
    }
  }

  return roundedPolyline(pts, r);
}
