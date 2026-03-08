import { render } from "@testing-library/react";
import type { ReactNode } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { useAuthStore } from "@/features/auth/store/auth-store";
import { useProjectMembers } from "@/features/projects/hooks/useProjectMembers";
import { TaskDetailPanel } from "@/features/tasks/components/task-detail/TaskDetailPanel";
import { useTask, useUpdateTask } from "@/features/tasks/hooks/useTasks";

const mockCommentThread = vi.fn(() => <div data-testid="comment-thread" />);

vi.mock("@/features/tasks/hooks/useTasks", () => ({
    useTask: vi.fn(),
    useUpdateTask: vi.fn(),
}));

vi.mock("@/features/projects/hooks/useProjectMembers", () => ({
    useProjectMembers: vi.fn(),
}));

vi.mock("@/features/auth/store/auth-store", () => ({
    useAuthStore: vi.fn(),
}));

vi.mock("@/features/tasks/components/task-detail/TaskDependencyList", () => ({
    TaskDependencyList: () => <div />,
}));

vi.mock("@/features/tasks/components/task-detail/TaskAssignmentList", () => ({
    TaskAssignmentList: () => <div />,
}));

vi.mock("@/features/tasks/components/task-detail/TaskDetailCoreFields", () => ({
    TaskDetailCoreFields: () => <div />,
}));

vi.mock("@/features/tasks/components/task-detail/CommentThread", () => ({
    CommentThread: (props: unknown) => mockCommentThread(props),
}));

vi.mock("@/shared/ui/sheet", () => ({
    Sheet: ({ children }: { children: ReactNode }) => <div>{children}</div>,
    SheetContent: ({ children }: { children: ReactNode }) => <div>{children}</div>,
    SheetHeader: ({ children }: { children: ReactNode }) => <div>{children}</div>,
    SheetTitle: ({ children }: { children: ReactNode }) => <div>{children}</div>,
    SheetDescription: ({ children }: { children: ReactNode }) => <div>{children}</div>,
}));

vi.mock("@/shared/ui/alert-dialog", () => ({
    AlertDialog: ({ children }: { children: ReactNode }) => <div>{children}</div>,
    AlertDialogAction: ({ children }: { children: ReactNode }) => <button type="button">{children}</button>,
    AlertDialogCancel: ({ children }: { children: ReactNode }) => <button type="button">{children}</button>,
    AlertDialogContent: ({ children }: { children: ReactNode }) => <div>{children}</div>,
    AlertDialogDescription: ({ children }: { children: ReactNode }) => <div>{children}</div>,
    AlertDialogFooter: ({ children }: { children: ReactNode }) => <div>{children}</div>,
    AlertDialogHeader: ({ children }: { children: ReactNode }) => <div>{children}</div>,
    AlertDialogTitle: ({ children }: { children: ReactNode }) => <div>{children}</div>,
}));

const baseTask = {
    id: "task-1",
    project_id: "project-1",
    name: "Task One",
    notes: "",
    start_date: "2026-03-08",
    finish_date: "2026-03-09",
    duration: 480,
    actual_duration: 0,
    remaining_duration: 480,
    work: 480,
    percent_complete: 0,
    percent_work_complete: 0,
    parent_task_id: undefined,
    wbs_code: "1",
    outline_level: 1,
    order_index: 1,
    sort_order: 1,
    is_summary: false,
    is_milestone: false,
    is_critical: false,
    effort_driven: true,
    priority: 500,
    constraint_type: "ASAP",
    constraint_date: undefined,
    deadline: undefined,
    task_type: "FIXED_UNITS",
    actual_start: undefined,
    actual_finish: undefined,
    actual_cost: 0,
    total_cost: 0,
    fixed_cost: 0,
    total_slack: 0,
    free_slack: 0,
    color: null,
    comments_count: 0,
    created_at: "2026-03-08T00:00:00Z",
    updated_at: "2026-03-08T00:00:00Z",
};

describe("TaskDetailPanel", () => {
    beforeEach(() => {
        vi.clearAllMocks();
        vi.mocked(useTask).mockReturnValue({
            data: baseTask,
            isLoading: false,
        } as never);
        vi.mocked(useUpdateTask).mockReturnValue({
            mutateAsync: vi.fn().mockResolvedValue(undefined),
            isPending: false,
        } as never);
        vi.mocked(useAuthStore).mockImplementation((selector: (state: any) => any) =>
            selector({ user: { id: "user-1" } }));
    });

    it("passes canModerate=true when current user is owner/manager", () => {
        vi.mocked(useProjectMembers).mockReturnValue({
            data: {
                items: [
                    { id: "m1", user_id: "user-1", role: "manager" },
                ],
            },
        } as never);

        render(
            <TaskDetailPanel
                projectId="project-1"
                taskId="task-1"
                isOpen
                onClose={vi.fn()}
            />,
        );

        const [props] = mockCommentThread.mock.calls.at(-1) ?? [];
        expect(props).toMatchObject({
            projectId: "project-1",
            taskId: "task-1",
            canModerate: true,
        });
    });

    it("passes canModerate=false for non-moderator roles", () => {
        vi.mocked(useProjectMembers).mockReturnValue({
            data: {
                items: [
                    { id: "m1", user_id: "user-1", role: "member" },
                ],
            },
        } as never);

        render(
            <TaskDetailPanel
                projectId="project-1"
                taskId="task-1"
                isOpen
                onClose={vi.fn()}
            />,
        );

        const [props] = mockCommentThread.mock.calls.at(-1) ?? [];
        expect(props).toMatchObject({
            canModerate: false,
        });
    });
});
