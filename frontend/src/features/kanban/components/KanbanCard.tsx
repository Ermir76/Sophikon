import type { MouseEvent, PointerEvent } from "react";
import { useSortable } from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import { AlertTriangle, Link2, MessageSquare } from "lucide-react";
import { Avatar, AvatarFallback } from "@/shared/ui/avatar";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/shared/ui/tooltip";
import type { Task } from "@/features/tasks";
import type { KanbanDependencyIndicator } from "../types";

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
    dependencyIndicator?: KanbanDependencyIndicator;
    isDragOverlay?: boolean;
    onClick?: (taskId: string) => void;
    isKeyboardFocused?: boolean;
    onFocus?: (taskId: string) => void;
    cardRef?: (node: HTMLDivElement | null) => void;
}

export function KanbanCard({
    task,
    dependencyIndicator,
    isDragOverlay = false,
    onClick,
    isKeyboardFocused = false,
    onFocus,
    cardRef,
}: KanbanCardProps) {
    const { setNodeRef, listeners, attributes, transform, transition, isDragging } = useSortable({
        id: task.id,
        data: {
            type: "kanban-card",
            status: task.status,
            parentTaskId: task.parent_task_id ?? null,
        },
        disabled: isDragOverlay,
    });
    const style = isDragOverlay
        ? undefined
        : {
            transform: CSS.Transform.toString(transform),
            transition,
        };

    const badge = getPriorityBadge(task.priority);
    const overdue = isOverdue(task);
    const progress = Math.round(Number(task.percent_complete));
    const blockedCount = dependencyIndicator?.blockedCount ?? 0;
    const blockingCount = dependencyIndicator?.blockingCount ?? 0;

    const handleDependencyClick = (event: MouseEvent<HTMLButtonElement>) => {
        event.preventDefault();
        event.stopPropagation();
        onClick?.(task.id);
    };

    const handleDependencyPointerDown = (event: PointerEvent<HTMLButtonElement>) => {
        event.stopPropagation();
    };

    const handleFocus = () => {
        if (isDragOverlay) return;
        onFocus?.(task.id);
    };

    return (
        <div
            ref={isDragOverlay ? undefined : (node) => {
                setNodeRef(node);
                cardRef?.(node);
            }}
            style={style}
            {...(isDragOverlay ? {} : listeners)}
            {...(isDragOverlay ? {} : attributes)}
            onClick={isDragOverlay ? undefined : () => onClick?.(task.id)}
            onFocus={handleFocus}
            tabIndex={isDragOverlay ? undefined : (isKeyboardFocused ? 0 : -1)}
            data-task-id={task.id}
            className={`flex rounded-lg border border-border bg-card shadow-sm cursor-grab active:cursor-grabbing select-none overflow-hidden hover:shadow-md transition-shadow ${
                !isDragOverlay && isDragging ? "opacity-40" : ""
            } ${isKeyboardFocused ? "ring-2 ring-primary/40" : ""}`}
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

                {(blockedCount > 0 || blockingCount > 0) && (
                    <div className="flex items-center gap-1.5 pt-0.5">
                        {blockedCount > 0 && (
                            <button
                                type="button"
                                aria-label={`Blocked dependencies: ${blockedCount}`}
                                onPointerDown={handleDependencyPointerDown}
                                onClick={handleDependencyClick}
                                className="inline-flex items-center gap-1 rounded-sm bg-destructive/10 px-1.5 py-0.5 text-[10px] font-semibold text-destructive hover:bg-destructive/20"
                            >
                                <Link2 className="size-3" />
                                Blocked {blockedCount}
                            </button>
                        )}
                        {blockingCount > 0 && (
                            <button
                                type="button"
                                aria-label={`Blocking dependencies: ${blockingCount}`}
                                onPointerDown={handleDependencyPointerDown}
                                onClick={handleDependencyClick}
                                className="inline-flex items-center gap-1 rounded-sm bg-amber-500/15 px-1.5 py-0.5 text-[10px] font-semibold text-amber-700 dark:text-amber-400 hover:bg-amber-500/25"
                            >
                                <Link2 className="size-3" />
                                Blocking {blockingCount}
                            </button>
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
