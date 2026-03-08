import { formatDistanceToNow } from "date-fns";

import type { ProjectActivityItem } from "@/features/projects/types";
import { getErrorMessage } from "@/shared/lib/errors";
import { cn } from "@/shared/lib/utils";
import { Badge } from "@/shared/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/shared/ui/card";

interface ProjectActivityFeedCardProps {
  items: ProjectActivityItem[];
  isLoading?: boolean;
  isError?: boolean;
  error?: unknown;
  className?: string;
  contentClassName?: string;
  listClassName?: string;
}

const ENTITY_LABELS: Record<ProjectActivityItem["entity_type"], string> = {
  project: "Project",
  task: "Task",
  resource: "Resource",
  assignment: "Assignment",
  dependency: "Dependency",
  project_member: "Member",
  comment: "Comment",
};

const ACTION_LABELS: Record<ProjectActivityItem["action"], string> = {
  created: "created",
  updated: "updated",
  deleted: "deleted",
  restored: "restored",
};

function renderChangeSummary(item: ProjectActivityItem) {
  if (!item.changes?.fields.length) {
    return null;
  }

  const labels = item.changes.fields.map((field) => field.field.replaceAll("_", " "));
  if (labels.length === 1) {
    return `Changed ${labels[0]}.`;
  }
  if (labels.length === 2) {
    return `Changed ${labels[0]} and ${labels[1]}.`;
  }
  return `Changed ${labels[0]} and ${labels.length - 1} other fields.`;
}

export function ProjectActivityFeedCard({
  items,
  isLoading = false,
  isError = false,
  error,
  className,
  contentClassName,
  listClassName,
}: ProjectActivityFeedCardProps) {
  return (
    <Card className={cn("py-4", className)}>
      <CardHeader className="px-4">
        <CardTitle className="text-sm font-semibold">Recent Project Activity</CardTitle>
      </CardHeader>
      <CardContent className={cn("px-4 min-h-0", contentClassName)}>
        {isLoading ? (
          <p className="text-sm text-muted-foreground">Loading project activity...</p>
        ) : isError ? (
          <div className="rounded-lg border border-dashed p-4 text-sm text-muted-foreground">
            {getErrorMessage(error)}
          </div>
        ) : items.length === 0 ? (
          <p className="text-sm text-muted-foreground">No recent activity for this project.</p>
        ) : (
          <ul className={cn("space-y-2.5", listClassName)}>
            {items.map((item) => {
              const actorName = item.user?.full_name ?? "Someone";
              const actionLabel = ACTION_LABELS[item.action];
              const changeSummary = renderChangeSummary(item);

              return (
                <li key={item.id} className="rounded-lg border border-border/60 p-3">
                  <div className="flex items-start justify-between gap-2">
                    <div className="min-w-0 flex items-center gap-2">
                      <Badge variant="outline" className="uppercase tracking-wide">
                        {ENTITY_LABELS[item.entity_type]}
                      </Badge>
                      <span className="truncate text-sm font-medium">{item.entity_name}</span>
                    </div>
                    <span className="shrink-0 text-xs text-muted-foreground">
                      {formatDistanceToNow(new Date(item.created_at), { addSuffix: true })}
                    </span>
                  </div>
                  <p className="mt-1 text-xs text-muted-foreground">
                    {actorName} {actionLabel} this {ENTITY_LABELS[item.entity_type].toLowerCase()}.
                  </p>
                  {changeSummary ? (
                    <p className="mt-1 text-xs text-muted-foreground">{changeSummary}</p>
                  ) : null}
                </li>
              );
            })}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}
