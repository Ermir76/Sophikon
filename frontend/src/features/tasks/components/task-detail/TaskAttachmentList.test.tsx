import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach } from "vitest";

import { TaskAttachmentList } from "@/features/tasks/components/task-detail/TaskAttachmentList";
import {
  useAttachments,
  useDeleteAttachment,
  useUploadAttachment,
} from "@/features/tasks/hooks/useAttachments";

vi.mock("sonner", () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
  },
}));

vi.mock("@/features/tasks/hooks/useAttachments", () => ({
  useAttachments: vi.fn(),
  useUploadAttachment: vi.fn(),
  useDeleteAttachment: vi.fn(),
}));

const uploadMutateAsync = vi.fn();
const deleteMutateAsync = vi.fn();

describe("TaskAttachmentList", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(useUploadAttachment).mockReturnValue({
      mutateAsync: uploadMutateAsync,
      isPending: false,
    } as never);
    vi.mocked(useDeleteAttachment).mockReturnValue({
      mutateAsync: deleteMutateAsync,
      isPending: false,
    } as never);
  });

  it("renders loading state while attachments query is loading", () => {
    vi.mocked(useAttachments).mockReturnValue({
      data: undefined,
      isLoading: true,
    } as never);

    render(<TaskAttachmentList projectId="p1" taskId="t1" canManage />);
    expect(screen.getByText("Loading attachments...")).toBeInTheDocument();
  });

  it("renders attachments list and deletes selected file", async () => {
    vi.mocked(useAttachments).mockReturnValue({
      data: [
        {
          id: "att-1",
          task_id: "t1",
          uploaded_by_id: "u1",
          file_name: "spec.pdf",
          file_size: 1024,
          mime_type: "application/pdf",
          description: null,
          created_at: "2026-03-13T10:00:00Z",
          download_url: "/api/v1/projects/p1/tasks/t1/attachments/att-1/download",
        },
      ],
      isLoading: false,
    } as never);
    deleteMutateAsync.mockResolvedValue(undefined);

    render(<TaskAttachmentList projectId="p1" taskId="t1" canManage />);

    expect(screen.getByText("spec.pdf")).toBeInTheDocument();
    fireEvent.click(screen.getByLabelText("Delete spec.pdf"));

    await waitFor(() => {
      expect(deleteMutateAsync).toHaveBeenCalledWith("att-1");
    });
  });

  it("uploads selected file when manager permission is enabled", async () => {
    vi.mocked(useAttachments).mockReturnValue({
      data: [],
      isLoading: false,
    } as never);
    uploadMutateAsync.mockResolvedValue(undefined);

    const { container } = render(
      <TaskAttachmentList projectId="p1" taskId="t1" canManage />,
    );
    const fileInput = container.querySelector("input[type='file']");
    expect(fileInput).not.toBeNull();

    const file = new File(["hello"], "hello.txt", { type: "text/plain" });
    fireEvent.change(fileInput!, { target: { files: [file] } });

    await waitFor(() => {
      expect(uploadMutateAsync).toHaveBeenCalledTimes(1);
    });
    expect(uploadMutateAsync).toHaveBeenCalledWith({ file });
  });

  it("disables upload and delete actions for viewers", () => {
    vi.mocked(useAttachments).mockReturnValue({
      data: [
        {
          id: "att-1",
          task_id: "t1",
          uploaded_by_id: "u1",
          file_name: "spec.pdf",
          file_size: 1024,
          mime_type: "application/pdf",
          description: null,
          created_at: "2026-03-13T10:00:00Z",
          download_url: "/api/v1/projects/p1/tasks/t1/attachments/att-1/download",
        },
      ],
      isLoading: false,
    } as never);

    render(<TaskAttachmentList projectId="p1" taskId="t1" canManage={false} />);

    expect(screen.getByRole("button", { name: /upload/i })).toBeDisabled();
    expect(screen.getByLabelText("Delete spec.pdf")).toBeDisabled();
  });
});
