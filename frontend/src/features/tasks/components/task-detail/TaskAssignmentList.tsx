import { Loader2, Trash2 } from "lucide-react";
import { Button } from "@/shared/ui/button";
import { useAssignments, useDeleteAssignment } from "@/features/tasks/hooks/useAssignments";
import { useResources } from "@/features/resources";
import { AddAssignmentDialog } from "@/features/tasks/components/task-detail/AddAssignmentDialog";
import { useState } from "react";

interface TaskAssignmentListProps {
    projectId: string;
    taskId: string;
}

export function TaskAssignmentList({ projectId, taskId }: TaskAssignmentListProps) {
    const { data: assignments, isLoading: isLoadingAssignments } = useAssignments(projectId, taskId);
    const { data: resourcesData } = useResources(projectId);
    const deleteAssignment = useDeleteAssignment(projectId, taskId);
    const [isAddDialogOpen, setIsAddDialogOpen] = useState(false);

    const resources = resourcesData?.items ?? [];

    return (
        <div className="flex flex-col h-full bg-card">
            {/* Header Area */}
            <div className="flex justify-between items-center px-5 py-4 border-b border-border/50 bg-muted/10">
                <div className="flex items-center gap-2">
                    <h4 className="font-semibold text-sm tracking-tight">Assignments</h4>
                    {assignments && assignments.length > 0 && (
                        <span className="flex h-5 items-center justify-center rounded-full bg-primary/10 px-2 text-[10px] font-semibold text-primary">
                            {assignments.length}
                        </span>
                    )}
                </div>
                <Button
                    variant="secondary"
                    size="sm"
                    className="h-8 text-xs font-medium"
                    onClick={() => setIsAddDialogOpen(true)}
                >
                    Add Assignment
                </Button>
            </div>

            {/* List Body */}
            <div className="p-0">
                {isLoadingAssignments ? (
                    <div className="flex justify-center py-8"><Loader2 className="size-5 animate-spin text-muted-foreground/50" /></div>
                ) : !assignments || assignments.length === 0 ? (
                    <div className="text-sm text-muted-foreground/60 text-center py-8 flex flex-col items-center justify-center gap-2">
                        <span className="text-xs">No resources assigned</span>
                    </div>
                ) : (
                    <div className="divide-y divide-border/50">
                        {assignments.map((assignment) => {
                            const resource = resources.find((r) => r.id === assignment.resource_id);
                            return (
                                <div key={assignment.id} className="group flex flex-col sm:flex-row sm:items-center justify-between p-3 px-4 gap-3 bg-transparent hover:bg-muted/30 transition-colors">
                                    <div className="flex items-center gap-3 min-w-0">
                                        {resource?.initials && (
                                            <span className="inline-flex items-center justify-center size-7 rounded-full bg-primary/10 text-[10px] font-bold text-primary shrink-0">
                                                {resource.initials}
                                            </span>
                                        )}
                                        <span className="truncate text-sm font-medium text-foreground/90">
                                            {resource ? resource.name : assignment.resource_id.slice(0, 8)}
                                        </span>
                                        <span className="inline-flex items-center rounded-full bg-blue-500/10 px-2 py-0.5 text-[10px] font-bold tracking-wide text-blue-500 uppercase border border-blue-500/20 shrink-0">
                                            {Math.round(Number(assignment.units) * 100)}%
                                        </span>
                                        {Number(assignment.work) > 0 && (
                                            <span className="text-[10px] font-medium text-muted-foreground shrink-0">
                                                {assignment.work}m work
                                            </span>
                                        )}
                                    </div>
                                    <div className="flex items-center gap-1 shrink-0">
                                        <Button
                                            variant="ghost"
                                            size="icon"
                                            className="size-7 text-muted-foreground/50 hover:text-destructive hover:bg-destructive/10 shrink-0 opacity-100 sm:opacity-0 group-hover:opacity-100 transition-all rounded-full"
                                            disabled={deleteAssignment.isPending}
                                            onClick={() => deleteAssignment.mutate(assignment.id)}
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

            <AddAssignmentDialog
                projectId={projectId}
                taskId={taskId}
                isOpen={isAddDialogOpen}
                onClose={() => setIsAddDialogOpen(false)}
            />
        </div>
    );
}
