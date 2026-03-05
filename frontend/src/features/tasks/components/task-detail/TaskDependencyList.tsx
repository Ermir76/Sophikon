import { Loader2, Trash2, Pencil } from "lucide-react";
import { Button } from "@/shared/ui/button";
import { Badge } from "@/shared/ui/badge";
import { useDependencies, useDeleteDependency } from "@/features/tasks/hooks/useDependencies";
import { useTasks } from "@/features/tasks/hooks/useTasks";
import { AddDependencyDialog } from "@/features/tasks/components/task-detail/AddDependencyDialog";
import { EditDependencyDialog } from "@/features/tasks/components/task-detail/EditDependencyDialog";
import { useState } from "react";
import type { Dependency } from "@/features/tasks/types";

interface TaskDependencyListProps {
    projectId: string;
    taskId: string;
}

export function TaskDependencyList({ projectId, taskId }: TaskDependencyListProps) {
    const { data: tasksData } = useTasks(projectId);
    const { data: dependenciesData, isLoading: isLoadingDeps } = useDependencies(projectId);
    const deleteDependency = useDeleteDependency(projectId);
    const [isDependencyDialogOpen, setIsDependencyDialogOpen] = useState(false);
    const [editingDependency, setEditingDependency] = useState<Dependency | null>(null);

    // Filter to only show dependencies where this task is the successor
    const taskDependencies = dependenciesData?.items?.filter(d => d.successor_id === taskId) || [];

    return (
        <div className="flex flex-col h-full bg-card">
            {/* Header Area */}
            <div className="flex items-center justify-between border-b px-5 py-4">
                <div className="flex items-center gap-2">
                    <h4 className="font-semibold text-sm tracking-tight">Dependencies</h4>
                    {taskDependencies.length > 0 && (
                        <Badge variant="outline" className="h-5 px-2 text-[10px] font-semibold">
                            {taskDependencies.length}
                        </Badge>
                    )}
                </div>
                <Button
                    variant="secondary"
                    size="sm"
                    className="h-8 text-xs font-medium"
                    onClick={() => setIsDependencyDialogOpen(true)}
                >
                    Add Dependency
                </Button>
            </div>

            {/* List Body */}
            <div className="p-0">
                {isLoadingDeps ? (
                    <div className="flex justify-center py-8"><Loader2 className="size-5 animate-spin text-muted-foreground" /></div>
                ) : taskDependencies.length === 0 ? (
                    <div className="flex flex-col items-center justify-center gap-2 py-8 text-center text-sm text-muted-foreground">
                        <span className="text-xs">No dependencies set</span>
                    </div>
                ) : (
                    <div className="divide-y divide-border">
                        {taskDependencies.map((dep) => {
                            const predecessorTask = tasksData?.items?.find(t => t.id === dep.predecessor_id);
                            return (
                                <div key={dep.id} className={`group flex flex-col justify-between gap-3 p-3 px-4 hover:bg-muted/30 sm:flex-row sm:items-center ${dep.is_disabled ? "opacity-50" : ""}`}>
                                    <div className="flex items-center gap-3 min-w-0">
                                        <Badge variant="outline" className="shrink-0 px-1.5 py-0.5 font-mono text-xs font-medium text-muted-foreground">
                                            {predecessorTask ? predecessorTask.wbs_code : dep.predecessor_id.slice(0, 6)}
                                        </Badge>
                                        <span className="truncate text-sm font-medium">
                                            {predecessorTask ? predecessorTask.name : "Unknown Task"}
                                        </span>
                                        <Badge variant="outline" className="shrink-0 text-[10px] font-bold uppercase tracking-wide">
                                            {dep.type}
                                        </Badge>
                                        {dep.lag !== 0 && (
                                            <span className="shrink-0 text-[10px] font-medium text-muted-foreground">
                                                {dep.lag > 0 ? `+${dep.lag}m` : `${dep.lag}m`}
                                            </span>
                                        )}
                                        {dep.is_disabled && (
                                            <Badge variant="outline" className="shrink-0 px-1.5 py-0.5 text-[10px] font-medium text-muted-foreground">
                                                disabled
                                            </Badge>
                                        )}
                                    </div>
                                    <div className="flex shrink-0 items-center gap-1">
                                        <Button
                                            variant="ghost"
                                            size="icon"
                                            className="size-7 shrink-0 rounded-full opacity-100 transition-all sm:opacity-0 group-hover:opacity-100"
                                            onClick={() => setEditingDependency(dep)}
                                        >
                                            <Pencil className="size-3.5" />
                                        </Button>
                                        <Button
                                            variant="ghost"
                                            size="icon"
                                            className="size-7 shrink-0 rounded-full opacity-100 transition-all sm:opacity-0 group-hover:opacity-100"
                                            disabled={deleteDependency.isPending}
                                            onClick={() => deleteDependency.mutate(dep.id)}
                                        >
                                            <Trash2 className="size-3.5" />
                                        </Button>
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                )}
            </div>

            <AddDependencyDialog
                projectId={projectId}
                successorTaskId={taskId}
                isOpen={isDependencyDialogOpen}
                onClose={() => setIsDependencyDialogOpen(false)}
            />

            {editingDependency && (
                <EditDependencyDialog
                    projectId={projectId}
                    dependency={editingDependency}
                    isOpen={!!editingDependency}
                    onClose={() => setEditingDependency(null)}
                />
            )}
        </div>
    );
}
