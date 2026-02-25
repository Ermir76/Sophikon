import { useState, useEffect } from "react";
import { format, parseISO } from "date-fns";
import { Loader2, Trash2 } from "lucide-react";
import {
    Sheet,
    SheetContent,
    SheetHeader,
    SheetTitle,
    SheetDescription,
} from "@/shared/ui/sheet";
import { Button } from "@/shared/ui/button";
import { Input } from "@/shared/ui/input";
import { Textarea } from "@/shared/ui/textarea";
import { useTask, useTasks, useUpdateTask } from "@/features/tasks/hooks/useTasks";
import { useDependencies, useDeleteDependency } from "@/features/tasks/hooks/useDependencies";
import { AddDependencyDialog } from "@/features/tasks/components/AddDependencyDialog";
import { toast } from "sonner";
import type { TaskUpdate } from "@/features/tasks/types";

interface TaskDetailPanelProps {
    projectId: string;
    taskId: string | null;
    isOpen: boolean;
    onClose: () => void;
}

export function TaskDetailPanel({ projectId, taskId, isOpen, onClose }: TaskDetailPanelProps) {
    const { data: tasksData } = useTasks(projectId);
    const { data: task, isLoading } = useTask(projectId, taskId ?? undefined);
    const updateTask = useUpdateTask(projectId);

    // Dependencies
    const { data: dependenciesData, isLoading: isLoadingDeps } = useDependencies(projectId);
    const deleteDependency = useDeleteDependency(projectId);
    const [isDependencyDialogOpen, setIsDependencyDialogOpen] = useState(false);

    // Filter to only show dependencies where this task is the successor
    const taskDependencies = dependenciesData?.items?.filter(d => d.successor_id === taskId) || [];

    // Local form state to track keystrokes without spamming the API
    const [localData, setLocalData] = useState<Partial<TaskUpdate>>({});

    // Sync from server when task loads or is externally updated
    useEffect(() => {
        if (task) {
            setLocalData({
                name: task.name,
                percent_complete: task.percent_complete,
                start_date: task.start_date ? task.start_date.split("T")[0] : "",
                duration: task.duration,
                notes: task.notes || "",
            });
        }
    }, [task]);

    // Only fire the update mutation when the user clicks away, if the value actually changed
    const handleBlur = (field: keyof TaskUpdate) => {
        if (!task) return;

        const currentValue = localData[field];
        let originalValue: any = task[field as keyof typeof task];

        if (field === "start_date" && originalValue) {
            originalValue = String(originalValue).split("T")[0];
        } else if (field === "notes" && !originalValue) {
            originalValue = "";
        }

        if (currentValue !== originalValue) {
            updateTask.mutate(
                { taskId: task.id, data: { [field]: currentValue } },
                {
                    onError: () => {
                        toast.error(`Failed to update ${field}`);
                        // Rebound the local state on failure
                        setLocalData((prev) => ({ ...prev, [field]: originalValue }));
                    },
                }
            );
        }
    };

    return (
        <Sheet open={isOpen} onOpenChange={(open) => !open && onClose()}>
            <SheetContent className="w-full sm:max-w-md md:max-w-lg overflow-y-auto">
                {isLoading || !task ? (
                    <div className="flex justify-center items-center h-full">
                        <Loader2 className="size-8 animate-spin text-muted-foreground" />
                    </div>
                ) : (
                    <>
                        <SheetHeader className="mb-6">
                            <SheetTitle>
                                <div className="flex items-center gap-2">
                                    <span className="text-muted-foreground font-mono text-sm">{task.wbs_code}</span>
                                    <Input
                                        value={localData.name ?? ""}
                                        onChange={(e) => setLocalData({ ...localData, name: e.target.value })}
                                        onBlur={() => handleBlur("name")}
                                        className="text-lg font-semibold border-transparent hover:border-border focus:border-primary shadow-none -ml-3"
                                    />
                                </div>
                            </SheetTitle>
                            <SheetDescription>
                                Created on {format(parseISO(task.created_at), "PPP")}
                            </SheetDescription>
                        </SheetHeader>

                        <div className="space-y-6">
                            {/* Core Details Grid */}
                            <div className="grid grid-cols-2 gap-4">
                                <div className="space-y-2">
                                    <label htmlFor="percent_complete" className="text-sm font-medium">% Complete</label>
                                    <div className="flex items-center gap-2">
                                        <Input
                                            id="percent_complete"
                                            type="number"
                                            min={0}
                                            max={100}
                                            value={localData.percent_complete ?? 0}
                                            onChange={(e) => setLocalData({ ...localData, percent_complete: Number(e.target.value) })}
                                            onBlur={() => handleBlur("percent_complete")}
                                        />
                                        <span className="text-sm text-muted-foreground">%</span>
                                    </div>
                                </div>

                                <div className="space-y-2">
                                    <label htmlFor="start_date" className="text-sm font-medium">Start Date</label>
                                    <Input
                                        id="start_date"
                                        type="date"
                                        value={localData.start_date ?? ""}
                                        onChange={(e) => setLocalData({ ...localData, start_date: e.target.value })}
                                        onBlur={() => handleBlur("start_date")}
                                    />
                                </div>

                                <div className="space-y-2">
                                    <label htmlFor="duration" className="text-sm font-medium">Duration (mins)</label>
                                    <Input
                                        id="duration"
                                        type="number"
                                        value={localData.duration ?? 0}
                                        onChange={(e) => setLocalData({ ...localData, duration: Number(e.target.value) })}
                                        onBlur={() => handleBlur("duration")}
                                        disabled={task.is_summary}
                                    />
                                </div>
                            </div>

                            {/* Notes */}
                            <div className="space-y-2">
                                <label htmlFor="notes" className="text-sm font-medium">Notes</label>
                                <Textarea
                                    id="notes"
                                    placeholder="Add task notes..."
                                    value={localData.notes ?? ""}
                                    onChange={(e) => setLocalData({ ...localData, notes: e.target.value })}
                                    onBlur={() => handleBlur("notes")}
                                    className="min-h-[120px] resize-y"
                                />
                            </div>

                            {/* Dependencies Placeholder */}
                            <div className="space-y-2 pt-4 border-t">
                                <div className="flex justify-between items-center mb-4">
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
                                            const predecessorTask = tasksData?.items?.find((t: any) => t.id === dep.predecessor_id);
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
                            </div>
                        </div>

                        {/* Add Dependency Dialog */}
                        <AddDependencyDialog
                            projectId={projectId}
                            successorTaskId={task.id}
                            isOpen={isDependencyDialogOpen}
                            onClose={() => setIsDependencyDialogOpen(false)}
                        />
                    </>
                )}
            </SheetContent>
        </Sheet>
    );
}
