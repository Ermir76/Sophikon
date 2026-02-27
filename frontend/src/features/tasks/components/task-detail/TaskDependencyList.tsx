import { Loader2, Trash2, Pencil } from "lucide-react";
import { Button } from "@/shared/ui/button";
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
            <div className="flex justify-between items-center px-5 py-4 border-b border-border/50 bg-muted/10">
                <div className="flex items-center gap-2">
                    <h4 className="font-semibold text-sm tracking-tight">Dependencies</h4>
                    {taskDependencies.length > 0 && (
                        <span className="flex h-5 items-center justify-center rounded-full bg-primary/10 px-2 text-[10px] font-semibold text-primary">
                            {taskDependencies.length}
                        </span>
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
                    <div className="flex justify-center py-8"><Loader2 className="size-5 animate-spin text-muted-foreground/50" /></div>
                ) : taskDependencies.length === 0 ? (
                    <div className="text-sm text-muted-foreground/60 text-center py-8 flex flex-col items-center justify-center gap-2">
                        <span className="text-xs">No dependencies set</span>
                    </div>
                ) : (
                    <div className="divide-y divide-border/50">
                        {taskDependencies.map((dep) => {
                            const predecessorTask = tasksData?.items?.find(t => t.id === dep.predecessor_id);
                            return (
                                <div key={dep.id} className={`group flex flex-col sm:flex-row sm:items-center justify-between p-3 px-4 gap-3 bg-transparent hover:bg-muted/30 transition-colors ${dep.is_disabled ? "opacity-50" : ""}`}>
                                    <div className="flex items-center gap-3 min-w-0">
                                        <span className="inline-flex items-center rounded bg-muted/60 px-1.5 py-0.5 text-xs font-mono font-medium text-muted-foreground shrink-0 border border-border/40">
                                            {predecessorTask ? predecessorTask.wbs_code : dep.predecessor_id.slice(0, 6)}
                                        </span>
                                        <span className="truncate text-sm font-medium text-foreground/90">
                                            {predecessorTask ? predecessorTask.name : "Unknown Task"}
                                        </span>
                                        <span className="inline-flex items-center rounded-full bg-blue-500/10 px-2 py-0.5 text-[10px] font-bold tracking-wide text-blue-500 uppercase border border-blue-500/20 shrink-0">
                                            {dep.type}
                                        </span>
                                        {dep.lag !== 0 && (
                                            <span className="text-[10px] font-medium text-muted-foreground shrink-0">
                                                {dep.lag > 0 ? `+${dep.lag}m` : `${dep.lag}m`}
                                            </span>
                                        )}
                                        {dep.is_disabled && (
                                            <span className="inline-flex items-center rounded-full bg-muted px-1.5 py-0.5 text-[10px] font-medium text-muted-foreground shrink-0">
                                                disabled
                                            </span>
                                        )}
                                    </div>
                                    <div className="flex items-center gap-1 shrink-0">
                                        <Button
                                            variant="ghost"
                                            size="icon"
                                            className="size-7 text-muted-foreground/50 hover:text-foreground hover:bg-muted shrink-0 opacity-100 sm:opacity-0 group-hover:opacity-100 transition-all rounded-full"
                                            onClick={() => setEditingDependency(dep)}
                                        >
                                            <Pencil className="size-3.5" />
                                        </Button>
                                        <Button
                                            variant="ghost"
                                            size="icon"
                                            className="size-7 text-muted-foreground/50 hover:text-destructive hover:bg-destructive/10 shrink-0 opacity-100 sm:opacity-0 group-hover:opacity-100 transition-all rounded-full"
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
