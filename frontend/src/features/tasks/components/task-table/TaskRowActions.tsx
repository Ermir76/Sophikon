import { useState } from "react";
import { MoreHorizontal, Indent, Outdent, Link, PanelRight, Trash2 } from "lucide-react";
import { Button } from "@/shared/ui/button";
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
import type { Task } from "@/features/tasks/types";

interface TaskRowActionsProps {
    task: Task;
    onIndent?: (taskId: string) => void;
    onOutdent?: (taskId: string) => void;
    onAddDependency?: (taskId: string) => void;
    onViewDetails?: (taskId: string) => void;
    onDelete?: (taskId: string) => void;
    isIndentPending?: boolean;
    isOutdentPending?: boolean;
    isDeletePending?: boolean;
}

export function TaskRowActions({
    task,
    onIndent,
    onOutdent,
    onAddDependency,
    onViewDetails,
    onDelete,
    isIndentPending,
    isOutdentPending,
    isDeletePending,
}: TaskRowActionsProps) {
    const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

    return (
        <div onClick={(e) => e.stopPropagation()}>
            <DropdownMenu>
                <DropdownMenuTrigger asChild>
                    <Button
                        variant="ghost"
                        size="icon"
                        className="size-8 text-muted-foreground hover:text-foreground"
                    >
                        <MoreHorizontal className="size-4" />
                        <span className="sr-only">Open actions menu</span>
                    </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end">
                    <DropdownMenuItem
                        disabled={isIndentPending}
                        onClick={() => onIndent?.(task.id)}
                    >
                        <Indent className="size-4" />
                        Indent
                    </DropdownMenuItem>
                    <DropdownMenuItem
                        disabled={isOutdentPending}
                        onClick={() => onOutdent?.(task.id)}
                    >
                        <Outdent className="size-4" />
                        Outdent
                    </DropdownMenuItem>
                    <DropdownMenuSeparator />
                    <DropdownMenuItem onClick={() => onAddDependency?.(task.id)}>
                        <Link className="size-4" />
                        Add Dependency
                    </DropdownMenuItem>
                    <DropdownMenuItem onClick={() => onViewDetails?.(task.id)}>
                        <PanelRight className="size-4" />
                        View Details
                    </DropdownMenuItem>
                    <DropdownMenuSeparator />
                    <DropdownMenuItem
                        disabled={isDeletePending}
                        className="text-destructive focus:text-destructive focus:bg-destructive/10"
                        onClick={() => setShowDeleteConfirm(true)}
                    >
                        <Trash2 className="size-4" />
                        Delete
                    </DropdownMenuItem>
                </DropdownMenuContent>
            </DropdownMenu>

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
                            onClick={() => onDelete?.(task.id)}
                        >
                            Delete
                        </AlertDialogAction>
                    </AlertDialogFooter>
                </AlertDialogContent>
            </AlertDialog>
        </div>
    );
}
