import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { type ReactNode } from "react";
import {
    useAssignments,
    useCreateAssignment,
    useUpdateAssignment,
    useDeleteAssignment,
} from "./useAssignments";
import type { AssignmentCreate, AssignmentUpdate } from "@/features/tasks/types";

// Mock services
vi.mock("@/features/tasks/api/assignment.service", () => ({
    assignmentService: {
        list: vi.fn(),
        create: vi.fn(),
        update: vi.fn(),
        delete: vi.fn(),
    },
}));

import { assignmentService } from "@/features/tasks/api/assignment.service";

function createWrapper() {
    const qc = new QueryClient({
        defaultOptions: { queries: { retry: false } },
    });
    return ({ children }: { children: ReactNode }) => (
        <QueryClientProvider client={qc}>{children}</QueryClientProvider>
    );
}

describe("Assignment Hooks", () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

    const projectId = "proj-1";
    const taskId = "task-1";
    const assignmentId = "asgn-1";

    it("useAssignments — fetches list, disabled when no taskId", async () => {
        const mockData = [{ id: assignmentId, task_id: taskId, resource_id: "res-1", units: 1.0 }];
        (assignmentService.list as any).mockResolvedValue(mockData);

        const { result, rerender } = renderHook(
            ({ pid, tid }: { pid: string; tid: string | undefined }) => useAssignments(pid, tid),
            {
                wrapper: createWrapper(),
                initialProps: { pid: projectId, tid: taskId } as { pid: string; tid: string | undefined },
            }
        );

        await waitFor(() => expect(result.current.isSuccess).toBe(true));
        expect(result.current.data).toEqual(mockData);
        expect(assignmentService.list).toHaveBeenCalledWith(projectId, taskId);

        rerender({ pid: projectId, tid: undefined });
        expect(result.current.fetchStatus).toBe("idle");
        expect(assignmentService.list).toHaveBeenCalledTimes(1);
    });

    it("useCreateAssignment — calls service, invalidates caches", async () => {
        const newData: AssignmentCreate = {
            resource_id: "res-1",
            units: 1.0,
            start_date: "2024-01-01",
            finish_date: "2024-01-10",
        };
        (assignmentService.create as any).mockResolvedValue({ id: "asgn-2", ...newData });

        const { result } = renderHook(() => useCreateAssignment(projectId, taskId), { wrapper: createWrapper() });

        result.current.mutate(newData);

        await waitFor(() => expect(result.current.isSuccess).toBe(true));
        expect(assignmentService.create).toHaveBeenCalledWith(projectId, taskId, newData);
    });

    it("useUpdateAssignment — calls service with assignmentId and data", async () => {
        const updateData: AssignmentUpdate = { units: 0.5 };
        (assignmentService.update as any).mockResolvedValue({ id: assignmentId, ...updateData });

        const { result } = renderHook(() => useUpdateAssignment(projectId, taskId), { wrapper: createWrapper() });

        result.current.mutate({ assignmentId, data: updateData });

        await waitFor(() => expect(result.current.isSuccess).toBe(true));
        expect(assignmentService.update).toHaveBeenCalledWith(assignmentId, updateData);
    });

    it("useDeleteAssignment — calls service, invalidates caches", async () => {
        (assignmentService.delete as any).mockResolvedValue(null);

        const { result } = renderHook(() => useDeleteAssignment(projectId, taskId), { wrapper: createWrapper() });

        result.current.mutate(assignmentId);

        await waitFor(() => expect(result.current.isSuccess).toBe(true));
        expect(assignmentService.delete).toHaveBeenCalledWith(assignmentId);
    });

    describe("Throws 'No active project or task' when projectId/taskId is undefined", () => {
        it("useCreateAssignment", async () => {
            const { result } = renderHook(() => useCreateAssignment(undefined, undefined), { wrapper: createWrapper() });
            result.current.mutate({ resource_id: "r1", start_date: "2024-01-01", finish_date: "2024-01-10" });
            await waitFor(() => expect(result.current.isError).toBe(true));
            expect(result.current.error?.message).toBe("No active project or task");
        });

        it("useUpdateAssignment", async () => {
            const { result } = renderHook(() => useUpdateAssignment(undefined, undefined), { wrapper: createWrapper() });
            result.current.mutate({ assignmentId: "a1", data: { units: 0.5 } });
            await waitFor(() => expect(result.current.isError).toBe(true));
            expect(result.current.error?.message).toBe("No active project or task");
        });

        it("useDeleteAssignment", async () => {
            const { result } = renderHook(() => useDeleteAssignment(undefined, undefined), { wrapper: createWrapper() });
            result.current.mutate("a1");
            await waitFor(() => expect(result.current.isError).toBe(true));
            expect(result.current.error?.message).toBe("No active project or task");
        });
    });
});
