import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { useAuthStore } from "@/features/auth/store/auth-store";
import { useProjectMembers } from "@/features/projects/hooks/useProjectMembers";
import {
    useComments,
    useCreateComment,
    useDeleteComment,
    useUpdateComment,
} from "@/features/tasks/hooks/useComments";
import { CommentThread } from "@/features/tasks/components/task-detail/CommentThread";

vi.mock("@/features/tasks/hooks/useComments", () => ({
    useComments: vi.fn(),
    useCreateComment: vi.fn(),
    useUpdateComment: vi.fn(),
    useDeleteComment: vi.fn(),
}));

vi.mock("@/features/projects/hooks/useProjectMembers", () => ({
    useProjectMembers: vi.fn(),
}));

describe("CommentThread", () => {
    const createMutateAsync = vi.fn().mockResolvedValue(undefined);
    const updateMutateAsync = vi.fn().mockResolvedValue(undefined);
    const deleteMutate = vi.fn();

    beforeEach(() => {
        vi.clearAllMocks();
        useAuthStore.setState({
            user: {
                id: "user-1",
                email: "user@example.com",
                full_name: "Current User",
                email_verified: true,
            },
            isAuthenticated: true,
            isInitialized: true,
        });
        vi.mocked(useProjectMembers).mockReturnValue({
            data: {
                items: [
                    {
                        id: "member-1",
                        user_id: "user-2",
                        role: "member",
                        user_full_name: "Alice Doe",
                        user_email: "alice@example.com",
                    },
                ],
            },
        } as never);
        vi.mocked(useComments).mockReturnValue({
            data: {
                data: [
                    {
                        id: "comment-1",
                        entity_type: "task",
                        entity_id: "task-1",
                        author: {
                            id: "user-2",
                            full_name: "Alice Doe",
                            avatar_url: null,
                        },
                        content:
                            "Hello @[Current%20User](user:00000000-0000-0000-0000-000000000001)",
                        mentions: ["00000000-0000-0000-0000-000000000001"],
                        parent_comment_id: null,
                        is_edited: false,
                        edited_at: null,
                        created_at: "2026-03-08T12:00:00Z",
                        replies: [],
                    },
                ],
            },
            isLoading: false,
            isError: false,
        } as never);
        vi.mocked(useCreateComment).mockReturnValue({
            mutateAsync: createMutateAsync,
            isPending: false,
        } as never);
        vi.mocked(useUpdateComment).mockReturnValue({
            mutateAsync: updateMutateAsync,
            isPending: false,
        } as never);
        vi.mocked(useDeleteComment).mockReturnValue({
            mutate: deleteMutate,
            isPending: false,
        } as never);
    });

    it("renders mention tokens as plain @display text", () => {
        render(<CommentThread projectId="project-1" taskId="task-1" canModerate={false} />);
        expect(screen.getByText("@Current User", { exact: false })).toBeInTheDocument();
    });

    it("creates a top-level comment from input", async () => {
        const user = userEvent.setup();
        render(<CommentThread projectId="project-1" taskId="task-1" canModerate={false} />);

        const inputs = screen.getAllByPlaceholderText("Write a comment...");
        await user.type(inputs[0], "A new top-level comment");
        await user.click(screen.getAllByRole("button", { name: "Comment" })[0]);

        expect(createMutateAsync).toHaveBeenCalledWith({
            content: "A new top-level comment",
            parent_comment_id: null,
        });
    });

    it("deletes a comment via fire-and-forget mutate", async () => {
        const user = userEvent.setup();
        render(<CommentThread projectId="project-1" taskId="task-1" canModerate />);

        await user.click(screen.getByRole("button", { name: "Delete" }));

        expect(deleteMutate).toHaveBeenCalledTimes(1);
        expect(deleteMutate.mock.calls[0]?.[0]).toBe("comment-1");
    });

    it("closes reply box after successful reply submit", async () => {
        const user = userEvent.setup();
        render(<CommentThread projectId="project-1" taskId="task-1" canModerate={false} />);

        await user.click(screen.getByRole("button", { name: "Reply" }));
        expect(screen.getByRole("button", { name: "Cancel" })).toBeInTheDocument();

        const inputs = screen.getAllByPlaceholderText("Write a comment...");
        await user.type(inputs[1], "Reply content");
        await user.click(screen.getAllByRole("button", { name: "Reply" })[1]);

        expect(createMutateAsync).toHaveBeenCalledWith({
            content: "Reply content",
            parent_comment_id: "comment-1",
        });
        expect(screen.queryByRole("button", { name: "Cancel" })).not.toBeInTheDocument();
    });
});
