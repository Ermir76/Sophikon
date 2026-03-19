import { useState, useRef } from "react";
import { ExternalLink, Link2, Flag, Trash2, Copy } from "lucide-react";
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuSeparator,
    DropdownMenuTrigger,
} from "@/shared/ui/dropdown-menu";
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
import { AddDependencyDialog, useUpdateTask, useDeleteTask } from "@/features/tasks";
import type { Task } from "@/features/tasks";
import { toast } from "sonner";

interface GanttContextMenuProps {
    task: Task;
    projectId: string;
    x: number;
    y: number;
    onClose: () => void;
    onOpenDetails: (taskId: string) => void;
}

export function GanttContextMenu({
    task,
    projectId,
    x,
    y,
    onClose,
    onOpenDetails,
}: GanttContextMenuProps) {
    const [showAddDep, setShowAddDep] = useState(false);
    const [showDelete, setShowDelete] = useState(false);
    // Prevents the DropdownMenu's onOpenChange from calling onClose while a sub-dialog is opening.
    // State updates from onSelect are batched and haven't re-rendered yet when onOpenChange fires,
    // so we use a ref to track intent synchronously.
    const suppressClose = useRef(false);

    const updateTask = useUpdateTask(projectId);
    const deleteTask = useDeleteTask(projectId);

    return (
        <>
            <DropdownMenu
                open
                onOpenChange={(open) => {
                    if (!open && !suppressClose.current) onClose();
                }}
            >
                <DropdownMenuTrigger asChild>
                    <div style={{ position: "fixed", left: x, top: y, width: 0, height: 0 }} />
                </DropdownMenuTrigger>
                <DropdownMenuContent align="start" onCloseAutoFocus={(e) => e.preventDefault()}>
                    <DropdownMenuItem onSelect={() => { onOpenDetails(task.id); onClose(); }}>
                        <ExternalLink className="size-4 mr-2" />
                        Open Details
                    </DropdownMenuItem>
                    <DropdownMenuItem onSelect={() => {
                        suppressClose.current = true;
                        setShowAddDep(true);
                    }}>
                        <Link2 className="size-4 mr-2" />
                        Add Dependency
                    </DropdownMenuItem>
                    <DropdownMenuItem onSelect={() => {
                        updateTask.mutate(
                            { taskId: task.id, data: { is_milestone: !task.is_milestone } },
                            { onSuccess: () => toast.success(task.is_milestone ? "Milestone unset" : "Set as milestone") },
                        );
                        onClose();
                    }}>
                        <Flag className="size-4 mr-2" />
                        {task.is_milestone ? "Unset Milestone" : "Set as Milestone"}
                    </DropdownMenuItem>
                    <DropdownMenuItem
                        className="text-destructive focus:text-destructive"
                        onSelect={() => {
                            suppressClose.current = true;
                            setShowDelete(true);
                        }}
                    >
                        <Trash2 className="size-4 mr-2" />
                        Delete Task
                    </DropdownMenuItem>
                    <DropdownMenuSeparator />
                    <DropdownMenuItem onSelect={() => {
                        navigator.clipboard.writeText(task.wbs_code);
                        toast.success(`Copied ${task.wbs_code}`);
                        onClose();
                    }}>
                        <Copy className="size-4 mr-2" />
                        Copy WBS Code
                    </DropdownMenuItem>
                </DropdownMenuContent>
            </DropdownMenu>

            <AddDependencyDialog
                projectId={projectId}
                successorTaskId={task.id}
                isOpen={showAddDep}
                onClose={() => {
                    suppressClose.current = false;
                    setShowAddDep(false);
                    onClose();
                }}
            />

            <AlertDialog
                open={showDelete}
                onOpenChange={(open) => {
                    if (!open) {
                        suppressClose.current = false;
                        setShowDelete(false);
                        onClose();
                    }
                }}
            >
                <AlertDialogContent>
                    <AlertDialogHeader>
                        <AlertDialogTitle>Delete task?</AlertDialogTitle>
                        <AlertDialogDescription>
                            "{task.name}" will be permanently deleted. This cannot be undone.
                        </AlertDialogDescription>
                    </AlertDialogHeader>
                    <AlertDialogFooter>
                        <AlertDialogCancel>Cancel</AlertDialogCancel>
                        <AlertDialogAction
                            className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                            onClick={() => {
                                deleteTask.mutate(task.id, {
                                    onSuccess: () => toast.success("Task deleted"),
                                    onError: () => toast.error("Failed to delete task"),
                                });
                            }}
                        >
                            Delete
                        </AlertDialogAction>
                    </AlertDialogFooter>
                </AlertDialogContent>
            </AlertDialog>
        </>
    );
}
