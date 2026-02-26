import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { type ReactNode } from "react";
import { useDependencies, useCreateDependency, useDeleteDependency } from "./useDependencies";
import type { DependencyCreate } from "@/features/tasks/types";

// Mock services
vi.mock("@/features/tasks/api/dependency.service", () => ({
    dependencyService: {
        list: vi.fn(),
        create: vi.fn(),
        delete: vi.fn(),
    },
}));

import { dependencyService } from "@/features/tasks/api/dependency.service";

function createWrapper() {
    const qc = new QueryClient({
        defaultOptions: { queries: { retry: false } },
    });
    return ({ children }: { children: ReactNode }) => (
        <QueryClientProvider client={qc}>{children}</QueryClientProvider>
    );
}

describe("Dependency Hooks", () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

    const projectId = "proj-1";

    it("useDependencies — fetches list, disabled when no projectId", async () => {
        const mockDeps = { items: [{ id: "dep-1", predecessor_id: "t1", successor_id: "t2", type: "FS" }] };
        (dependencyService.list as any).mockResolvedValue(mockDeps);

        const { result, rerender } = renderHook((pid: string | undefined) => useDependencies(pid), {
            wrapper: createWrapper(),
            initialProps: projectId,
        });

        await waitFor(() => expect(result.current.isSuccess).toBe(true));
        expect(result.current.data).toEqual(mockDeps);
        expect(dependencyService.list).toHaveBeenCalledWith(projectId);

        // Fetch with undefined projectId
        rerender(undefined);
        expect(result.current.fetchStatus).toBe("idle");
        expect(dependencyService.list).toHaveBeenCalledTimes(1);
    });

    it("useCreateDependency — calls service, invalidates dependency list + task list", async () => {
        const newDepData: DependencyCreate = { predecessor_id: "t1", successor_id: "t2", type: "FS" };
        (dependencyService.create as any).mockResolvedValue({ id: "new-dep-id", ...newDepData });

        const { result } = renderHook(() => useCreateDependency(projectId), { wrapper: createWrapper() });

        result.current.mutate(newDepData);

        await waitFor(() => expect(result.current.isSuccess).toBe(true));
        expect(dependencyService.create).toHaveBeenCalledWith(projectId, newDepData);
    });

    it("useDeleteDependency — calls service, invalidates dependency list + task list", async () => {
        (dependencyService.delete as any).mockResolvedValue(null);

        const { result } = renderHook(() => useDeleteDependency(projectId), { wrapper: createWrapper() });

        result.current.mutate("dep-1");

        await waitFor(() => expect(result.current.isSuccess).toBe(true));
        expect(dependencyService.delete).toHaveBeenCalledWith(projectId, "dep-1");
    });

    describe("Throws 'No active project' when projectId is undefined", () => {
        it("useCreateDependency", async () => {
            const { result } = renderHook(() => useCreateDependency(undefined), { wrapper: createWrapper() });
            const newDepData: DependencyCreate = { predecessor_id: "t1", successor_id: "t2", type: "FS" };
            result.current.mutate(newDepData);
            await waitFor(() => expect(result.current.isError).toBe(true));
            expect(result.current.error?.message).toBe("No active project");
        });

        it("useDeleteDependency", async () => {
            const { result } = renderHook(() => useDeleteDependency(undefined), { wrapper: createWrapper() });
            result.current.mutate("dep-1");
            await waitFor(() => expect(result.current.isError).toBe(true));
            expect(result.current.error?.message).toBe("No active project");
        });
    });
});
