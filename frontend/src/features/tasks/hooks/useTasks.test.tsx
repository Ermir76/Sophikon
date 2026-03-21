import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { type ReactNode } from "react";
import {
    useTasks,
    useTask,
    useCreateTask,
    useUpdateTask,
    useDeleteTask,
    useIndentTask,
    useOutdentTask,
    useReorderTask,
    useBulkCreateTasks,
    useBulkUpdateTasks,
    useBulkDeleteTasks
} from "./useTasks";
import type { Task } from "@/features/tasks/types";

// Mock services
vi.mock("@/features/tasks/api/task.service", () => ({
    taskService: {
        list: vi.fn(),
        get: vi.fn(),
        create: vi.fn(),
        update: vi.fn(),
        delete: vi.fn(),
        indent: vi.fn(),
        outdent: vi.fn(),
        reorder: vi.fn(),
        bulkCreate: vi.fn(),
        bulkUpdate: vi.fn(),
        bulkDelete: vi.fn(),
    },
}));

import { taskService } from "@/features/tasks/api/task.service";

function createWrapper() {
    const qc = new QueryClient({
        defaultOptions: { queries: { retry: false } },
    });
    return ({ children }: { children: ReactNode }) => (
        <QueryClientProvider client={qc}>{children}</QueryClientProvider>
    );
}

