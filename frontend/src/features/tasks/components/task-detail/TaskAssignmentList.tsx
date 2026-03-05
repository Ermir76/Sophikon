import { Loader2, Trash2 } from "lucide-react";
import { Button } from "@/shared/ui/button";
import { Badge } from "@/shared/ui/badge";
import { useAssignments, useDeleteAssignment } from "@/features/tasks/hooks/useAssignments";
import { useResources, useOverAllocations, OverAllocationBadge } from "@/features/resources";
import { AddAssignmentDialog } from "@/features/tasks/components/task-detail/AddAssignmentDialog";
import { useState } from "react";
import { format, addDays } from "date-fns";

interface TaskAssignmentListProps {
    projectId: string;
    taskId: string;
}

export function TaskAssignmentList({ projectId, taskId }: TaskAssignmentListProps) {
    const { data: assignments, isLoading: isLoadingAssignments } = useAssignments(projectId, taskId);
    const { data: resourcesData } = useResources(projectId);
    const deleteAssignment = useDeleteAssignment(projectId, taskId);
    const [isAddDialogOpen, setIsAddDialogOpen] = useState(false);

    // Get over-allocations for the next 30 days to show warnings
    const today = new Date();
    const startDate = format(today, "yyyy-MM-dd");
    const endDate = format(addDays(today, 30), "yyyy-MM-dd");
    const { data: overAllocations } = useOverAllocations(projectId, startDate, endDate);

    const overAllocatedIds = new Set(
        overAllocations?.items.map(item => item.resource_id) ?? []
    );

    const resources = resourcesData?.items ?? [];

    return (
        <div className="flex flex-col h-full bg-card">
            {/* Header Area */}
            <div className="flex items-center justify-between border-b px-5 py-4">
                <div className="flex items-center gap-2">
                    <h4 className="font-semibold text-sm tracking-tight">Assignments</h4>
                    {assignments && assignments.length > 0 && (
                        <Badge variant="outline" className="h-5 px-2 text-[10px] font-semibold">
                            {assignments.length}
                        </Badge>
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
                    <div className="flex justify-center py-8"><Loader2 className="size-5 animate-spin text-muted-foreground" /></div>
                ) : !assignments || assignments.length === 0 ? (
                    <div className="flex flex-col items-center justify-center gap-2 py-8 text-center text-sm text-muted-foreground">
                        <span className="text-xs">No resources assigned</span>
                    </div>
                ) : (
                    <div className="divide-y divide-border">
                        {assignments.map((assignment) => {
                            const resource = resources.find((r) => r.id === assignment.resource_id);
                            return (
                                <div key={assignment.id} className="group flex flex-col justify-between gap-3 p-3 px-4 hover:bg-muted/30 sm:flex-row sm:items-center">
                                    <div className="flex items-center gap-3 min-w-0">
                                        {resource?.initials && (
                                            <span className="inline-flex size-7 shrink-0 items-center justify-center rounded-full border text-[10px] font-bold">
                                                {resource.initials}
                                            </span>
                                        )}
                                        <span className="truncate text-sm font-medium">
                                            {resource ? resource.name : assignment.resource_id.slice(0, 8)}
                                        </span>
                                        {overAllocatedIds.has(assignment.resource_id) && (
                                            <OverAllocationBadge />
                                        )}
                                        <Badge variant="outline" className="shrink-0 text-[10px] font-bold tracking-wide">
                                            {Math.round(Number(assignment.units) * 100)}%
                                        </Badge>
                                        {Number(assignment.work) > 0 && (
                                            <span className="shrink-0 text-[10px] font-medium text-muted-foreground">
                                                {assignment.work}m work
                                            </span>
                                        )}
                                    </div>
                                    <div className="flex shrink-0 items-center gap-1">
                                        <Button
                                            variant="ghost"
                                            size="icon"
                                            className="size-7 shrink-0 rounded-full opacity-100 transition-all sm:opacity-0 group-hover:opacity-100"
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
