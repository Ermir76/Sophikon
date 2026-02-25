import { useState, useEffect } from "react";
import { useParams, Navigate } from "react-router";
import { Loader2, ListTodo } from "lucide-react";
import type { RowSelectionState } from "@tanstack/react-table";
import { Button } from "@/shared/ui/button";
import { QueryError } from "@/shared/components/QueryError";
import { useTasks } from "@/features/tasks/hooks/useTasks";
import { TaskTable } from "@/features/tasks/components/TaskTable";
import { TaskDetailPanel } from "@/features/tasks/components/TaskDetailPanel";
import type { Task } from "@/features/tasks/types";

const EMPTY_TASKS: Task[] = [];

export default function TasksPage() {
  const { id: projectId } = useParams<{ id: string }>();

  // Local state for table row selection
  const [rowSelection, setRowSelection] = useState<RowSelectionState>({});

  // Detail panel state
  const [selectedTaskId, setSelectedTaskId] = useState<string | null>(null);

  // Local state to override empty view and show the table with the inline row
  const [isAddingFirstTask, setIsAddingFirstTask] = useState(false);

  // Fetch task data
  const { data, isLoading, isError, refetch } = useTasks(projectId);

  // Ensure data structure safely maps out items array
  const tasks = data?.items ?? EMPTY_TASKS;

  // Reset the "adding first task" state if tasks are successfully loaded from the backend
  useEffect(() => {
    if (tasks.length > 0 && isAddingFirstTask) {
      setIsAddingFirstTask(false);
    }
  }, [tasks.length, isAddingFirstTask]);

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
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-2xl font-medium">Tasks</h3>
          <p className="text-sm text-muted-foreground">
            Manage project tasks, subtasks, and dependencies.
          </p>
        </div>

        {/* Placeholder for toolbar actions */}
        <div className="flex items-center gap-2">
          {/* We will add Add/Indent/Outdent buttons here in future phases */}
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
            onRowClick={(id: string) => setSelectedTaskId(id)}
          />
        </div>
      )}

      {/* Slide-out Panel for Task Core Edit */}
      <TaskDetailPanel
        projectId={projectId}
        taskId={selectedTaskId}
        isOpen={!!selectedTaskId}
        onClose={() => setSelectedTaskId(null)}
      />
    </div>
  );
}
