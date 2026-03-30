import type { KeyboardEvent } from "react";
import { useEffect, useMemo, useRef, useState } from "react";
import { useDroppable } from "@dnd-kit/core";
import { SortableContext, verticalListSortingStrategy } from "@dnd-kit/sortable";
import { format } from "date-fns";
import { ChevronsRight, LayoutList, Loader2 } from "lucide-react";
import { toast } from "sonner";
import { useCreateTask } from "@/features/tasks";
import { getErrorMessage } from "@/shared/lib/errors";
import { Input } from "@/shared/ui/input";
import type { Task, TaskAssignmentSummary } from "@/features/tasks";
import type {
    KanbanColumn as KanbanColumnType,
    KanbanDependencyIndicatorsByTaskId,
    KanbanLaneMode,
} from "../types";
import { useKanbanStore } from "../store/kanban-store";
import { KanbanCard } from "./KanbanCard";
import { KanbanColumnHeader } from "./KanbanColumnHeader";

interface KanbanColumnProps {
    column: KanbanColumnType;
    tasks: Task[];
    dependencyIndicatorsByTaskId: KanbanDependencyIndicatorsByTaskId;
    projectId: string | undefined;
    wipLimit?: number;
    laneMode: KanbanLaneMode;
    selectionMode?: boolean;
    selectedTaskId?: string | null;
    selectedTaskIds?: Set<string>;
    onTaskClick?: (taskId: string) => void;
    onTaskDoubleClick?: (taskId: string) => void;
    onSetWipLimit?: (limit: number | null) => void;
    focusedTaskId?: string | null;
    onCardFocus?: (taskId: string) => void;
    getCardRef?: (taskId: string) => (node: HTMLDivElement | null) => void;
    quickAddNonce?: number;
}

interface KanbanLane {
    id: string;
    label: string;
    tasks: Task[];
}

const PRIORITY_LANE_ORDER = ["priority:high", "priority:medium", "priority:low", "priority:minimal"] as const;

const PRIORITY_LANE_LABEL: Record<(typeof PRIORITY_LANE_ORDER)[number], string> = {
    "priority:high": "High priority",
    "priority:medium": "Medium priority",
    "priority:low": "Low priority",
    "priority:minimal": "Minimal priority",
};

const ASSIGNEE_UNASSIGNED_LANE_ID = "assignee:unassigned";

function getPriorityLaneId(priority: number): (typeof PRIORITY_LANE_ORDER)[number] {
    if (priority >= 750) return "priority:high";
    if (priority >= 500) return "priority:medium";
    if (priority >= 250) return "priority:low";
    return "priority:minimal";
}

function getPrimaryAssignee(task: Task): TaskAssignmentSummary | null {
    const assignments = task.assignments ?? [];
    if (assignments.length === 0) return null;

    return assignments.reduce((best, current) => {
        const byName = current.resource_name.localeCompare(best.resource_name);
        if (byName !== 0) return byName < 0 ? current : best;
        return current.resource_id.localeCompare(best.resource_id) < 0 ? current : best;
    });
}

function buildAssigneeLanes(tasks: Task[]): KanbanLane[] {
    const byId: Record<string, KanbanLane> = {};

    for (const task of tasks) {
        const assignee = getPrimaryAssignee(task);
        const laneId = assignee ? `assignee:${assignee.resource_id}` : ASSIGNEE_UNASSIGNED_LANE_ID;
        const laneLabel = assignee ? assignee.resource_name : "Unassigned";

        if (!byId[laneId]) {
            byId[laneId] = { id: laneId, label: laneLabel, tasks: [] };
        }

        byId[laneId].tasks.push(task);
    }

    return Object.values(byId).sort((left, right) => {
        if (left.id === ASSIGNEE_UNASSIGNED_LANE_ID) return -1;
        if (right.id === ASSIGNEE_UNASSIGNED_LANE_ID) return 1;
        return left.label.localeCompare(right.label);
    });
}

function buildPriorityLanes(tasks: Task[]): KanbanLane[] {
    const byId: Record<(typeof PRIORITY_LANE_ORDER)[number], KanbanLane> = {
        "priority:high": { id: "priority:high", label: PRIORITY_LANE_LABEL["priority:high"], tasks: [] },
        "priority:medium": { id: "priority:medium", label: PRIORITY_LANE_LABEL["priority:medium"], tasks: [] },
        "priority:low": { id: "priority:low", label: PRIORITY_LANE_LABEL["priority:low"], tasks: [] },
        "priority:minimal": { id: "priority:minimal", label: PRIORITY_LANE_LABEL["priority:minimal"], tasks: [] },
    };

    for (const task of tasks) {
        byId[getPriorityLaneId(task.priority)].tasks.push(task);
    }

    return PRIORITY_LANE_ORDER.map((laneId) => byId[laneId]).filter((lane) => lane.tasks.length > 0);
}

