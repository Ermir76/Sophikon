import { Link } from "react-router";
import { Card, CardContent, CardHeader, CardTitle } from "@/shared/ui/card";
import { cn } from "@/shared/lib/utils";

interface InsightsMetricCardProps {
  label: string;
  value: string | number;
  hint?: string;
  to?: string;
  className?: string;
}

export function InsightsMetricCard({
  label,
  value,
  hint,
  to,
  className,
}: InsightsMetricCardProps) {
  const content = (
    <Card className={cn("gap-3 py-4", className)}>
      <CardHeader className="px-4">
        <CardTitle className="text-xs font-medium text-muted-foreground">{label}</CardTitle>
      </CardHeader>
      <CardContent className="px-4">
        <div className="text-2xl font-semibold tabular-nums">{value}</div>
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
