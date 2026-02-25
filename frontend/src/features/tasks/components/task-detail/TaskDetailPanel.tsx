import { useState, useEffect } from "react";
import { format, parseISO } from "date-fns";
import { Loader2 } from "lucide-react";
import {
    Sheet,
    SheetContent,
    SheetHeader,
    SheetTitle,
    SheetDescription,
} from "@/shared/ui/sheet";
import { Input } from "@/shared/ui/input";
import { useTask, useUpdateTask } from "@/features/tasks/hooks/useTasks";
import { TaskDependencyList } from "@/features/tasks/components/task-detail/TaskDependencyList";
import { TaskDetailCoreFields } from "@/features/tasks/components/task-detail/TaskDetailCoreFields";
import { toast } from "sonner";
import type { TaskUpdate } from "@/features/tasks/types";

interface TaskDetailPanelProps {
    projectId: string;
    taskId: string | null;
    isOpen: boolean;
    onClose: () => void;
}

export function TaskDetailPanel({ projectId, taskId, isOpen, onClose }: TaskDetailPanelProps) {
    const { data: task, isLoading } = useTask(projectId, taskId ?? undefined);
    const updateTask = useUpdateTask(projectId);

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
                            <TaskDetailCoreFields
                                task={task}
                                localData={localData}
                                setLocalData={setLocalData}
                                handleBlur={handleBlur}
                            />

                            {/* Dependencies Placeholder */}
                            <TaskDependencyList projectId={projectId} taskId={task.id} />
                        </div>
                    </>
                )}
            </SheetContent>
        </Sheet>
    );
}
