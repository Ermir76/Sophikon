import { useDroppable } from "@dnd-kit/core";
import { LayoutList } from "lucide-react";
import type { Task } from "@/features/tasks";
import type { KanbanColumn as KanbanColumnType } from "../types";
import { KanbanCard } from "./KanbanCard";
import { KanbanColumnHeader } from "./KanbanColumnHeader";

interface KanbanColumnProps {
    column: KanbanColumnType;
    tasks: Task[];
}

export function KanbanColumn({ column, tasks }: KanbanColumnProps) {
    const { setNodeRef, isOver } = useDroppable({ id: column.id });

    return (
        <div
            ref={setNodeRef}
            className={`group flex flex-col h-full w-[300px] min-w-[300px] shrink-0 rounded-lg border border-border transition-colors ${
                isOver ? "bg-muted/50 ring-2 ring-primary/40" : "bg-muted/30"
            }`}
        >
            <KanbanColumnHeader column={column} count={tasks.length} />

            <div className="flex flex-col flex-1 overflow-y-auto min-h-0 p-2">
                {tasks.length === 0 ? (
                    <div className="flex flex-col flex-1 items-center justify-center text-muted-foreground py-8">
                        <LayoutList className="size-6 mb-2 opacity-40" />
                        <p className="text-xs">No tasks</p>
                    </div>
                ) : (
                    <div className="space-y-2">
                        {tasks.map((task) => (
                            <KanbanCard key={task.id} task={task} />
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}
