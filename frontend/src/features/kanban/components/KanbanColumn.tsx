import type { KeyboardEvent } from "react";
import { useEffect, useRef, useState } from "react";
import { useDroppable } from "@dnd-kit/core";
import { format } from "date-fns";
import { ChevronsRight, LayoutList, Loader2 } from "lucide-react";
import { toast } from "sonner";
import { useCreateTask } from "@/features/tasks";
import { Input } from "@/shared/ui/input";
import type { Task } from "@/features/tasks";
import type { KanbanColumn as KanbanColumnType } from "../types";
import { useKanbanStore } from "../store/kanban-store";
import { KanbanCard } from "./KanbanCard";
import { KanbanColumnHeader } from "./KanbanColumnHeader";

interface KanbanColumnProps {
    column: KanbanColumnType;
    tasks: Task[];
    projectId: string | undefined;
    wipLimit?: number;
    onTaskClick?: (taskId: string) => void;
    onSetWipLimit?: (limit: number | null) => void;
}

export function KanbanColumn({
    column,
    tasks,
    projectId,
    wipLimit,
    onTaskClick,
    onSetWipLimit,
}: KanbanColumnProps) {
    const { setNodeRef, isOver } = useDroppable({ id: column.id });
    const collapsedByProject = useKanbanStore((s) => s.collapsedByProject);
    const toggleCollapse = useKanbanStore((s) => s.toggleCollapse);
    const isCollapsed = projectId
        ? (collapsedByProject[projectId] ?? []).includes(column.id)
        : false;

    const [isAdding, setIsAdding] = useState(false);
    const [taskName, setTaskName] = useState("");
    const createTask = useCreateTask(projectId);
    const isSubmitting = useRef(false);
    const isMounted = useRef(true);

    useEffect(() => {
        return () => {
            isMounted.current = false;
        };
    }, []);

    const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
        if (e.key === "Enter") handleSubmit();
        else if (e.key === "Escape") handleCancel();
    };

    const handleCancel = () => {
        setIsAdding(false);
        setTaskName("");
    };

    const handleSubmit = async () => {
        if (isSubmitting.current) return;
        if (!taskName.trim()) {
            handleCancel();
            return;
        }
        isSubmitting.current = true;
        try {
            await createTask.mutateAsync({
                name: taskName.trim(),
                start_date: format(new Date(), "yyyy-MM-dd"),
                duration: 480,
                status: column.id,
            });
            if (isMounted.current) {
                setTaskName("");
                setIsAdding(false);
            }
        } catch {
            if (isMounted.current) {
                toast.error("Failed to create task");
            }
        } finally {
            isSubmitting.current = false;
        }
    };

    const handleToggleCollapse = () => {
        if (projectId) toggleCollapse(projectId, column.id);
    };
    const isOverLimit = typeof wipLimit === "number" && tasks.length > wipLimit;

    if (isCollapsed) {
        return (
            <div
                ref={setNodeRef}
                className="flex flex-col h-full w-12 min-w-[3rem] shrink-0 rounded-lg border border-border bg-muted/30 transition-colors"
            >
                <button
                    type="button"
                    className="flex flex-col flex-1 items-center gap-3 pt-3 pb-3 w-full cursor-pointer hover:bg-muted/50 rounded-lg transition-colors"
                    onClick={handleToggleCollapse}
                    aria-label={`Expand ${column.label}`}
                    aria-expanded={false}
                >
                    <ChevronsRight className="size-4 text-muted-foreground shrink-0" />
                    <span
                        className="flex-1 text-sm font-semibold text-muted-foreground tracking-wide"
                        style={{ writingMode: "vertical-rl", transform: "rotate(180deg)" }}
                    >
                        {column.label}
                    </span>
                    <span className="text-xs text-muted-foreground bg-muted px-1.5 py-0.5 rounded-full">
                        {tasks.length}
                    </span>
                </button>
            </div>
        );
    }

    return (
        <div
            ref={setNodeRef}
            className={`group flex flex-col h-full w-[300px] min-w-[300px] shrink-0 rounded-lg border border-border transition-colors ${
                isOver ? "bg-muted/50 ring-2 ring-primary/40" : "bg-muted/30"
            }`}
        >
            <KanbanColumnHeader
                column={column}
                count={tasks.length}
                limit={wipLimit}
                isOverLimit={isOverLimit}
                onToggleCollapse={handleToggleCollapse}
                onAdd={() => setIsAdding(true)}
                onSetWipLimit={onSetWipLimit}
            />

            <div className="flex flex-col flex-1 overflow-y-auto min-h-0 p-2">
                {tasks.length === 0 && !isAdding ? (
                    <div className="flex flex-col flex-1 items-center justify-center text-muted-foreground py-8">
                        <LayoutList className="size-6 mb-2 opacity-40" />
                        <p className="text-xs">No tasks</p>
                    </div>
                ) : (
                    <div className="space-y-2">
                        {tasks.map((task) => (
                            <KanbanCard key={task.id} task={task} onClick={onTaskClick} />
                        ))}
                    </div>
                )}
            </div>

            {isAdding && (
                <div className="shrink-0 p-2 border-t border-border">
                    <div className="flex items-center gap-2">
                        <Input
                            autoFocus
                            placeholder="Task name..."
                            value={taskName}
                            onChange={(e) => setTaskName(e.target.value)}
                            onKeyDown={handleKeyDown}
                            onBlur={handleSubmit}
                            className="h-8 flex-1"
                            disabled={createTask.isPending}
                        />
                        {createTask.isPending && (
                            <Loader2 className="size-4 animate-spin text-muted-foreground shrink-0" />
                        )}
                    </div>
                </div>
            )}
        </div>
    );
}
