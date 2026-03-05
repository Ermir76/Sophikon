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
import { Badge } from "@/shared/ui/badge";
import { Input } from "@/shared/ui/input";
import { Button } from "@/shared/ui/button";
import {
    AlertDialog,
    AlertDialogAction,
    AlertDialogCancel,
    AlertDialogContent,
    AlertDialogDescription,
    AlertDialogFooter,
    AlertDialogHeader,
    AlertDialogTitle,
} from "@/shared/ui/alert-dialog";
import { useTask, useUpdateTask } from "@/features/tasks/hooks/useTasks";
import { TaskDependencyList } from "@/features/tasks/components/task-detail/TaskDependencyList";
import { TaskAssignmentList } from "@/features/tasks/components/task-detail/TaskAssignmentList";
import { TaskDetailCoreFields } from "@/features/tasks/components/task-detail/TaskDetailCoreFields";
import { toast } from "sonner";
import type { TaskUpdate } from "@/features/tasks/types";

interface TaskDetailPanelProps {
    projectId: string;
    taskId: string | null;
    isOpen: boolean;
    onClose: () => void;
    onDelete?: (taskId: string) => void;
    isDeletePending?: boolean;
}

export function TaskDetailPanel({ projectId, taskId, isOpen, onClose, onDelete, isDeletePending }: TaskDetailPanelProps) {
    const { data: task, isLoading } = useTask(projectId, taskId ?? undefined);
    const updateTask = useUpdateTask(projectId);
    const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

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
    const handleBlur = async (field: keyof TaskUpdate) => {
        if (!task) return;

        const currentValue = localData[field];
        let originalValue = task[field as keyof typeof task] as TaskUpdate[typeof field];

        if (field === "start_date" && originalValue) {
            originalValue = String(originalValue).split("T")[0];
        } else if (field === "notes" && !originalValue) {
            originalValue = "";
        }

        if (currentValue !== originalValue) {
            try {
                await updateTask.mutateAsync({ taskId: task.id, data: { [field]: currentValue } });
            } catch (error) {
                toast.error(`Failed to update ${field}`);
                // Rebound the local state on failure
                setLocalData((prev) => ({ ...prev, [field]: originalValue }));
            }
        }
    };

    return (<>
        <Sheet open={isOpen} onOpenChange={(open) => !open && onClose()}>
            <SheetContent className="w-full overflow-y-auto p-0 sm:max-w-md md:max-w-2xl">
                {isLoading || !task ? (
                    <div className="flex justify-center items-center h-full">
                        <Loader2 className="size-8 animate-spin text-muted-foreground" />
                    </div>
                ) : (
                    <div className="flex h-full flex-col bg-background">
                        {/* Header Section */}
                        <div className="border-b px-6 py-6">
                            <SheetHeader className="space-y-4">
                                <SheetTitle className="flex justify-between items-start gap-4 pr-8">
                                    <div className="flex flex-col gap-3 flex-1">
                                        <div className="flex items-center gap-2">
                                            <Badge variant="outline" className="rounded-md px-2 py-1 font-mono text-xs font-medium">
                                                {task.wbs_code}
                                            </Badge>
                                            <Button
                                                variant="ghost"
                                                size="icon"
                                                className="size-8"
                                                disabled={isDeletePending}
                                                onClick={() => setShowDeleteConfirm(true)}
                                            >
                                                <Trash2 className="size-4" />
                                            </Button>
                                        </div>
                                        <Input
                                            value={localData.name ?? ""}
                                            onChange={(e) => setLocalData({ ...localData, name: e.target.value })}
                                            onBlur={() => handleBlur("name")}
                                            className="h-auto w-full border-0 px-3 py-1.5 text-2xl font-bold shadow-none focus-visible:ring-0"
                                            placeholder="Task Name"
                                        />
                                    </div>
                                </SheetTitle>
                                <SheetDescription className="text-xs font-medium uppercase tracking-wider">
                                    Created on {format(parseISO(task.created_at), "MMMM do, yyyy")}
                                </SheetDescription>
                            </SheetHeader>
                        </div>

                        {/* Scrolling Body content */}
                        <div className="flex-1 overflow-y-auto p-6 space-y-10">
                            <TaskDetailCoreFields
                                task={task}
                                localData={localData}
                                setLocalData={setLocalData}
                                handleBlur={handleBlur}
                                onColorChange={async (color) => {
                                    try {
                                        await updateTask.mutateAsync({ taskId: task.id, data: { color } });
                                    } catch {
                                        toast.error("Failed to update color");
                                    }
                                }}
                            />

                            <div className="h-px w-full bg-border rounded-full" />

                            <div className="space-y-4">
                                <h3 className="text-lg font-semibold tracking-tight">Dependencies</h3>
                                <div className="overflow-hidden rounded-xl border bg-card">
                                    <TaskDependencyList projectId={projectId} taskId={task.id} />
                                </div>
                            </div>

                            <div className="h-px w-full bg-border rounded-full" />

                            <div className="space-y-4">
                                <h3 className="text-lg font-semibold tracking-tight">Assignments</h3>
                                <div className="overflow-hidden rounded-xl border bg-card">
                                    <TaskAssignmentList projectId={projectId} taskId={task.id} />
                                </div>
                            </div>
                        </div>
                    </div>
                )}
            </SheetContent>
        </Sheet>

        {task && (
            <AlertDialog open={showDeleteConfirm} onOpenChange={setShowDeleteConfirm}>
                <AlertDialogContent variant="destructive">
                    <AlertDialogHeader>
                        <AlertDialogTitle>Delete task?</AlertDialogTitle>
                        <AlertDialogDescription>
                            This will permanently delete "{task.name}". This action cannot be undone.
                        </AlertDialogDescription>
                    </AlertDialogHeader>
                    <AlertDialogFooter>
                        <AlertDialogCancel>Cancel</AlertDialogCancel>
                        <AlertDialogAction
                            variant="destructive"
                            onClick={() => {
                                onDelete?.(task.id);
                                setShowDeleteConfirm(false);
                            }}
                        >
                            Delete
                        </AlertDialogAction>
                    </AlertDialogFooter>
                </AlertDialogContent>
            </AlertDialog>
        )}
    </>);
}
