import { MoreHorizontal, Indent, Outdent, Link, PanelRight } from "lucide-react";
import { Button } from "@/shared/ui/button";
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuSeparator,
    DropdownMenuTrigger,
} from "@/shared/ui/dropdown-menu";
import type { Task } from "@/features/tasks/types";

interface TaskRowActionsProps {
    task: Task;
    onIndent?: (taskId: string) => void;
    onOutdent?: (taskId: string) => void;
    onAddDependency?: (taskId: string) => void;
    onViewDetails?: (taskId: string) => void;
    isIndentPending?: boolean;
    isOutdentPending?: boolean;
}

export function TaskRowActions({
    task,
    onIndent,
    onOutdent,
    onAddDependency,
    onViewDetails,
    isIndentPending,
    isOutdentPending,
}: TaskRowActionsProps) {
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
                </DropdownMenuContent>
            </DropdownMenu>
        </div>
    );
}
