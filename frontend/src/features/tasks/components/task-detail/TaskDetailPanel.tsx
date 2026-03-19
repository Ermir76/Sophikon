import { useState, useEffect, useRef, useCallback } from "react";
import { createPortal } from "react-dom";
import { format, parseISO } from "date-fns";
import { Loader2, Trash2, X, GripHorizontal } from "lucide-react";
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
import { useProjectMembers } from "@/features/projects/hooks/useProjectMembers";
import { TaskDependencyList } from "@/features/tasks/components/task-detail/TaskDependencyList";
import { TaskAssignmentList } from "@/features/tasks/components/task-detail/TaskAssignmentList";
import { TaskAttachmentList } from "@/features/tasks/components/task-detail/TaskAttachmentList";
import { TaskDetailCoreFields } from "@/features/tasks/components/task-detail/TaskDetailCoreFields";
import { CommentThread } from "@/features/tasks/components/task-detail/CommentThread";
import { useCalendars } from "@/features/calendar";
import { useAuthStore } from "@/features/auth/store/auth-store";
import { toast } from "sonner";
import type { TaskUpdate } from "@/features/tasks/types";

interface TaskDetailPanelProps {
    projectId: string;
    taskId: string | null;
    isOpen: boolean;
    onClose: () => void;
    onDelete?: (taskId: string) => void;
    isDeletePending?: boolean;
    floating?: boolean;
}

