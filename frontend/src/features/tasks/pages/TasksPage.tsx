import { useState } from "react";
import { useParams, Navigate } from "react-router";
import { ListTodo, Trash2, Pencil } from "lucide-react";
import { isValid, parseISO, startOfDay } from "date-fns";
import type { RowSelectionState } from "@tanstack/react-table";
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
import { QueryError } from "@/shared/components/QueryError";
import { useTasks, useIndentTask, useOutdentTask, useReorderTask, useDeleteTask, useBulkDeleteTasks } from "@/features/tasks/hooks/useTasks";
import { TaskTable } from "@/features/tasks/components/task-table/TaskTable";
import { TaskDetailPanel } from "@/features/tasks/components/task-detail/TaskDetailPanel";
import { AddDependencyDialog } from "@/features/tasks/components/task-detail/AddDependencyDialog";
import { BulkEditDialog } from "@/features/tasks/components/BulkEditDialog";
import { toast } from "sonner";
import type { Task } from "@/features/tasks/types";

import { PageShell } from "@/shared/components/layout/PageShell";
import { PageHeader } from "@/shared/components/layout/PageHeader";
import { PageLoading } from "@/shared/components/state/PageLoading";
import { PageEmpty } from "@/shared/components/state/PageEmpty";

const EMPTY_TASKS: Task[] = [];

function isPastDueDate(dateValue: string, now: Date): boolean {
  const parsed = parseISO(dateValue);
  if (!isValid(parsed)) return false;
  return parsed < startOfDay(now);
}

