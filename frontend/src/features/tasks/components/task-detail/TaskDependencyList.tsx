import { Loader2, Trash2 } from "lucide-react";
import { Button } from "@/shared/ui/button";
import { useDependencies, useDeleteDependency } from "@/features/tasks/hooks/useDependencies";
import { useTasks } from "@/features/tasks/hooks/useTasks";
import { AddDependencyDialog } from "@/features/tasks/components/task-detail/AddDependencyDialog";
import { useState } from "react";

interface TaskDependencyListProps {
    projectId: string;
    taskId: string;
}

export function TaskDependencyList({ projectId, taskId }: TaskDependencyListProps) {
    const { data: tasksData } = useTasks(projectId);
    const { data: dependenciesData, isLoading: isLoadingDeps } = useDependencies(projectId);
    const deleteDependency = useDeleteDependency(projectId);
    const [isDependencyDialogOpen, setIsDependencyDialogOpen] = useState(false);

    // Filter to only show dependencies where this task is the successor
    const taskDependencies = dependenciesData?.items?.filter(d => d.successor_id === taskId) || [];

    return (
        <div className="space-y-4 pt-4 border-t mt-6">
            <div className="flex justify-between items-center">
                <h4 className="font-semibold text-sm">Dependencies</h4>
                <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setIsDependencyDialogOpen(true)}
                >
                    Add Dependency
                </Button>
            </div>

            {isLoadingDeps ? (
                <div className="flex justify-center py-4"><Loader2 className="size-4 animate-spin text-muted-foreground" /></div>
            ) : taskDependencies.length === 0 ? (
                <div className="text-sm text-muted-foreground text-center py-6 border border-dashed rounded-md">
                    No dependencies set for this task.
                </div>
            ) : (
                <div className="space-y-2">
                    {taskDependencies.map((dep) => {
                        const predecessorTask = tasksData?.items?.find(t => t.id === dep.predecessor_id);
                        return (
                            <div key={dep.id} className="flex items-center justify-between p-2 rounded-md border text-sm">
                                <div className="flex items-center gap-2">
                                    <span className="font-mono text-muted-foreground">
                                        {predecessorTask ? predecessorTask.wbs_code : dep.predecessor_id.slice(0, 6)}
                                    </span>
                                    <span className="truncate max-w-[150px]">
                                        {predecessorTask ? predecessorTask.name : "Unknown Task"}
                                    </span>
                                    <span className="font-semibold px-2 py-0.5 bg-muted rounded">
                                        {dep.type}
                                    </span>
                                </div>
                                <Button
                                    variant="ghost"
                                    size="icon"
                                    className="size-6 text-destructive hover:bg-destructive/10"
                                    disabled={deleteDependency.isPending}
                                    onClick={() => deleteDependency.mutate(dep.id)}
                                >
                                    <Trash2 className="size-4" />
                                </Button>
                            </div>
                        );
                    })}
                </div>
            )}

            <AddDependencyDialog
                projectId={projectId}
                successorTaskId={taskId}
                isOpen={isDependencyDialogOpen}
                onClose={() => setIsDependencyDialogOpen(false)}
            />
        </div>
    );
}
