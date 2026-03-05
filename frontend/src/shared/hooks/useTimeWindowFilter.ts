import { useMemo } from "react";
import { useSearchParams } from "react-router";
import type { TimeWindowPreset, TimeWindowSelection } from "@/shared/types/insights";

const DEFAULT_PRESET: TimeWindowPreset = "30d";
const PRESETS: TimeWindowPreset[] = ["7d", "30d", "90d", "custom"];

function normalizePreset(value: string | null): TimeWindowPreset {
  if (value && PRESETS.includes(value as TimeWindowPreset)) {
    return value as TimeWindowPreset;
  }
  return DEFAULT_PRESET;
}

export function useTimeWindowFilter(scope: string) {
  const [searchParams, setSearchParams] = useSearchParams();

  const windowKey = `${scope}_window`;
  const startKey = `${scope}_start`;
  const endKey = `${scope}_end`;

  const windowPreset = normalizePreset(searchParams.get(windowKey));
  const startDate = searchParams.get(startKey) ?? undefined;
  const endDate = searchParams.get(endKey) ?? undefined;

  const window = useMemo<TimeWindowSelection>(
    () => ({
      windowPreset,
      startDate,
      endDate,
    }),
    [windowPreset, startDate, endDate],
  );

  const setPreset = (preset: TimeWindowPreset) => {
    setSearchParams((prev) => {
      const next = new URLSearchParams(prev);
      next.set(windowKey, preset);
      if (preset !== "custom") {
        next.delete(startKey);
        next.delete(endKey);
      }
      return next;
    });
  };

  const setCustomRange = (nextStart?: string, nextEnd?: string) => {
    setSearchParams((prev) => {
      const next = new URLSearchParams(prev);
      next.set(windowKey, "custom");
      if (nextStart) next.set(startKey, nextStart);
      else next.delete(startKey);
      if (nextEnd) next.set(endKey, nextEnd);
      else next.delete(endKey);
      return next;
    });
  };

  const isCustomInvalid = windowPreset === "custom" && (!startDate || !endDate);

  return {
    window,
    windowPreset,
    startDate,
    endDate,
    isCustomInvalid,
    setPreset,
    setCustomRange,
  };
}
