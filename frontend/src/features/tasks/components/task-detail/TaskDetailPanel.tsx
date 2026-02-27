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
            <SheetContent className="w-full sm:max-w-md md:max-w-2xl overflow-y-auto p-0 border-l border-border/50 shadow-2xl">
                {isLoading || !task ? (
                    <div className="flex justify-center items-center h-full">
                        <Loader2 className="size-8 animate-spin text-muted-foreground" />
                    </div>
                ) : (
                    <div className="flex flex-col h-full bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
                        {/* Header Section */}
                        <div className="px-6 py-6 border-b border-border/50 bg-muted/20">
                            <SheetHeader className="space-y-4">
                                <SheetTitle className="flex justify-between items-start gap-4 pr-8">
                                    <div className="flex flex-col gap-3 flex-1">
                                        <div className="flex items-center">
                                            <span className="inline-flex items-center rounded-md bg-primary/10 px-2 py-1 text-xs font-mono font-medium text-primary ring-1 ring-inset ring-primary/20">
                                                {task.wbs_code}
                                            </span>
                                        </div>
                                        <Input
                                            value={localData.name ?? ""}
                                            onChange={(e) => setLocalData({ ...localData, name: e.target.value })}
                                            onBlur={() => handleBlur("name")}
                                            className="text-2xl font-bold h-auto px-3 py-1.5 bg-transparent border-none hover:bg-muted/30 focus-visible:ring-0 focus-visible:outline-none focus-visible:shadow-none shadow-none rounded-md transition-colors w-full"
                                            placeholder="Task Name"
                                        />
                                    </div>
                                </SheetTitle>
                                <SheetDescription className="text-xs font-medium uppercase tracking-wider text-muted-foreground/70">
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
                            />

                            <div className="h-px w-full bg-border/50 rounded-full" />

                            <div className="space-y-4">
                                <h3 className="text-lg font-semibold tracking-tight">Dependencies</h3>
                                <div className="rounded-xl border border-border/50 bg-card shadow-sm overflow-hidden">
                                    <TaskDependencyList projectId={projectId} taskId={task.id} />
                                </div>
                            </div>
                        </div>
                    </div>
                )}
            </SheetContent>
        </Sheet>
    );
}
