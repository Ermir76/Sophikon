import { type ChangeEvent, useRef } from "react";
import { Download, Loader2, Trash2, Upload } from "lucide-react";
import { format } from "date-fns";
import { toast } from "sonner";

import { Button } from "@/shared/ui/button";
import { Input } from "@/shared/ui/input";
import { useAttachments, useDeleteAttachment, useUploadAttachment } from "@/features/tasks/hooks/useAttachments";

interface TaskAttachmentListProps {
  projectId: string;
  taskId: string;
  canManage: boolean;
}

function formatBytes(size: number): string {
  if (size < 1024) return `${size} B`;
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`;
  return `${(size / (1024 * 1024)).toFixed(1)} MB`;
}

export function TaskAttachmentList({ projectId, taskId, canManage }: TaskAttachmentListProps) {
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const attachmentsQuery = useAttachments(projectId, taskId);
  const uploadAttachment = useUploadAttachment(projectId, taskId);
  const deleteAttachment = useDeleteAttachment(projectId, taskId);

  const attachments = attachmentsQuery.data ?? [];

  const handlePickFile = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = async (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;
    try {
      await uploadAttachment.mutateAsync({ file });
      toast.success("Attachment uploaded");
    } catch {
      toast.error("Failed to upload attachment");
    } finally {
      event.target.value = "";
    }
  };

  const handleDelete = async (attachmentId: string) => {
    try {
      await deleteAttachment.mutateAsync(attachmentId);
      toast.success("Attachment deleted");
    } catch {
      toast.error("Failed to delete attachment");
    }
  };

  if (attachmentsQuery.isLoading) {
    return (
      <div className="flex items-center gap-2 px-4 py-3 text-sm text-muted-foreground">
        <Loader2 className="size-4 animate-spin" />
        Loading attachments...
      </div>
    );
  }

  return (
    <div className="space-y-3 p-4">
      <div className="flex items-center justify-between gap-2">
        <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
          Files
        </p>
        <div className="flex items-center gap-2">
          <Input
            ref={fileInputRef}
            type="file"
            className="hidden"
            onChange={handleFileChange}
          />
          <Button
            type="button"
            variant="outline"
            size="sm"
            className="h-8 text-xs"
            disabled={!canManage || uploadAttachment.isPending}
            onClick={handlePickFile}
          >
            {uploadAttachment.isPending ? (
              <Loader2 className="mr-1 size-3.5 animate-spin" />
            ) : (
              <Upload className="mr-1 size-3.5" />
            )}
            Upload
          </Button>
        </div>
      </div>

      {attachments.length === 0 ? (
        <p className="rounded-md border border-dashed px-3 py-2 text-sm text-muted-foreground">
          No attachments yet.
        </p>
      ) : (
        <div className="space-y-2">
          {attachments.map((attachment) => (
            <div
              key={attachment.id}
              className="flex items-center justify-between gap-3 rounded-md border px-3 py-2"
            >
              <div className="min-w-0">
                <p className="truncate text-sm font-medium">{attachment.file_name}</p>
                <p className="text-xs text-muted-foreground">
                  {formatBytes(attachment.file_size)} - {format(new Date(attachment.created_at), "yyyy-MM-dd HH:mm")}
                </p>
              </div>
              <div className="flex items-center gap-1">
                <Button
                  asChild
                  type="button"
                  size="icon"
                  variant="ghost"
                  className="size-8"
                >
                  <a
                    href={attachment.download_url}
                    target="_blank"
                    rel="noreferrer"
                    aria-label={`Download ${attachment.file_name}`}
                  >
                    <Download className="size-4" />
                  </a>
                </Button>
                <Button
                  type="button"
                  size="icon"
                  variant="ghost"
                  className="size-8 text-destructive"
                  disabled={!canManage || deleteAttachment.isPending}
                  onClick={() => handleDelete(attachment.id)}
                  aria-label={`Delete ${attachment.file_name}`}
                >
                  <Trash2 className="size-4" />
                </Button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
