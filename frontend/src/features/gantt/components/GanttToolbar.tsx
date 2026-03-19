import { ZoomIn, ZoomOut, Maximize2, Route, CalendarDays, Calculator, Loader2, AlertTriangle } from "lucide-react";
import { Button } from "@/shared/ui/button";
import { Separator } from "@/shared/ui/separator";
import type { ZoomLevel } from "../types";
import { ColumnVisibilityMenu } from "./ColumnVisibilityMenu";

interface GanttToolbarProps {
  zoom: ZoomLevel;
  onZoomChange: (zoom: ZoomLevel) => void;
  showCriticalPath: boolean;
  onToggleCriticalPath: () => void;
  criticalTaskCount: number;
  onScrollToToday: () => void;
  onZoomToFit: () => void;
  autoCalculate: boolean;
  onToggleAutoCalculate: () => void;
  onManualCalculate: () => void;
  isCalculating: boolean;
}

const ZOOM_ORDER: ZoomLevel[] = ["month", "week", "day"];

export function GanttToolbar({
  zoom,
  onZoomChange,
  showCriticalPath,
  onToggleCriticalPath,
  criticalTaskCount,
  onScrollToToday,
  onZoomToFit,
  autoCalculate,
  onToggleAutoCalculate,
  onManualCalculate,
  isCalculating,
}: GanttToolbarProps) {
  const zoomIndex = ZOOM_ORDER.indexOf(zoom);

  const handleZoomIn = () => {
    if (zoomIndex < ZOOM_ORDER.length - 1) {
      onZoomChange(ZOOM_ORDER[zoomIndex + 1]);
    }
  };

  const handleZoomOut = () => {
    if (zoomIndex > 0) {
      onZoomChange(ZOOM_ORDER[zoomIndex - 1]);
    }
  };

  return (
    <div className="flex items-center gap-1">
      <ColumnVisibilityMenu />
      <Separator orientation="vertical" className="mx-1 h-5" />
      <Button
        variant="outline"
        size="icon-sm"
        onClick={handleZoomOut}
        disabled={zoomIndex === 0}
        title="Zoom out"
      >
        <ZoomOut className="size-4" />
      </Button>
      <span className="text-xs text-muted-foreground w-12 text-center capitalize">
        {zoom}
      </span>
      <Button
        variant="outline"
        size="icon-sm"
        onClick={handleZoomIn}
        disabled={zoomIndex === ZOOM_ORDER.length - 1}
        title="Zoom in"
      >
        <ZoomIn className="size-4" />
      </Button>

      <Button
        variant="outline"
        size="icon-sm"
        onClick={onZoomToFit}
        title="Zoom to fit"
      >
        <Maximize2 className="size-4" />
      </Button>

      <Separator orientation="vertical" className="mx-1 h-5" />

      <Button
        variant="outline"
        size="icon-sm"
        onClick={onScrollToToday}
        title="Scroll to today"
      >
        <CalendarDays className="size-4" />
      </Button>

      <Button
        variant={showCriticalPath ? "default" : "outline"}
        size="icon-sm"
        onClick={onToggleCriticalPath}
        title="Toggle critical path"
      >
        <Route className="size-4" />
      </Button>
      {showCriticalPath && criticalTaskCount === 0 && (
        <span title="No critical path data — run Schedule → Calculate first">
          <AlertTriangle className="size-4 text-amber-500 shrink-0" />
        </span>
      )}

      <Separator orientation="vertical" className="mx-1 h-5" />

      {/* Schedule controls */}
      <Button
        variant="outline"
        size="icon-sm"
        onClick={onManualCalculate}
        disabled={isCalculating}
        title="Recalculate schedule"
      >
        {isCalculating ? (
          <Loader2 className="size-4 animate-spin" />
        ) : (
          <Calculator className="size-4" />
        )}
      </Button>

      <Button
        variant="outline"
        size="sm"
        onClick={onToggleAutoCalculate}
        title={autoCalculate ? "Switch to manual scheduling" : "Switch to auto scheduling"}
        className="h-7 gap-1.5 px-2 text-xs"
      >
        <span
          className={`inline-block size-2 rounded-full ${autoCalculate ? "bg-emerald-500" : "bg-muted-foreground/40"}`}
        />
        <span className="text-muted-foreground">
          {autoCalculate ? "Auto" : "Manual"}
        </span>
      </Button>
    </div>
  );
}
