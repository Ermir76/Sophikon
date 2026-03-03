import type { Task } from "@/features/tasks";

/**
 * Build a map of taskId → resolved color for Gantt bar rendering.
 *
 * Resolution order per task:
 * 1. If it's a summary task with its own color → use it
 * 2. Walk up the parent chain → use nearest ancestor summary color
 * 3. Fall back to project color
 * 4. null = transparent with border (no fill)
 */
export function buildColorInheritanceMap(
  tasks: Task[],
  projectColor: string | null | undefined,
): Map<string, string | null> {
  const taskById = new Map<string, Task>();
  for (const t of tasks) {
    taskById.set(t.id, t);
  }

  const resolved = new Map<string, string | null>();

  function resolve(task: Task): string | null {
    if (resolved.has(task.id)) return resolved.get(task.id)!;

    // Summary tasks with own color
    if (task.is_summary && task.color) {
      resolved.set(task.id, task.color);
      return task.color;
    }

    // Walk up parent chain
    if (task.parent_task_id) {
      const parent = taskById.get(task.parent_task_id);
      if (parent) {
        const parentColor = resolve(parent);
        resolved.set(task.id, parentColor);
        return parentColor;
      }
    }

    // Fall back to project color
    const fallback = projectColor ?? null;
    resolved.set(task.id, fallback);
    return fallback;
  }

  for (const task of tasks) {
    resolve(task);
  }

  return resolved;
}
