import { useState } from "react";
import { format, parseISO } from "date-fns";
import { User, Calendar, Clock, ExternalLink, Trash2 } from "lucide-react";
import { Popover, PopoverAnchor, PopoverContent } from "@/shared/ui/popover";
import { Badge } from "@/shared/ui/badge";
import { Button } from "@/shared/ui/button";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/shared/ui/alert-dialog";
import { useAssignments } from "@/features/tasks/hooks/useAssignments";
import { useResources } from "@/features/resources";
import { useDeleteTask } from "@/features/tasks";
import type { Task } from "@/features/tasks";
import { toast } from "sonner";

interface GanttBarQuickInfoProps {
  task: Task;
  projectId: string;
  x: number;
  y: number;
  onClose: () => void;
  onOpenDetails: (taskId: string) => void;
}

function getStatus(pct: number): { label: string; variant: "secondary" | "default" | "outline" } {
  if (pct >= 100) return { label: "Done", variant: "default" };
  if (pct > 0) return { label: "In Progress", variant: "outline" };
  return { label: "Not Started", variant: "secondary" };
}

export function GanttBarQuickInfo({ task, projectId, x, y, onClose, onOpenDetails }: GanttBarQuickInfoProps) {
  const [showDelete, setShowDelete] = useState(false);
  const { data: assignments } = useAssignments(projectId, task.id);
  const { data: resourcesData } = useResources(projectId);
  const deleteTask = useDeleteTask(projectId);

  const resources = resourcesData?.items ?? [];
  const assigneeNames = assignments && assignments.length > 0
    ? assignments.map((a) => resources.find((r) => r.id === a.resource_id)?.name ?? "Unknown").join(", ")
    : null;

  const status = getStatus(task.percent_complete);
  const durationDays = Math.round(task.duration / 480);
  const startFormatted = format(parseISO(task.start_date.substring(0, 10)), "MMM d, yyyy");
  const finishFormatted = format(parseISO(task.finish_date.substring(0, 10)), "MMM d, yyyy");

  return (
    <>
      <Popover open onOpenChange={(open) => { if (!open) onClose(); }}>
        <PopoverAnchor asChild>
          <div className="fixed pointer-events-none" style={{ left: x, top: y, width: 0, height: 0 }} />
        </PopoverAnchor>
        <PopoverContent
          side="bottom"
          align="start"
          sideOffset={8}
          className="w-64 p-3 space-y-2.5"
          onInteractOutside={onClose}
          onEscapeKeyDown={onClose}
        >
          <p className="font-semibold text-sm leading-snug">{task.name}</p>

          <Badge variant={status.variant} className="text-xs">
            {status.label}
          </Badge>

          <div className="flex items-start gap-2 text-xs text-muted-foreground">
            <User className="size-3.5 mt-0.5 shrink-0" />
            <span>{assigneeNames ?? "Unassigned"}</span>
          </div>

          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <Calendar className="size-3.5 shrink-0" />
            <span>{startFormatted} → {finishFormatted}</span>
          </div>

          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <Clock className="size-3.5 shrink-0" />
            <span>{durationDays} {durationDays === 1 ? "day" : "days"}</span>
          </div>

          <div className="h-px bg-border" />

          <div className="flex gap-2">
            <Button
              size="sm"
              className="h-7 flex-1 text-xs"
              onClick={() => { onOpenDetails(task.id); onClose(); }}
            >
              <ExternalLink className="size-3 mr-1.5" />
              Open Details
            </Button>
            <Button
              size="sm"
              variant="ghost"
              className="h-7 text-xs text-destructive hover:text-destructive hover:bg-destructive/10"
              onClick={() => setShowDelete(true)}
            >
              <Trash2 className="size-3 mr-1.5" />
              Delete
            </Button>
          </div>
        </PopoverContent>
      </Popover>

      <AlertDialog open={showDelete} onOpenChange={(open) => { if (!open) setShowDelete(false); }}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete task?</AlertDialogTitle>
            <AlertDialogDescription>
              "{task.name}" will be permanently deleted. This cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
              onClick={() => {
                deleteTask.mutate(task.id, {
                  onSuccess: () => { toast.success("Task deleted"); onClose(); },
                  onError: () => toast.error("Failed to delete task"),
                });
              }}
            >
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
}
