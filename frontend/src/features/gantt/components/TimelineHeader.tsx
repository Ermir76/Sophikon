import { useMemo } from "react";
import type { ZoomLevel } from "../types";
import { getTimelineUnits, dateToX } from "../utils/dateUtils";

interface TimelineHeaderProps {
  chartStartDate: Date;
  chartEndDate: Date;
  zoom: ZoomLevel;
  pxPerDay: number;
  totalWidth: number;
  headerHeight: number;
}

export function TimelineHeader({
  chartStartDate,
  chartEndDate,
  zoom,
  pxPerDay,
  totalWidth,
  headerHeight,
}: TimelineHeaderProps) {
  const { topTier, bottomTier } = useMemo(
    () => getTimelineUnits(chartStartDate, chartEndDate, zoom, pxPerDay),
    [chartStartDate, chartEndDate, zoom, pxPerDay],
  );

  const tierHeight = headerHeight / 2;

  return (
    <div
      className="relative border-b border-border bg-muted/80 select-none"
      style={{ width: totalWidth, height: headerHeight }}
    >
      {/* Top tier */}
      {topTier.map((unit, i) => {
        const x = dateToX(unit.startDate, chartStartDate, pxPerDay);
        return (
          <div
            key={`top-${i}`}
            className="absolute flex items-center justify-center border-r border-border text-[11px] font-medium text-muted-foreground overflow-hidden"
            style={{ left: x, top: 0, width: unit.width, height: tierHeight }}
          >
            {unit.label}
          </div>
        );
      })}

      {/* Divider */}
      <div
        className="absolute left-0 w-full border-b border-border"
        style={{ top: tierHeight }}
      />

      {/* Bottom tier */}
      {bottomTier.map((unit, i) => {
        const x = dateToX(unit.startDate, chartStartDate, pxPerDay);
        return (
          <div
            key={`bot-${i}`}
            className={`absolute flex items-center justify-center border-r border-border text-[10px] overflow-hidden ${
              unit.isToday
                ? "bg-destructive/15 text-destructive font-semibold"
                : "text-muted-foreground"
            }`}
            style={{
              left: x,
              top: tierHeight,
              width: unit.width,
              height: tierHeight,
            }}
          >
            {unit.label}
          </div>
        );
      })}
    </div>
  );
}
