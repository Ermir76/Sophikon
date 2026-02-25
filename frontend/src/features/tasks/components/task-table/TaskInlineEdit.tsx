import type { KeyboardEvent } from "react";
import { useState, useRef, useEffect } from "react";
import { Input } from "@/shared/ui/input";
import { useUpdateTask } from "@/features/tasks/hooks/useTasks";
import { toast } from "sonner";
import type { Task, TaskUpdate } from "@/features/tasks/types";

interface TaskInlineEditProps {
    task: Task;
    field: keyof TaskUpdate;
    value: string | number;
    type?: "text" | "number" | "date";
    disabled?: boolean;
    onSuccess?: () => void;
}

export function TaskInlineEdit({
    task,
    field,
    value: initialValue,
    type = "text",
    disabled = false,
    onSuccess,
}: TaskInlineEditProps) {
    const [isEditing, setIsEditing] = useState(false);
    const [value, setValue] = useState(initialValue);
    const updateTask = useUpdateTask(task.project_id);
    const inputRef = useRef<HTMLInputElement>(null);
    const isSubmitting = useRef(false);
    const isCancelling = useRef(false);

    // Sync local state if external data changes (e.g., from a refetch)
    useEffect(() => {
        setValue(initialValue);
    }, [initialValue]);

    useEffect(() => {
        if (isEditing && inputRef.current) {
            inputRef.current.focus();
        }
    }, [isEditing]);

    const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
        if (e.key === "Enter") {
            handleSubmit();
        } else if (e.key === "Escape") {
            isCancelling.current = true;
            setValue(initialValue);
            setIsEditing(false);
        }
    };

    const handleSubmit = () => {
        if (isCancelling.current) {
            isCancelling.current = false;
            return;
        }
        if (isSubmitting.current) return;

        setIsEditing(false);

        // Normalize value and initialValue for accurate comparison to prevent redundant API calls
        const isUnchangedText = type === "text" && value === initialValue;
        const isUnchangedNumber = type === "number" && Number(value) === Number(initialValue);

        // Prevent empty text or unchanged values
        if (isUnchangedText || isUnchangedNumber || (type === "text" && !String(value).trim())) {
            setValue(initialValue);
            return;
        }

        isSubmitting.current = true;

        const payload: TaskUpdate = {
            [field]: type === "number" ? Number(value) : value,
        };

        updateTask.mutate(
            { taskId: task.id, data: payload },
            {
                onSuccess: () => {
                    isSubmitting.current = false;
                    if (onSuccess) onSuccess();
                },
                onError: () => {
                    isSubmitting.current = false;
                    setValue(initialValue); // Revert on failure
                    toast.error(`Failed to update ${field}`);
                },
            }
        );
    };

    if (!isEditing) {
        if (disabled) {
            return (
                <div
                    className="p-1 -m-1 truncate min-h-[28px] w-full text-muted-foreground cursor-default"
                    onClick={(e) => e.stopPropagation()}
                >
                    {initialValue !== "" && initialValue != null ? initialValue : "—"}
                </div>
            );
        }

        return (
            <div
                className="cursor-text rounded border border-transparent hover:border-border hover:bg-muted/50 p-1 -m-1 truncate min-h-[28px] w-full transition-colors"
                onClick={(e) => {
                    e.stopPropagation();
                    setIsEditing(true);
                }}
            >
                {initialValue !== "" && initialValue != null ? (
                    initialValue
                ) : (
                    <span className="text-muted-foreground">—</span>
                )}
            </div>
        );
    }

    return (
        <Input
            ref={inputRef}
            type={type}
            value={value}
            onClick={(e) => e.stopPropagation()}
            onChange={(e) => setValue(e.target.value)}
            onKeyDown={handleKeyDown}
            onBlur={handleSubmit}
            className="h-7 w-full border-primary rounded-sm outline-none m-0 shadow-none px-1"
            disabled={updateTask.isPending}
        />
    );
}