export default function TasksPage() {
  const shellClassName = "h-full overflow-y-auto";
  const { projectId } = useParams<{ projectId: string }>();

  // Local state for table row selection
  const [rowSelection, setRowSelection] = useState<RowSelectionState>({});

  // Row highlight state and detail panel state are intentionally decoupled.
  const [selectedTaskId, setSelectedTaskId] = useState<string | null>(null);
  const [detailTaskId, setDetailTaskId] = useState<string | null>(null);

  // Add Dependency dialog state (triggered from row kebab menu)
  const [dependencyTaskId, setDependencyTaskId] = useState<string | null>(null);

  // Local state to override empty view and show the table with the inline row
  const [isAddingFirstTask, setIsAddingFirstTask] = useState(false);

  // Bulk delete confirmation dialog state
  const [showBulkDeleteConfirm, setShowBulkDeleteConfirm] = useState(false);
  const [showBulkEdit, setShowBulkEdit] = useState(false);

  // Fetch task data
  const { data, isLoading, isError, refetch } = useTasks(projectId);
  const indentTask = useIndentTask(projectId);
  const outdentTask = useOutdentTask(projectId);
  const reorderTask = useReorderTask(projectId);
  const deleteTask = useDeleteTask(projectId);
  const bulkDeleteTasks = useBulkDeleteTasks(projectId);

  // Ensure data structure safely maps out items array
  const tasks = data?.items ?? EMPTY_TASKS;
  const now = new Date();
  const overdueTasks = tasks.filter(
    (task) => task.percent_complete < 100 && isPastDueDate(task.finish_date, now),
  ).length;
  const inProgressTasks = tasks.filter(
    (task) => task.percent_complete > 0 && task.percent_complete < 100,
  ).length;
  const highPriorityTasks = tasks.filter((task) => Number(task.priority) >= 700).length;

  // Compute selected task IDs from rowSelection state
  const selectedTaskIds = Object.keys(rowSelection).filter((id) => rowSelection[id]);
  const selectionCount = selectedTaskIds.length;
  const selectedTaskIdSet = new Set(selectedTaskIds);
  const selectedTasks = tasks.filter((task) => selectedTaskIdSet.has(task.id));

  const isAddingFirstTaskMode = isAddingFirstTask && tasks.length === 0;

  // Single task delete handler (used by row actions + detail panel)
  const handleDeleteTask = async (taskId: string) => {
    try {
      await deleteTask.mutateAsync(taskId);
      toast.success("Task deleted");
      // Close detail panel if the deleted task was being viewed
      if (detailTaskId === taskId) {
        setDetailTaskId(null);
      }
      if (selectedTaskId === taskId) setSelectedTaskId(null);
      // Remove from selection if selected
      setRowSelection((prev) => {
        const next = { ...prev };
        delete next[taskId];
        return next;
      });
    } catch {
      toast.error("Failed to delete task");
    }
  };

  // Bulk delete handler
  const handleBulkDelete = async () => {
    try {
      const result = await bulkDeleteTasks.mutateAsync({ task_ids: selectedTaskIds });
      toast.success(`${result.succeeded} task(s) deleted`);
      setRowSelection({});
      setShowBulkDeleteConfirm(false);
    } catch {
      toast.error("Failed to delete tasks");
      setShowBulkDeleteConfirm(false);
    }
  };

  if (!projectId) {
    return <Navigate to="/projects" replace />;
  }

  if (isError) {
    return (
      <PageShell className={shellClassName}>
        <QueryError
          message="Failed to load project tasks."
          onRetry={() => refetch()}
        />
      </PageShell>
    );
  }

  return (
    <PageShell className={shellClassName}>
      {/* Header section */}
      <PageHeader
        title="Tasks"
        description="Plan, sequence, and update task execution."
      />

      {!isLoading && tasks.length > 0 ? (
        <div className="grid gap-2 sm:grid-cols-2 xl:grid-cols-4">
          <div className="rounded-md border bg-card/70 px-3 py-2">
            <p className="text-[10px] uppercase tracking-wide text-muted-foreground">Total</p>
            <p className="mt-1 text-lg font-semibold tabular-nums">{tasks.length}</p>
          </div>
          <div className="rounded-md border bg-card/70 px-3 py-2">
            <p className="text-[10px] uppercase tracking-wide text-muted-foreground">In Progress</p>
            <p className="mt-1 text-lg font-semibold tabular-nums text-primary">{inProgressTasks}</p>
          </div>
          <div className="rounded-md border bg-card/70 px-3 py-2">
            <p className="text-[10px] uppercase tracking-wide text-muted-foreground">Overdue</p>
            <p className="mt-1 text-lg font-semibold tabular-nums text-destructive">{overdueTasks}</p>
          </div>
          <div className="rounded-md border bg-card/70 px-3 py-2">
            <p className="text-[10px] uppercase tracking-wide text-muted-foreground">High Priority</p>
            <p className="mt-1 text-lg font-semibold tabular-nums text-destructive">{highPriorityTasks}</p>
          </div>
        </div>
      ) : null}

      {isLoading ? (
        <PageLoading />
      ) : tasks.length === 0 && !isAddingFirstTaskMode ? (
        <PageEmpty
          icon={ListTodo}
          title="No tasks"
          description="You haven't added any tasks to this project yet."
          action={
            <Button variant="outline" onClick={() => setIsAddingFirstTask(true)}>
              Add task
            </Button>
          }
        />
      ) : (
        <div className="animate-in fade-in duration-200">
          <TaskTable
            projectId={projectId}
            data={tasks}
            rowSelection={rowSelection}
            setRowSelection={setRowSelection}
            forceAdding={isAddingFirstTaskMode}
            onCancelAdding={() => setIsAddingFirstTask(false)}
            onIndent={async (id) => {
              try { await indentTask.mutateAsync(id); } catch { toast.error("Failed to indent task"); }
            }}
            onOutdent={async (id) => {
              try { await outdentTask.mutateAsync(id); } catch { toast.error("Failed to outdent task"); }
            }}
            onAddDependency={(id) => setDependencyTaskId(id)}
            onViewDetails={(id) => {
              setSelectedTaskId(id);
              setDetailTaskId(id);
            }}
            onDelete={handleDeleteTask}
            isIndentPending={indentTask.isPending}
            isOutdentPending={outdentTask.isPending}
            isDeletePending={deleteTask.isPending}
            onReorder={async (taskId, afterTaskId, beforeTaskId, sortedData) => {
              try {
                await reorderTask.mutateAsync({
                  taskId,
                  data: {
                    after_task_id: afterTaskId || null,
                    before_task_id: beforeTaskId || null
                  },
                  optimisticData: sortedData
                });
              } catch {
                toast.error("Failed to reorder task");
              }
            }}
          />
        </div>
      )}

      {/* Floating bulk-action toolbar */}
      {selectionCount > 0 && (
        <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-50 animate-in slide-in-from-bottom-4 fade-in duration-200">
          <div className="flex items-center gap-3 rounded-xl border bg-card px-5 py-3 shadow-sm">
            <span className="text-sm font-semibold text-primary">
              {selectionCount} selected
            </span>
            <div className="h-5 w-px bg-border" />
            <Button
              variant="outline"
              size="sm"
              className="h-8 text-xs font-medium gap-1.5"
              onClick={() => setShowBulkEdit(true)}
            >
              <Pencil className="size-3.5" />
              Edit
            </Button>
            <Button
              variant="destructive"
              size="sm"
              className="h-8 text-xs font-medium gap-1.5"
              disabled={bulkDeleteTasks.isPending}
              onClick={() => setShowBulkDeleteConfirm(true)}
            >
              <Trash2 className="size-3.5" />
              Delete
            </Button>
          </div>
        </div>
      )}

      {/* Bulk delete confirmation dialog */}
      <AlertDialog open={showBulkDeleteConfirm} onOpenChange={setShowBulkDeleteConfirm}>
        <AlertDialogContent variant="destructive">
          <AlertDialogHeader>
            <AlertDialogTitle>Delete {selectionCount} task{selectionCount !== 1 ? "s" : ""}?</AlertDialogTitle>
            <AlertDialogDescription>
              This will permanently delete the selected task{selectionCount !== 1 ? "s" : ""}. This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              variant="destructive"
              disabled={bulkDeleteTasks.isPending}
              onClick={handleBulkDelete}
            >
              {bulkDeleteTasks.isPending ? "Deleting..." : "Delete"}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Slide-out Panel for Task Core Edit */}
      <TaskDetailPanel
        projectId={projectId}
        taskId={detailTaskId}
        isOpen={!!detailTaskId}
        onClose={() => setDetailTaskId(null)}
        onDelete={handleDeleteTask}
        isDeletePending={deleteTask.isPending}
        floating
      />

      {/* Add Dependency Dialog triggered from row kebab menu */}
      {dependencyTaskId && (
        <AddDependencyDialog
          projectId={projectId}
          successorTaskId={dependencyTaskId}
          isOpen={true}
          onClose={() => setDependencyTaskId(null)}
        />
      )}

      {/* Bulk Edit Dialog */}
      {showBulkEdit && (
        <BulkEditDialog
          projectId={projectId}
          selectedTaskIds={selectedTaskIds}
          selectedTasks={selectedTasks}
          isOpen={showBulkEdit}
          onClose={() => setShowBulkEdit(false)}
          onSuccess={() => {
            setRowSelection({});
            setShowBulkEdit(false);
          }}
        />
      )}
    </PageShell>
  );
}
