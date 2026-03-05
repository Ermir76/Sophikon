import type { TimeWindowSelection } from "@/shared/types/insights";

export function buildInsightsWindowParams(window: TimeWindowSelection) {
  const params: Record<string, string> = {
    window_preset: window.windowPreset,
  };

  if (window.windowPreset === "custom") {
    if (window.startDate) params.start_date = window.startDate;
    if (window.endDate) params.end_date = window.endDate;
  }

  return params;
}
