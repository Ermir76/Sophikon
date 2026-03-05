import { cn } from "@/shared/lib/utils";
import { Input } from "@/shared/ui/input";
import { Label } from "@/shared/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/shared/ui/select";
import type { TimeWindowPreset } from "@/shared/types/insights";

interface TimeWindowFilterProps {
  value: TimeWindowPreset;
  startDate?: string;
  endDate?: string;
  onChange: (value: TimeWindowPreset) => void;
  onCustomRangeChange: (startDate?: string, endDate?: string) => void;
  className?: string;
}

export function TimeWindowFilter({
  value,
  startDate,
  endDate,
  onChange,
  onCustomRangeChange,
  className,
}: TimeWindowFilterProps) {
  return (
    <div className={cn("flex flex-wrap items-end gap-2", className)}>
      <div className="min-w-[140px]">
        <Label className="mb-1 block text-xs text-muted-foreground">Window</Label>
        <Select value={value} onValueChange={(next) => onChange(next as TimeWindowPreset)}>
          <SelectTrigger className="h-9">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="7d">Last 7 days</SelectItem>
            <SelectItem value="30d">Last 30 days</SelectItem>
            <SelectItem value="90d">Last 90 days</SelectItem>
            <SelectItem value="custom">Custom</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {value === "custom" && (
        <>
          <div>
            <Label className="mb-1 block text-xs text-muted-foreground">Start</Label>
            <Input
              type="date"
              className="h-9"
              value={startDate ?? ""}
              onChange={(e) => onCustomRangeChange(e.target.value || undefined, endDate)}
            />
          </div>
          <div>
            <Label className="mb-1 block text-xs text-muted-foreground">End</Label>
            <Input
              type="date"
              className="h-9"
              value={endDate ?? ""}
              onChange={(e) => onCustomRangeChange(startDate, e.target.value || undefined)}
            />
          </div>
        </>
      )}
    </div>
  );
}