export function TaskDetailPanel({ projectId, taskId, isOpen, onClose, onDelete, isDeletePending, floating }: TaskDetailPanelProps) {
    const { data: task, isLoading } = useTask(projectId, taskId ?? undefined);
    const updateTask = useUpdateTask(projectId);
    const calendarsQuery = useCalendars(projectId);
    const membersQuery = useProjectMembers(projectId);
    const currentUserId = useAuthStore((state) => state.user?.id ?? null);
    const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

    // Floating window state
    const [pos, setPos] = useState({ x: Math.max(0, window.innerWidth / 2 - 240), y: 80 });
    const [size, setSize] = useState({ w: 480, h: 600 });
    const dragRef = useRef<{ startX: number; startY: number; startPosX: number; startPosY: number } | null>(null);
    const resizeRef = useRef<{ startX: number; startY: number; startW: number; startH: number; startPosX: number; startPosY: number; dir: string } | null>(null);

    const handleTitleBarPointerDown = useCallback((e: React.PointerEvent) => {
        if ((e.target as HTMLElement).closest("button")) return;
        e.currentTarget.setPointerCapture(e.pointerId);
        dragRef.current = { startX: e.clientX, startY: e.clientY, startPosX: pos.x, startPosY: pos.y };
    }, [pos]);

    const handleTitleBarPointerMove = useCallback((e: React.PointerEvent) => {
        if (!dragRef.current) return;
        const dx = e.clientX - dragRef.current.startX;
        const dy = e.clientY - dragRef.current.startY;
        setPos({ x: dragRef.current.startPosX + dx, y: dragRef.current.startPosY + dy });
    }, []);

    const handleTitleBarPointerUp = useCallback(() => { dragRef.current = null; }, []);

    const handleResizePointerDown = useCallback((e: React.PointerEvent, dir: string) => {
        e.stopPropagation();
        e.currentTarget.setPointerCapture(e.pointerId);
        resizeRef.current = { startX: e.clientX, startY: e.clientY, startW: size.w, startH: size.h, startPosX: pos.x, startPosY: pos.y, dir };
    }, [size, pos]);

    const handleResizePointerMove = useCallback((e: React.PointerEvent) => {
        if (!resizeRef.current) return;
        const { startX, startY, startW, startH, startPosX, startPosY, dir } = resizeRef.current;
        const dx = e.clientX - startX;
        const dy = e.clientY - startY;
        let newW = startW, newH = startH, newX = startPosX, newY = startPosY;
        if (dir.includes("e")) newW = Math.max(320, startW + dx);
        if (dir.includes("w")) { newW = Math.max(320, startW - dx); newX = startPosX + (startW - newW); }
        if (dir.includes("s")) newH = Math.max(300, startH + dy);
        if (dir.includes("n")) { newH = Math.max(300, startH - dy); newY = startPosY + (startH - newH); }
        setSize({ w: newW, h: newH });
        setPos({ x: newX, y: newY });
    }, []);

    const handleResizePointerUp = useCallback(() => { resizeRef.current = null; }, []);

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
                calendar_id: task.calendar_id ?? null,
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
    const currentMember = membersQuery.data?.items.find((member) => member.user_id === currentUserId);
    const canModerateComments = currentMember?.role === "owner" || currentMember?.role === "manager";
    const canManageAttachments = currentMember?.role !== "viewer";

    const bodyContent = isLoading || !task ? (
        <div className="flex justify-center items-center h-full">
            <Loader2 className="size-8 animate-spin text-muted-foreground" />
        </div>
    ) : (
        <div className="flex h-full flex-col bg-background">
            {/* Header Section */}
            <div className="sticky top-0 z-10 border-b bg-background/95 px-4 py-4 backdrop-blur supports-[backdrop-filter]:bg-background/85 sm:px-5">
                <div className="space-y-3">
                    <div className="flex items-start justify-between gap-4 pr-8">
                        <div className="flex flex-1 flex-col gap-2.5">
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
                                className="h-auto w-full border-0 px-2.5 py-1 text-xl font-bold shadow-none focus-visible:ring-0"
                                placeholder="Task Name"
                            />
                        </div>
                    </div>
                    <p className="text-[11px] font-medium uppercase tracking-wide text-muted-foreground/90">
                        Created on {format(parseISO(task.created_at), "MMMM do, yyyy")}
                    </p>
                </div>
            </div>

            {/* Scrolling Body content */}
            <div className="flex-1 space-y-6 overflow-y-auto p-4 sm:p-5">
                <TaskDetailCoreFields
                    task={task}
                    localData={localData}
                    setLocalData={setLocalData}
                    handleBlur={handleBlur}
                    calendarOptions={(calendarsQuery.data ?? []).map((calendar) => ({
                        id: calendar.id,
                        name: calendar.name,
                    }))}
                    onCalendarChange={async (calendarId) => {
                        try {
                            await updateTask.mutateAsync({ taskId: task.id, data: { calendar_id: calendarId } });
                        } catch {
                            toast.error("Failed to update calendar");
                        }
                    }}
                    onColorChange={async (color) => {
                        try {
                            await updateTask.mutateAsync({ taskId: task.id, data: { color } });
                        } catch {
                            toast.error("Failed to update color");
                        }
                    }}
                />
                <div className="h-px w-full rounded-full bg-border/80" />
                <div className="space-y-3">
                    <h3 className="text-sm font-semibold uppercase tracking-wide text-muted-foreground">Dependencies</h3>
                    <div className="overflow-hidden rounded-xl border bg-card">
                        <TaskDependencyList projectId={projectId} taskId={task.id} />
                    </div>
                </div>
                <div className="h-px w-full rounded-full bg-border/80" />
                <div className="space-y-3">
                    <h3 className="text-sm font-semibold uppercase tracking-wide text-muted-foreground">Assignments</h3>
                    <div className="overflow-hidden rounded-xl border bg-card">
                        <TaskAssignmentList projectId={projectId} taskId={task.id} />
                    </div>
                </div>
                <div className="h-px w-full rounded-full bg-border/80" />
                <div className="space-y-3">
                    <h3 className="text-sm font-semibold uppercase tracking-wide text-muted-foreground">Attachments</h3>
                    <div className="overflow-hidden rounded-xl border bg-card">
                        <TaskAttachmentList projectId={projectId} taskId={task.id} canManage={canManageAttachments} />
                    </div>
                </div>
                <div className="h-px w-full rounded-full bg-border/80" />
                <CommentThread projectId={projectId} taskId={task.id} canModerate={canModerateComments} />
            </div>
        </div>
    );

    return (<>
        {floating ? (
            isOpen ? createPortal(
                <div
                    className="fixed z-50 flex flex-col rounded-lg border border-border bg-background overflow-hidden"
                    style={{ left: pos.x, top: pos.y, width: size.w, height: size.h, boxShadow: "0 25px 60px 0 rgba(0,0,0,0.7), 0 8px 20px 0 rgba(0,0,0,0.5)" }}
                    onPointerMove={(e) => { handleTitleBarPointerMove(e); handleResizePointerMove(e); }}
                    onPointerUp={() => { handleTitleBarPointerUp(); handleResizePointerUp(); }}
                >
                    {/* Drag handle / title bar */}
                    <div
                        className="flex shrink-0 items-center justify-between border-b bg-muted/40 px-3 py-2 cursor-grab active:cursor-grabbing select-none"
                        onPointerDown={handleTitleBarPointerDown}
                        onPointerMove={handleTitleBarPointerMove}
                        onPointerUp={handleTitleBarPointerUp}
                    >
                        <div className="flex items-center gap-2 text-xs text-muted-foreground">
                            <GripHorizontal className="size-3.5" />
                            <span>Task Detail</span>
                        </div>
                        <Button variant="ghost" size="icon" className="size-6" onClick={onClose}>
                            <X className="size-3.5" />
                        </Button>
                    </div>

                    {/* Content */}
                    <div className="flex-1 overflow-hidden">
                        {bodyContent}
                    </div>

                    {/* Resize handles */}
                    {/* Edges */}
                    <div className="absolute inset-x-0 top-0 h-1 cursor-n-resize" onPointerDown={(e) => handleResizePointerDown(e, "n")} />
                    <div className="absolute inset-x-0 bottom-0 h-1 cursor-s-resize" onPointerDown={(e) => handleResizePointerDown(e, "s")} />
                    <div className="absolute inset-y-0 left-0 w-1 cursor-w-resize" onPointerDown={(e) => handleResizePointerDown(e, "w")} />
                    <div className="absolute inset-y-0 right-0 w-1 cursor-e-resize" onPointerDown={(e) => handleResizePointerDown(e, "e")} />
                    {/* Corners */}
                    <div className="absolute top-0 left-0 size-3 cursor-nw-resize" onPointerDown={(e) => handleResizePointerDown(e, "nw")} />
                    <div className="absolute top-0 right-0 size-3 cursor-ne-resize" onPointerDown={(e) => handleResizePointerDown(e, "ne")} />
                    <div className="absolute bottom-0 left-0 size-3 cursor-sw-resize" onPointerDown={(e) => handleResizePointerDown(e, "sw")} />
                    <div className="absolute bottom-0 right-0 size-3 cursor-se-resize" onPointerDown={(e) => handleResizePointerDown(e, "se")} />
                </div>,
                document.body
            ) : null
        ) : (
            <Sheet open={isOpen} onOpenChange={(open) => !open && onClose()}>
                <SheetContent className="w-full overflow-y-auto p-0 sm:max-w-md md:max-w-xl">
                    <SheetHeader className="sr-only">
                        <SheetTitle>Task Detail</SheetTitle>
                        <SheetDescription>Edit task properties</SheetDescription>
                    </SheetHeader>
                    {bodyContent}
                </SheetContent>
            </Sheet>
        )}

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
