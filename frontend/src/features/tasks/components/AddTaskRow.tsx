import type { KeyboardEvent } from "react";
import { useState, useRef, useEffect } from "react";
import { format } from "date-fns";
import { Plus, Loader2 } from "lucide-react";
import { TableRow, TableCell } from "@/shared/ui/table";
import { Button } from "@/shared/ui/button";
import { Input } from "@/shared/ui/input";
import { useCreateTask } from "@/features/tasks/hooks/useTasks";
import { toast } from "sonner";

interface AddTaskRowProps {
    projectId: string;
    colSpan: number;
    forceAdding?: boolean;
    onCancelAdding?: () => void;
}

export function AddTaskRow({ projectId, colSpan, forceAdding, onCancelAdding }: AddTaskRowProps) {
    const [isAdding, setIsAdding] = useState(false);
    const [taskName, setTaskName] = useState("");
    const createTask = useCreateTask(projectId);
    const isSubmitting = useRef(false);

    // Auto-open if parent forces it (e.g. from the empty state)
    useEffect(() => {
        if (forceAdding) {
            setIsAdding(true);
        }
    }, [forceAdding]);

    const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
        if (e.key === "Enter") {
            handleSubmit();
        } else if (e.key === "Escape") {
            handleCancel();
        }
    };

    const handleCancel = () => {
        setIsAdding(false);
        setTaskName("");
        if (onCancelAdding) {
            onCancelAdding();
        }
    };

    const handleSubmit = () => {
        if (isSubmitting.current) return;

        if (!taskName.trim()) {
            handleCancel();
            return;
        }

        isSubmitting.current = true;

        createTask.mutate(
            {
                name: taskName.trim(),
                start_date: format(new Date(), "yyyy-MM-dd"), // Default to today (local timezone safe)
                duration: 480, // Default 1 day (8 hours * 60 mins)
            },
            {
                onSuccess: () => {
                    setTaskName("");
                    isSubmitting.current = false;
                    // Keep it open for rapid consecutive entry
                },
                onError: () => {
                    isSubmitting.current = false;
                    toast.error("Failed to create task");
                },
            }
        );
    };

    if (!isAdding) {
        return (
            <TableRow className="hover:bg-transparent">
                <TableCell colSpan={colSpan} className="p-2">
                    <Button
                        variant="ghost"
                        size="sm"
                        className="w-full justify-start text-muted-foreground hover:text-foreground"
                        onClick={() => setIsAdding(true)}
                    >
                        <Plus className="mr-2 size-4" />
                        Add Task
                    </Button>
                </TableCell>
            </TableRow>
        );
    }

    return (
        <TableRow>
            <TableCell colSpan={colSpan} className="p-2">
                <div className="flex items-center gap-2">
                    <Input
                        autoFocus
                        placeholder="Task name..."
                        value={taskName}
                        onChange={(e) => setTaskName(e.target.value)}
                        onKeyDown={handleKeyDown}
                        onBlur={handleSubmit}
                        className="h-8 max-w-sm"
                        disabled={createTask.isPending}
                    />
                    {createTask.isPending && (
                        <Loader2 className="size-4 animate-spin text-muted-foreground" />
                    )}
                </div>
            </TableCell>
        </TableRow>
    );
}
