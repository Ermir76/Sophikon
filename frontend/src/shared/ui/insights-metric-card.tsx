import { Link } from "react-router";
import { Card, CardContent, CardHeader, CardTitle } from "@/shared/ui/card";
import { cn } from "@/shared/lib/utils";

interface InsightsMetricCardProps {
  label: string;
  value: string | number;
  hint?: string;
  to?: string;
  className?: string;
  compact?: boolean;
  valueClassName?: string;
}

export function InsightsMetricCard({
  label,
  value,
  hint,
  to,
  className,
  compact = false,
  valueClassName,
}: InsightsMetricCardProps) {
  const content = (
    <Card className={cn(compact ? "gap-2 py-3" : "gap-3 py-4", className)}>
      <CardHeader className={cn(compact ? "px-3" : "px-4")}>
        <CardTitle className={cn("font-medium tracking-wide text-muted-foreground", compact ? "text-[10px]" : "text-[11px]")}>
          {label}
        </CardTitle>
      </CardHeader>
      <CardContent className={cn(compact ? "px-3" : "px-4")}>
        <div
          className={cn(
            "leading-none font-semibold tabular-nums",
            compact ? "text-[1.45rem]" : "text-[1.65rem]",
            valueClassName,
          )}
        >
          {value}
        </div>
        {hint && <p className="mt-1 text-xs text-muted-foreground">{hint}</p>}
      </CardContent>
    </Card>
  );

  if (!to) return content;

  return (
    <Link to={to} className="block transition-opacity hover:opacity-90">
      {content}
    </Link>
  );
}
