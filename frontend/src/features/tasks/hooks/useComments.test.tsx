import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { renderHook, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { commentService } from "@/features/tasks/api/comment.service";
import {
    commentKeys,
    useComments,
    useCreateComment,
    useDeleteComment,
    useUpdateComment,
} from "@/features/tasks/hooks/useComments";

vi.mock("@/features/tasks/api/comment.service", () => ({
    commentService: {
        list: vi.fn(),
        create: vi.fn(),
        update: vi.fn(),
        delete: vi.fn(),
    },
}));

function createWrapper(queryClient: QueryClient) {
    return function Wrapper({ children }: { children: ReactNode }) {
        return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
    };
}

describe("useComments hooks", () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

    it("loads comments for entity", async () => {
        const queryClient = new QueryClient();
        vi.mocked(commentService.list).mockResolvedValue({
            data: [],
        });

        const { result } = renderHook(
            () => useComments("task", "task-1"),
            { wrapper: createWrapper(queryClient) },
        );

        await waitFor(() => {
            expect(result.current.isSuccess).toBe(true);
        });

        expect(commentService.list).toHaveBeenCalledWith("task", "task-1");
    });

    it("creates comment and invalidates entity query", async () => {
        const queryClient = new QueryClient();
        const invalidateQueries = vi.spyOn(queryClient, "invalidateQueries");
        vi.mocked(commentService.create).mockResolvedValue({} as never);

        const { result } = renderHook(
            () => useCreateComment("project-1", "task", "task-1"),
            { wrapper: createWrapper(queryClient) },
        );

        result.current.mutate({
            content: "New comment",
            parent_comment_id: null,
        });

        await waitFor(() => {
            expect(result.current.isSuccess).toBe(true);
        });

        expect(commentService.create).toHaveBeenCalledWith({
            entity_type: "task",
            entity_id: "task-1",
            content: "New comment",
            parent_comment_id: null,
        });
        expect(invalidateQueries).toHaveBeenCalledWith({
            queryKey: commentKeys.byEntity("task", "task-1"),
        });
    });

    it("updates and deletes comments", async () => {
        const queryClient = new QueryClient();
        vi.mocked(commentService.update).mockResolvedValue({} as never);
        vi.mocked(commentService.delete).mockResolvedValue(undefined);

        const { result: updateResult } = renderHook(
            () => useUpdateComment("project-1", "task", "task-1"),
            { wrapper: createWrapper(queryClient) },
        );
        updateResult.current.mutate({
            commentId: "comment-1",
            data: { content: "Updated content" },
        });
        await waitFor(() => {
            expect(updateResult.current.isSuccess).toBe(true);
        });
        expect(commentService.update).toHaveBeenCalledWith("comment-1", {
            content: "Updated content",
        });

        const { result: deleteResult } = renderHook(
            () => useDeleteComment("project-1", "task", "task-1"),
            { wrapper: createWrapper(queryClient) },
        );
        deleteResult.current.mutate("comment-1");
        await waitFor(() => {
            expect(deleteResult.current.isSuccess).toBe(true);
        });
        expect(commentService.delete).toHaveBeenCalledWith("comment-1");
    });
});