function buildLanes(tasks: Task[], laneMode: KanbanLaneMode): KanbanLane[] {
    if (laneMode === "assignee") return buildAssigneeLanes(tasks);
    if (laneMode === "priority") return buildPriorityLanes(tasks);

    return [{ id: "none", label: "All tasks", tasks }];
}

export function KanbanColumn({
    column,
    tasks,
    dependencyIndicatorsByTaskId,
    projectId,
    wipLimit,
    laneMode,
    selectionMode = false,
    selectedTaskId,
    selectedTaskIds,
    onTaskClick,
    onTaskDoubleClick,
    onSetWipLimit,
    focusedTaskId,
    onCardFocus,
    getCardRef,
    quickAddNonce = 0,
}: KanbanColumnProps) {
    const { setNodeRef, isOver } = useDroppable({
        id: column.id,
        data: { type: "kanban-column", status: column.id },
    });
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
    const lastQuickAddNonceRef = useRef(0);

    const lanes = useMemo(() => buildLanes(tasks, laneMode), [tasks, laneMode]);

    useEffect(() => {
        return () => {
            isMounted.current = false;
        };
    }, []);

    useEffect(() => {
        if (quickAddNonce <= 0 || quickAddNonce === lastQuickAddNonceRef.current) return;
        lastQuickAddNonceRef.current = quickAddNonce;
        setIsAdding(true);
    }, [quickAddNonce]);

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
        } catch (error) {
            if (isMounted.current) {
                toast.error(getErrorMessage(error));
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
                ) : laneMode === "none" ? (
                    <SortableContext id={column.id} items={tasks.map((task) => task.id)} strategy={verticalListSortingStrategy}>
                        <div className="space-y-2">
                            {tasks.map((task) => {
                                const isSelected = selectionMode
                                    ? (selectedTaskIds?.has(task.id) ?? false)
                                    : selectedTaskId === task.id;
                                return (
                                <KanbanCard
                                    key={task.id}
                                    task={task}
                                    dependencyIndicator={dependencyIndicatorsByTaskId[task.id]}
                                    onClick={onTaskClick}
                                    onDoubleClick={onTaskDoubleClick}
                                    selectionMode={selectionMode}
                                    isSelected={isSelected}
                                    isKeyboardFocused={focusedTaskId === task.id}
                                    onFocus={onCardFocus}
                                    cardRef={getCardRef?.(task.id)}
                                />
                                );
                            })}
                        </div>
                    </SortableContext>
                ) : (
                    <SortableContext id={column.id} items={tasks.map((task) => task.id)} strategy={verticalListSortingStrategy}>
                        <div className="space-y-3">
                            {lanes.map((lane) => (
                                <section key={lane.id} className="space-y-2">
                                    <header className="flex items-center justify-between rounded-md border border-border/60 bg-background/60 px-2 py-1">
                                        <span className="text-[11px] font-semibold tracking-wide text-muted-foreground uppercase">
                                            {lane.label}
                                        </span>
                                        <span className="text-[11px] text-muted-foreground">{lane.tasks.length}</span>
                                    </header>
                                    <div className="space-y-2">
                                        {lane.tasks.map((task) => {
                                            const isSelected = selectionMode
                                                ? (selectedTaskIds?.has(task.id) ?? false)
                                                : selectedTaskId === task.id;
                                            return (
                                            <KanbanCard
                                                key={task.id}
                                                task={task}
                                                dependencyIndicator={dependencyIndicatorsByTaskId[task.id]}
                                                onClick={onTaskClick}
                                                onDoubleClick={onTaskDoubleClick}
                                                selectionMode={selectionMode}
                                                isSelected={isSelected}
                                                isKeyboardFocused={focusedTaskId === task.id}
                                                onFocus={onCardFocus}
                                                cardRef={getCardRef?.(task.id)}
                                            />
                                            );
                                        })}
                                    </div>
                                </section>
                            ))}
                        </div>
                    </SortableContext>
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
