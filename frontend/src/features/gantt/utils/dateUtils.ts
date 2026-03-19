import {
  differenceInCalendarDays,
  addDays,
  startOfMonth,
  endOfMonth,
  startOfWeek,
  endOfWeek,
  startOfDay,
  format,
  eachMonthOfInterval,
  eachWeekOfInterval,
  eachDayOfInterval,
  isWeekend,
  isSameDay,
  startOfQuarter,
  eachQuarterOfInterval,
  endOfQuarter,
} from "date-fns";
import type { ZoomLevel, TimelineUnit } from "../types";

export function dateToX(date: Date, startDate: Date, pxPerDay: number): number {
  return differenceInCalendarDays(date, startDate) * pxPerDay;
}

export function xToDate(x: number, startDate: Date, pxPerDay: number): Date {
  return addDays(startDate, Math.round(x / pxPerDay));
}

/**
 * Render width for task bars.
 *
 * Non-milestone same-day tasks should still display as one full day at
 * the current zoom level instead of collapsing to a tiny pixel stub.
 */
export function taskSpanWidthPx(
  startDate: Date,
  finishDate: Date,
  pxPerDay: number,
): number {
  const spanDays = Math.max(
    differenceInCalendarDays(finishDate, startDate) + 1,
    1,
  );
  return Math.max(spanDays * pxPerDay, 4);
}

export function getTimelineUnits(
  rangeStart: Date,
  rangeEnd: Date,
  zoom: ZoomLevel,
  pxPerDay: number,
): { topTier: TimelineUnit[]; bottomTier: TimelineUnit[] } {
  const today = new Date();

  switch (zoom) {
    case "day":
      return {
        topTier: buildWeekUnits(rangeStart, rangeEnd, pxPerDay),
        bottomTier: buildDayUnits(rangeStart, rangeEnd, pxPerDay, today),
      };
    case "week":
      return {
        topTier: buildMonthUnits(rangeStart, rangeEnd, pxPerDay),
        bottomTier: buildWeekUnits(rangeStart, rangeEnd, pxPerDay),
      };
    case "month":
      return {
        topTier: buildQuarterUnits(rangeStart, rangeEnd, pxPerDay),
        bottomTier: buildMonthUnits(rangeStart, rangeEnd, pxPerDay),
      };
  }
}

function buildQuarterUnits(start: Date, end: Date, pxPerDay: number): TimelineUnit[] {
  return eachQuarterOfInterval({ start, end }).map((q) => {
    const qStart = startOfQuarter(q);
    const qEnd = endOfQuarter(q);
    return {
      label: `Q${Math.ceil((q.getMonth() + 1) / 3)} ${format(q, "yyyy")}`,
      startDate: qStart,
      endDate: qEnd,
      width: differenceInCalendarDays(qEnd, qStart) * pxPerDay,
    };
  });
}

function buildMonthUnits(start: Date, end: Date, pxPerDay: number): TimelineUnit[] {
  return eachMonthOfInterval({ start, end }).map((m) => {
    const mStart = startOfMonth(m);
    const mEnd = endOfMonth(m);
    return {
      label: format(m, "MMM yyyy"),
      startDate: mStart,
      endDate: mEnd,
      width: differenceInCalendarDays(mEnd, mStart) * pxPerDay,
    };
  });
}

function buildWeekUnits(start: Date, end: Date, pxPerDay: number): TimelineUnit[] {
  return eachWeekOfInterval({ start, end }, { weekStartsOn: 1 }).map((w) => {
    const wStart = startOfWeek(w, { weekStartsOn: 1 });
    const wEnd = endOfWeek(w, { weekStartsOn: 1 });
    return {
      label: `W${format(w, "w")}`,
      startDate: wStart,
      endDate: wEnd,
      width: 7 * pxPerDay,
    };
  });
}

function buildDayUnits(
  start: Date,
  end: Date,
  pxPerDay: number,
  today: Date,
): TimelineUnit[] {
  return eachDayOfInterval({ start, end }).map((d) => ({
    label: format(d, "d"),
    startDate: startOfDay(d),
    endDate: startOfDay(d),
    width: pxPerDay,
    isToday: isSameDay(d, today),
  }));
}

export function getProjectDateRange(
  tasks: { start_date: string; finish_date: string }[],
): { start: Date; end: Date } {
  if (tasks.length === 0) {
    const today = new Date();
    return { start: addDays(today, -7), end: addDays(today, 30) };
  }
  let minDate = new Date(tasks[0].start_date);
  let maxDate = new Date(tasks[0].finish_date);
  for (const t of tasks) {
    const s = new Date(t.start_date);
    const f = new Date(t.finish_date);
    if (s < minDate) minDate = s;
    if (f > maxDate) maxDate = f;
  }
  // Add padding
  return { start: addDays(minDate, -7), end: addDays(maxDate, 14) };
}

export { isWeekend, differenceInCalendarDays, format };
