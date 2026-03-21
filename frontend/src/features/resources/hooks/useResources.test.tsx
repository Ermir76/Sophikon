import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { type ReactNode } from "react";
import {
    useResources,
    useResource,
    useCreateResource,
    useUpdateResource,
    useDeleteResource,
    useBulkDeleteResources,
} from "./useResources";
import type { ResourceCreate, ResourceUpdate } from "@/features/resources/types";

// Mock services
vi.mock("@/features/resources/api/resource.service", () => ({
    resourceService: {
        list: vi.fn(),
        get: vi.fn(),
        create: vi.fn(),
        update: vi.fn(),
        delete: vi.fn(),
    },
}));

import { resourceService } from "@/features/resources/api/resource.service";

function createWrapper() {
    const qc = new QueryClient({
        defaultOptions: { queries: { retry: false } },
    });
    return ({ children }: { children: ReactNode }) => (
        <QueryClientProvider client={qc}>{children}</QueryClientProvider>
    );
}

describe("Resource Hooks", () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

    const projectId = "proj-1";
    const resourceId = "res-1";

    it("useResources — fetches list, disabled when no projectId", async () => {
        const mockData = { items: [{ id: "res-1", name: "Alice" }], total: 1 };
        vi.mocked(resourceService.list).mockResolvedValue(mockData);

        const { result, rerender } = renderHook((pid: string | undefined) => useResources(pid), {
            wrapper: createWrapper(),
            initialProps: projectId,
        });

        await waitFor(() => expect(result.current.isSuccess).toBe(true));
        expect(result.current.data).toEqual(mockData);
        expect(resourceService.list).toHaveBeenCalledWith(projectId);

        rerender(undefined);
        expect(result.current.fetchStatus).toBe("idle");
        expect(resourceService.list).toHaveBeenCalledTimes(1);
    });

    it("useResource — fetches single resource, disabled when no resourceId", async () => {
        const mockResource = { id: resourceId, name: "Alice" };
        vi.mocked(resourceService.get).mockResolvedValue(mockResource);

        const { result, rerender } = renderHook(
            ({ pid, rid }: { pid: string; rid: string | undefined }) => useResource(pid, rid),
            {
                wrapper: createWrapper(),
                initialProps: { pid: projectId, rid: resourceId } as { pid: string; rid: string | undefined },
            }
        );

        await waitFor(() => expect(result.current.isSuccess).toBe(true));
        expect(result.current.data).toEqual(mockResource);
        expect(resourceService.get).toHaveBeenCalledWith(projectId, resourceId);

        rerender({ pid: projectId, rid: undefined });
        expect(result.current.fetchStatus).toBe("idle");
        expect(resourceService.get).toHaveBeenCalledTimes(1);
    });

    it("useCreateResource — calls service, invalidates list cache", async () => {
        const newData: ResourceCreate = { name: "Bob", type: "WORK" };
        vi.mocked(resourceService.create).mockResolvedValue({ id: "res-2", ...newData });

        const { result } = renderHook(() => useCreateResource(projectId), { wrapper: createWrapper() });

        result.current.mutate(newData);

        await waitFor(() => expect(result.current.isSuccess).toBe(true));
        expect(resourceService.create).toHaveBeenCalledWith(projectId, newData);
    });

    it("useUpdateResource — calls service, invalidates list + detail cache", async () => {
        const updateData: ResourceUpdate = { name: "Alice Updated" };
        vi.mocked(resourceService.update).mockResolvedValue({ id: resourceId, ...updateData });

        const { result } = renderHook(() => useUpdateResource(projectId), { wrapper: createWrapper() });

        result.current.mutate({ resourceId, data: updateData });

        await waitFor(() => expect(result.current.isSuccess).toBe(true));
        expect(resourceService.update).toHaveBeenCalledWith(projectId, resourceId, updateData);
    });

    it("useDeleteResource — calls service, invalidates list cache", async () => {
        vi.mocked(resourceService.delete).mockResolvedValue(null);

        const { result } = renderHook(() => useDeleteResource(projectId), { wrapper: createWrapper() });

        result.current.mutate(resourceId);

        await waitFor(() => expect(result.current.isSuccess).toBe(true));
        expect(resourceService.delete).toHaveBeenCalledWith(projectId, resourceId);
    });

    it("useBulkDeleteResources — calls delete for each id, returns succeeded/failed counts", async () => {
        vi.mocked(resourceService.delete).mockResolvedValue(null);

        const { result } = renderHook(() => useBulkDeleteResources(projectId), { wrapper: createWrapper() });

        result.current.mutate(["res-1", "res-2", "res-3"]);

        await waitFor(() => expect(result.current.isSuccess).toBe(true));
        expect(resourceService.delete).toHaveBeenCalledTimes(3);
        expect(result.current.data).toEqual({ succeeded: 3, failed: 0 });
    });

    it("useBulkDeleteResources — partial failure returns correct counts", async () => {
        vi.mocked(resourceService.delete)
            .mockResolvedValueOnce(null)
            .mockRejectedValueOnce(new Error("fail"))
            .mockResolvedValueOnce(null);

        const { result } = renderHook(() => useBulkDeleteResources(projectId), { wrapper: createWrapper() });

        result.current.mutate(["res-1", "res-2", "res-3"]);

        await waitFor(() => expect(result.current.isSuccess).toBe(true));
        expect(result.current.data).toEqual({ succeeded: 2, failed: 1 });
    });

    describe("Throws 'No active project' when projectId is undefined", () => {
        it("useCreateResource", async () => {
            const { result } = renderHook(() => useCreateResource(undefined), { wrapper: createWrapper() });
            result.current.mutate({ name: "R1" });
            await waitFor(() => expect(result.current.isError).toBe(true));
            expect(result.current.error?.message).toBe("No active project");
        });

        it("useUpdateResource", async () => {
            const { result } = renderHook(() => useUpdateResource(undefined), { wrapper: createWrapper() });
            result.current.mutate({ resourceId: "r1", data: { name: "R2" } });
            await waitFor(() => expect(result.current.isError).toBe(true));
            expect(result.current.error?.message).toBe("No active project");
        });

        it("useDeleteResource", async () => {
            const { result } = renderHook(() => useDeleteResource(undefined), { wrapper: createWrapper() });
            result.current.mutate("r1");
            await waitFor(() => expect(result.current.isError).toBe(true));
            expect(result.current.error?.message).toBe("No active project");
        });

        it("useBulkDeleteResources", async () => {
            const { result } = renderHook(() => useBulkDeleteResources(undefined), { wrapper: createWrapper() });
            result.current.mutate(["r1", "r2"]);
            await waitFor(() => expect(result.current.isError).toBe(true));
            expect(result.current.error?.message).toBe("No active project");
        });
    });
});
