import { useDraggable } from "@dnd-kit/core";
import { AlertTriangle, MessageSquare } from "lucide-react";
import { Avatar, AvatarFallback } from "@/shared/ui/avatar";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/shared/ui/tooltip";
import type { Task } from "@/features/tasks";

function getPriorityBadge(priority: number) {
    if (priority >= 750) return { label: "HIGH", cls: "bg-orange-500/15 text-orange-600 dark:text-orange-400" };
    if (priority >= 500) return { label: "MED", cls: "bg-yellow-500/15 text-yellow-700 dark:text-yellow-400" };
    if (priority >= 250) return { label: "LOW", cls: "bg-muted text-muted-foreground" };
    return null;
}

function formatDeadline(dateStr: string) {
    return new Date(dateStr).toLocaleDateString("en-US", { month: "short", day: "numeric" });
}

function getLocalDateString(): string {
    const d = new Date();
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
}

function isOverdue(task: Task): boolean {
    if (task.status === "DONE") return false;
    return task.finish_date < getLocalDateString();
}

interface KanbanCardProps {
    task: Task;
    isDragOverlay?: boolean;
}

export function KanbanCard({ task, isDragOverlay = false }: KanbanCardProps) {
    const { setNodeRef, listeners, attributes, isDragging } = useDraggable({
        id: task.id,
        data: { status: task.status },
        disabled: isDragOverlay,
    });

    const badge = getPriorityBadge(task.priority);
    const overdue = isOverdue(task);
    const progress = Math.round(Number(task.percent_complete));

    return (
        <div
            ref={isDragOverlay ? undefined : setNodeRef}
            {...(isDragOverlay ? {} : listeners)}
            {...(isDragOverlay ? {} : attributes)}
            className={`flex rounded-lg border border-border bg-card shadow-sm cursor-grab active:cursor-grabbing select-none overflow-hidden hover:shadow-md transition-shadow ${
                !isDragOverlay && isDragging ? "opacity-40" : ""
            }`}
        >
            {/* Left color strip — inline style required for dynamic task.color */}
            <div className="w-[3px] shrink-0" style={{ backgroundColor: task.color ?? "transparent" }} />

            <div className="flex-1 min-w-0 p-3 space-y-1.5">
                {/* WBS + priority badge */}
                <div className="flex items-center gap-2">
                    <span className="text-[11px] font-mono text-muted-foreground">{task.wbs_code}</span>
                    {badge && (
                        <span className={`text-[10px] font-semibold px-1.5 py-0.5 rounded-sm ${badge.cls}`}>
                            {badge.label}
                        </span>
                    )}
                </div>

                {/* Task name */}
                <p className="text-sm font-medium leading-snug line-clamp-2">{task.name}</p>

                {/* Deadline + overdue warning + comments */}
                {(task.deadline || overdue || (task.comments_count ?? 0) > 0) && (
                    <div className="flex items-center gap-2 text-xs text-muted-foreground pt-0.5">
                        {task.deadline && (
                            <span className={overdue ? "text-destructive font-medium" : ""}>
                                {formatDeadline(task.deadline)}
                            </span>
                        )}
                        {overdue && <AlertTriangle className="size-3 text-destructive shrink-0" />}
                        {(task.comments_count ?? 0) > 0 && (
                            <span className="flex items-center gap-1 ml-auto">
                                <MessageSquare className="size-3" />
                                {task.comments_count}
                            </span>
                        )}
                    </div>
                )}

                {/* Progress bar — inline style required for dynamic width */}
                {progress > 0 && (
                    <div className="flex items-center gap-2 pt-0.5">
                        <div className="flex-1 h-1.5 rounded-full bg-muted overflow-hidden">
                            <div className="h-full bg-primary rounded-full" style={{ width: `${progress}%` }} />
                        </div>
                        <span className="text-[10px] text-muted-foreground tabular-nums w-7 text-right">
                            {progress}%
                        </span>
                    </div>
                )}

                {/* Assignee avatars */}
                {(task.assignments ?? []).length > 0 && (
                    <div className="flex items-center gap-1 pt-0.5">
                        {(task.assignments ?? []).map((a) => (
                            <Tooltip key={a.resource_id}>
                                <TooltipTrigger asChild>
                                    <Avatar size="sm">
                                        <AvatarFallback>
                                            {a.resource_initials ?? a.resource_name.slice(0, 2).toUpperCase()}
                                        </AvatarFallback>
                                    </Avatar>
                                </TooltipTrigger>
                                <TooltipContent>{a.resource_name}</TooltipContent>
                            </Tooltip>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}
