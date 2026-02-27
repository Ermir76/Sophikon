import { useState, useEffect } from "react";
import { useParams, Navigate } from "react-router";
import { Loader2, ListTodo, Trash2 } from "lucide-react";
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
import { toast } from "sonner";
import type { Task } from "@/features/tasks/types";

const EMPTY_TASKS: Task[] = [];

export default function TasksPage() {
  const { projectId } = useParams<{ projectId: string }>();

  // Local state for table row selection
  const [rowSelection, setRowSelection] = useState<RowSelectionState>({});

  // Detail panel state
  const [selectedTaskId, setSelectedTaskId] = useState<string | null>(null);

  // Add Dependency dialog state (triggered from row kebab menu)
  const [dependencyTaskId, setDependencyTaskId] = useState<string | null>(null);

  // Local state to override empty view and show the table with the inline row
  const [isAddingFirstTask, setIsAddingFirstTask] = useState(false);

  // Bulk delete confirmation dialog state
  const [showBulkDeleteConfirm, setShowBulkDeleteConfirm] = useState(false);

  // Fetch task data
  const { data, isLoading, isError, refetch } = useTasks(projectId);
  const indentTask = useIndentTask(projectId);
  const outdentTask = useOutdentTask(projectId);
  const reorderTask = useReorderTask(projectId);
  const deleteTask = useDeleteTask(projectId);
  const bulkDeleteTasks = useBulkDeleteTasks(projectId);

  // Ensure data structure safely maps out items array
  const tasks = data?.items ?? EMPTY_TASKS;

  // Compute selected task IDs from rowSelection state
  const selectedTaskIds = Object.keys(rowSelection).filter((id) => rowSelection[id]);
  const selectionCount = selectedTaskIds.length;

  // Reset the "adding first task" state if tasks are successfully loaded from the backend
  useEffect(() => {
    if (tasks.length > 0 && isAddingFirstTask) {
      setIsAddingFirstTask(false);
    }
  }, [tasks.length, isAddingFirstTask]);

  // Single task delete handler (used by row actions + detail panel)
  const handleDeleteTask = (taskId: string) => {
    deleteTask.mutate(taskId, {
      onSuccess: () => {
        toast.success("Task deleted");
        // Close detail panel if the deleted task was being viewed
        if (selectedTaskId === taskId) {
          setSelectedTaskId(null);
        }
        // Remove from selection if selected
        setRowSelection((prev) => {
          const next = { ...prev };
          delete next[taskId];
          return next;
        });
      },
      onError: () => toast.error("Failed to delete task"),
    });
  };

  // Bulk delete handler
  const handleBulkDelete = () => {
    bulkDeleteTasks.mutate(
      { task_ids: selectedTaskIds },
      {
        onSuccess: (result) => {
          toast.success(`${result.succeeded} task(s) deleted`);
          setRowSelection({});
          setShowBulkDeleteConfirm(false);
        },
        onError: () => {
          toast.error("Failed to delete tasks");
          setShowBulkDeleteConfirm(false);
        },
      }
    );
  };

  if (!projectId) {
    return <Navigate to="/projects" replace />;
  }

  if (isError) {
    return (
      <div className="p-6">
        <QueryError
          message="Failed to load project tasks."
          onRetry={() => refetch()}
        />
      </div>
    );
  }

  return (
    <div className="space-y-6 p-6">
      {/* Header section */}
      <div className="flex items-center">
        <div>
          <h3 className="text-2xl font-medium">Tasks</h3>
          <p className="text-sm text-muted-foreground">
            Manage project tasks, subtasks, and dependencies.
          </p>
        </div>
      </div>

      {isLoading ? (
        <div className="flex justify-center p-8">
          <Loader2 className="size-8 animate-spin text-muted-foreground" />
        </div>
      ) : tasks.length === 0 && !isAddingFirstTask ? (
        <div className="flex flex-col items-center justify-center rounded-md border border-dashed p-8 text-center animate-in fade-in-50">
          <div className="mx-auto flex size-12 items-center justify-center rounded-full bg-accent">
            <ListTodo className="size-6 text-muted-foreground" />
          </div>
          <h3 className="mt-4 text-lg font-semibold">No tasks</h3>
          <p className="mb-4 mt-2 text-sm text-muted-foreground">
            You haven't added any tasks to this project yet.
          </p>
          <Button variant="outline" onClick={() => setIsAddingFirstTask(true)}>
            Add task
          </Button>
        </div>
      ) : (
        <div className="animate-in fade-in duration-200">
          <TaskTable
            projectId={projectId}
            data={tasks}
            rowSelection={rowSelection}
            setRowSelection={setRowSelection}
            forceAdding={isAddingFirstTask}
            onCancelAdding={() => setIsAddingFirstTask(false)}
            onIndent={(id) => indentTask.mutate(id, { onError: () => toast.error("Failed to indent task") })}
            onOutdent={(id) => outdentTask.mutate(id, { onError: () => toast.error("Failed to outdent task") })}
            onAddDependency={(id) => setDependencyTaskId(id)}
            onViewDetails={(id) => setSelectedTaskId(id)}
            onDelete={handleDeleteTask}
            isIndentPending={indentTask.isPending}
            isOutdentPending={outdentTask.isPending}
            isDeletePending={deleteTask.isPending}
            onReorder={(taskId, afterTaskId, beforeTaskId, sortedData) => {
              reorderTask.mutate({
                taskId,
                data: {
                  after_task_id: afterTaskId || null,
                  before_task_id: beforeTaskId || null
                },
                optimisticData: sortedData
              }, {
                onError: () => toast.error("Failed to reorder task")
              });
            }}
          />
        </div>
      )}

      {/* Floating bulk-action toolbar */}
      {selectionCount > 0 && (
        <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-50 animate-in slide-in-from-bottom-4 fade-in duration-200">
          <div className="flex items-center gap-3 rounded-xl border border-border/60 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/80 px-5 py-3 shadow-2xl">
            <span className="text-sm font-medium text-foreground/80">
              {selectionCount} selected
            </span>
            <div className="h-5 w-px bg-border/60" />
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
              {bulkDeleteTasks.isPending ? "Deleting…" : "Delete"}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Slide-out Panel for Task Core Edit */}
      <TaskDetailPanel
        projectId={projectId}
        taskId={selectedTaskId}
        isOpen={!!selectedTaskId}
        onClose={() => setSelectedTaskId(null)}
        onDelete={handleDeleteTask}
        isDeletePending={deleteTask.isPending}
      />

      {/* Add Dependency Dialog triggered from row kebab menu */}
      {dependencyTaskId && (
        <AddDependencyDialog
          projectId={projectId}
          successorTaskId={dependencyTaskId}
          isOpen={!!dependencyTaskId}
          onClose={() => setDependencyTaskId(null)}
        />
      )}
    </div>
  );
}
