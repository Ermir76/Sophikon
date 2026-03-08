import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { toast } from "sonner";

import { useProjectMembers } from "@/features/projects/hooks/useProjectMembers";
import { CommentInput } from "@/features/tasks/components/task-detail/CommentInput";

vi.mock("@/features/projects/hooks/useProjectMembers", () => ({
    useProjectMembers: vi.fn(),
}));

vi.mock("sonner", () => ({
    toast: {
        error: vi.fn(),
    },
}));

describe("CommentInput", () => {
    beforeEach(() => {
        vi.clearAllMocks();
        vi.mocked(useProjectMembers).mockReturnValue({
            data: {
                items: [
                    {
                        id: "member-1",
                        user_id: "user-1",
                        role: "member",
                        user_full_name: "Alice Doe",
                        user_email: "alice@example.com",
                    },
                ],
            },
        } as never);
    });

    it("inserts ID-backed mention token from autocomplete", async () => {
        const user = userEvent.setup();
        const onSubmit = vi.fn().mockResolvedValue(undefined);
        render(
            <CommentInput
                projectId="project-1"
                onSubmit={onSubmit}
            />,
        );

        await user.type(screen.getByPlaceholderText("Write a comment..."), "Hi @Ali");
        await user.click(screen.getByRole("button", { name: /Alice Doe/i }));
        await user.click(screen.getByRole("button", { name: "Comment" }));

        expect(onSubmit).toHaveBeenCalledWith("Hi @[Alice%20Doe](user:user-1)");
    });

    it("shows submit error and keeps input text when submit fails", async () => {
        const user = userEvent.setup();
        const onSubmit = vi.fn().mockRejectedValue(new Error("submit failed"));
        render(
            <CommentInput
                projectId="project-1"
                onSubmit={onSubmit}
            />,
        );

        const input = screen.getByPlaceholderText("Write a comment...");
        await user.type(input, "This should stay");
        await user.click(screen.getByRole("button", { name: "Comment" }));

        expect(onSubmit).toHaveBeenCalledWith("This should stay");
        expect((input as HTMLTextAreaElement).value).toBe("This should stay");
        expect(toast.error).toHaveBeenCalledTimes(1);
    });
});
