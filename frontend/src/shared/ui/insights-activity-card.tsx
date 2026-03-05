import { formatDistanceToNow } from "date-fns";
import { Card, CardContent, CardHeader, CardTitle } from "@/shared/ui/card";
import { Badge } from "@/shared/ui/badge";
import type { RecentActivityItem } from "@/shared/types/insights";

interface InsightsActivityCardProps {
  title: string;
  items: RecentActivityItem[];
  emptyMessage: string;
}

export function InsightsActivityCard({
  title,
  items,
  emptyMessage,
}: InsightsActivityCardProps) {
  return (
    <Card className="py-4">
      <CardHeader className="px-4">
        <CardTitle className="text-sm font-semibold">{title}</CardTitle>
      </CardHeader>
      <CardContent className="px-4">
        {items.length === 0 ? (
          <p className="text-sm text-muted-foreground">{emptyMessage}</p>
        ) : (
          <ul className="space-y-3">
            {items.map((item) => (
              <li key={`${item.entity_type}-${item.entity_id}-${item.timestamp}`} className="rounded-lg border border-border/60 p-3">
                <div className="flex items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <Badge variant="outline" className="uppercase tracking-wide">
                      {item.entity_type}
                    </Badge>
                    <span className="text-sm font-medium">{item.entity_name}</span>
                  </div>
                  <span className="text-xs text-muted-foreground">
                    {formatDistanceToNow(new Date(item.timestamp), { addSuffix: true })}
                  </span>
                </div>
                <p className="mt-1 text-xs text-muted-foreground">
                  {item.action === "created" ? "Created" : "Updated"}
                  {item.project_name ? ` in ${item.project_name}` : ""}
                </p>
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}