describe("Task Hooks", () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

    const projectId = "proj-1";
    const taskId = "task-1";

    it("useTasks — fetches list, disabled when no projectId", async () => {
        const mockTasks = { items: [{ id: "1", name: "Task 1" }] };
        vi.mocked(taskService.list).mockResolvedValue(mockTasks);

        const { result, rerender } = renderHook((pid: string | undefined) => useTasks(pid), {
            wrapper: createWrapper(),
            initialProps: projectId,
        });

        await waitFor(() => expect(result.current.isSuccess).toBe(true));
        expect(result.current.data).toEqual(mockTasks);
        expect(taskService.list).toHaveBeenCalledWith(projectId);

        // Fetch with undefined projectId
        rerender(undefined);
        expect(result.current.fetchStatus).toBe("idle");
        expect(taskService.list).toHaveBeenCalledTimes(1);
    });

    it("useTask — fetches single task, disabled when no taskId", async () => {
        const mockTask = { id: taskId, name: "Task 1" };
        vi.mocked(taskService.get).mockResolvedValue(mockTask);

        const { result, rerender } = renderHook(({ pid, tid }: { pid: string; tid: string | undefined }) => useTask(pid, tid), {
            wrapper: createWrapper(),
            initialProps: { pid: projectId, tid: taskId } as { pid: string; tid: string | undefined },
        });

        await waitFor(() => expect(result.current.isSuccess).toBe(true));
        expect(result.current.data).toEqual(mockTask);
        expect(taskService.get).toHaveBeenCalledWith(projectId, taskId);

        // Fetch with undefined taskId
        rerender({ pid: projectId, tid: undefined });
        expect(result.current.fetchStatus).toBe("idle");
        expect(taskService.get).toHaveBeenCalledTimes(1);
    });

    it("useCreateTask — calls service.create, invalidates list cache", async () => {
        const newTaskData = { name: "New Task", start_date: "2024-01-01", duration: 60 };
        vi.mocked(taskService.create).mockResolvedValue({ id: "new-id", ...newTaskData });

        const { result } = renderHook(() => useCreateTask(projectId), { wrapper: createWrapper() });

        result.current.mutate(newTaskData);

        await waitFor(() => expect(result.current.isSuccess).toBe(true));
        expect(taskService.create).toHaveBeenCalledWith(projectId, newTaskData);
    });

    it("useUpdateTask — calls service.update, invalidates list + detail cache", async () => {
        const updateData = { name: "Updated Task" };
        vi.mocked(taskService.update).mockResolvedValue({ id: taskId, ...updateData });

        const { result } = renderHook(() => useUpdateTask(projectId), { wrapper: createWrapper() });

        result.current.mutate({ taskId, data: updateData });

        await waitFor(() => expect(result.current.isSuccess).toBe(true));
        expect(taskService.update).toHaveBeenCalledWith(projectId, taskId, updateData);
    });

    it("useDeleteTask — calls service.delete, invalidates list cache", async () => {
        vi.mocked(taskService.delete).mockResolvedValue(null);

        const { result } = renderHook(() => useDeleteTask(projectId), { wrapper: createWrapper() });

        result.current.mutate(taskId);

        await waitFor(() => expect(result.current.isSuccess).toBe(true));
        expect(taskService.delete).toHaveBeenCalledWith(projectId, taskId);
    });

    it("useIndentTask — calls service.indent, invalidates list cache", async () => {
        vi.mocked(taskService.indent).mockResolvedValue({ id: taskId, outline_level: 2 });

        const { result } = renderHook(() => useIndentTask(projectId), { wrapper: createWrapper() });

        result.current.mutate(taskId);

        await waitFor(() => expect(result.current.isSuccess).toBe(true));
        expect(taskService.indent).toHaveBeenCalledWith(projectId, taskId);
    });

    it("useOutdentTask — calls service.outdent, invalidates list cache", async () => {
        vi.mocked(taskService.outdent).mockResolvedValue({ id: taskId, outline_level: 1 });

        const { result } = renderHook(() => useOutdentTask(projectId), { wrapper: createWrapper() });

        result.current.mutate(taskId);

        await waitFor(() => expect(result.current.isSuccess).toBe(true));
        expect(taskService.outdent).toHaveBeenCalledWith(projectId, taskId);
    });

    it("useReorderTask — optimistic update: sets cache immediately, rolls back on error", async () => {
        const reorderData = { after_task_id: "other-task" };
        const optimisticData = [{ id: "other-task" }, { id: taskId }] as unknown as Task[];

        vi.mocked(taskService.reorder).mockResolvedValue({ message: "reordered" });

        const { result } = renderHook(() => useReorderTask(projectId), { wrapper: createWrapper() });

        result.current.mutate({ taskId, data: reorderData, optimisticData });

        await waitFor(() => expect(result.current.isSuccess).toBe(true));
        expect(taskService.reorder).toHaveBeenCalledWith(projectId, taskId, reorderData);
    });

    it("useBulkCreateTasks — calls service.bulkCreate", async () => {
        const bulkData = { tasks: [{ name: "Bulk Task", start_date: "2024-01-01", duration: 60 }] };
        vi.mocked(taskService.bulkCreate).mockResolvedValue({ items: bulkData.tasks });

        const { result } = renderHook(() => useBulkCreateTasks(projectId), { wrapper: createWrapper() });

        result.current.mutate(bulkData);

        await waitFor(() => expect(result.current.isSuccess).toBe(true));
        expect(taskService.bulkCreate).toHaveBeenCalledWith(projectId, bulkData);
    });

    it("useBulkUpdateTasks — calls service.bulkUpdate", async () => {
        const bulkData = { tasks: [{ id: taskId, data: { name: "Bulk Update" } }] };
        vi.mocked(taskService.bulkUpdate).mockResolvedValue({ items: bulkData.tasks });

        const { result } = renderHook(() => useBulkUpdateTasks(projectId), { wrapper: createWrapper() });

        result.current.mutate(bulkData);

        await waitFor(() => expect(result.current.isSuccess).toBe(true));
        expect(taskService.bulkUpdate).toHaveBeenCalledWith(projectId, bulkData);
    });

    it("useBulkDeleteTasks — calls service.bulkDelete", async () => {
        const bulkData = { task_ids: [taskId] };
        vi.mocked(taskService.bulkDelete).mockResolvedValue(null);

        const { result } = renderHook(() => useBulkDeleteTasks(projectId), { wrapper: createWrapper() });

        result.current.mutate(bulkData);

        await waitFor(() => expect(result.current.isSuccess).toBe(true));
        expect(taskService.bulkDelete).toHaveBeenCalledWith(projectId, bulkData);
    });

    describe("All mutations throw 'No active project' when projectId is undefined", () => {
        it("useCreateTask", async () => {
            const { result } = renderHook(() => useCreateTask(undefined), { wrapper: createWrapper() });
            result.current.mutate({ name: "T1", start_date: "2024", duration: 0 });
            await waitFor(() => expect(result.current.isError).toBe(true));
            expect(result.current.error?.message).toBe("No active project");
        });

        it("useUpdateTask", async () => {
            const { result } = renderHook(() => useUpdateTask(undefined), { wrapper: createWrapper() });
            result.current.mutate({ taskId: "t1", data: { name: "T2" } });
            await waitFor(() => expect(result.current.isError).toBe(true));
            expect(result.current.error?.message).toBe("No active project");
        });

        it("useDeleteTask", async () => {
            const { result } = renderHook(() => useDeleteTask(undefined), { wrapper: createWrapper() });
            result.current.mutate("t1");
            await waitFor(() => expect(result.current.isError).toBe(true));
            expect(result.current.error?.message).toBe("No active project");
        });

        it("useIndentTask", async () => {
            const { result } = renderHook(() => useIndentTask(undefined), { wrapper: createWrapper() });
            result.current.mutate("t1");
            await waitFor(() => expect(result.current.isError).toBe(true));
            expect(result.current.error?.message).toBe("No active project");
        });

        it("useOutdentTask", async () => {
            const { result } = renderHook(() => useOutdentTask(undefined), { wrapper: createWrapper() });
            result.current.mutate("t1");
            await waitFor(() => expect(result.current.isError).toBe(true));
            expect(result.current.error?.message).toBe("No active project");
        });

        it("useReorderTask", async () => {
            const { result } = renderHook(() => useReorderTask(undefined), { wrapper: createWrapper() });
            result.current.mutate({ taskId: "t1", data: { after_task_id: "t2" } });
            await waitFor(() => expect(result.current.isError).toBe(true));
            expect(result.current.error?.message).toBe("No active project");
        });

        it("useBulkCreateTasks", async () => {
            const { result } = renderHook(() => useBulkCreateTasks(undefined), { wrapper: createWrapper() });
            result.current.mutate({ tasks: [{ name: "T1", start_date: "2024", duration: 0 }] });
            await waitFor(() => expect(result.current.isError).toBe(true));
            expect(result.current.error?.message).toBe("No active project");
        });

        it("useBulkUpdateTasks", async () => {
            const { result } = renderHook(() => useBulkUpdateTasks(undefined), { wrapper: createWrapper() });
            result.current.mutate({ tasks: [{ id: "t1", data: { name: "T2" } }] });
            await waitFor(() => expect(result.current.isError).toBe(true));
            expect(result.current.error?.message).toBe("No active project");
        });

        it("useBulkDeleteTasks", async () => {
            const { result } = renderHook(() => useBulkDeleteTasks(undefined), { wrapper: createWrapper() });
            result.current.mutate({ task_ids: ["t1"] });
            await waitFor(() => expect(result.current.isError).toBe(true));
            expect(result.current.error?.message).toBe("No active project");
        });
    });
});
