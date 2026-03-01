import { ZoomIn, ZoomOut, Maximize2, Route, CalendarDays } from "lucide-react";
import { Button } from "@/shared/ui/button";
import type { ZoomLevel } from "../types";

interface GanttToolbarProps {
  zoom: ZoomLevel;
  onZoomChange: (zoom: ZoomLevel) => void;
  showCriticalPath: boolean;
  onToggleCriticalPath: () => void;
  onScrollToToday: () => void;
  onZoomToFit: () => void;
}

const ZOOM_ORDER: ZoomLevel[] = ["month", "week", "day"];

export function GanttToolbar({
  zoom,
  onZoomChange,
  showCriticalPath,
  onToggleCriticalPath,
  onScrollToToday,
  onZoomToFit,
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

      <div className="w-px h-5 bg-border mx-1" />

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
    </div>
  );
}
