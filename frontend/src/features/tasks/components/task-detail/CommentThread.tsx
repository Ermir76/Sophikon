import { formatDistanceToNow } from "date-fns";
import { useState } from "react";
import { toast } from "sonner";

import { useAuthStore } from "@/features/auth/store/auth-store";
import {
    useComments,
    useCreateComment,
    useDeleteComment,
    useUpdateComment,
} from "@/features/tasks/hooks/useComments";
import { formatCommentContentForDisplay } from "@/features/tasks/lib/comment-mentions";
import type { TaskComment } from "@/features/tasks/types";
import { getErrorMessage } from "@/shared/lib/errors";
import { Button } from "@/shared/ui/button";
import { Card } from "@/shared/ui/card";

import { CommentInput } from "./CommentInput";

interface CommentThreadProps {
    projectId: string;
    taskId: string;
    canModerate: boolean;
}

export function CommentThread({ projectId, taskId, canModerate }: CommentThreadProps) {
    const currentUserId = useAuthStore((state) => state.user?.id ?? null);
    const commentsQuery = useComments("task", taskId);
    const createComment = useCreateComment(projectId, "task", taskId);
    const updateComment = useUpdateComment(projectId, "task", taskId);
    const deleteComment = useDeleteComment(projectId, "task", taskId);

    const [replyingToId, setReplyingToId] = useState<string | null>(null);
    const [editingCommentId, setEditingCommentId] = useState<string | null>(null);
    const [editingContent, setEditingContent] = useState("");

    async function handleCreate(content: string, parentCommentId?: string | null) {
        await createComment.mutateAsync({
            content,
            parent_comment_id: parentCommentId ?? null,
        });
    }

    async function handleSaveEdit(commentId: string, content: string) {
        await updateComment.mutateAsync({
            commentId,
            data: { content },
        });
        setEditingCommentId(null);
        setEditingContent("");
    }

    function renderComment(comment: TaskComment, depth = 0) {
        const canEditOrDelete = canModerate || comment.author.id === currentUserId;
        const isEditing = editingCommentId === comment.id;
        const isReplying = replyingToId === comment.id;

        return (
            <li key={comment.id} className="space-y-2">
                <Card className="p-3">
                    <div className="flex items-start justify-between gap-2">
                        <div className="text-sm">
                            <span className="font-semibold">
                                {comment.author.full_name ?? "Unknown user"}
                            </span>
                            <span className="ml-2 text-xs text-muted-foreground">
                                {formatDistanceToNow(new Date(comment.created_at), { addSuffix: true })}
                            </span>
                            {comment.is_edited ? (
                                <span className="ml-2 text-xs text-muted-foreground">(edited)</span>
                            ) : null}
                        </div>
                        {canEditOrDelete ? (
                            <div className="flex gap-1">
                                <Button
                                    type="button"
                                    size="sm"
                                    variant="ghost"
                                    onClick={() => {
                                        setEditingCommentId(comment.id);
                                        setEditingContent(comment.content);
                                        setReplyingToId(null);
                                    }}
                                >
                                    Edit
                                </Button>
                                <Button
                                    type="button"
                                    size="sm"
                                    variant="ghost"
                                    onClick={() => {
                                        deleteComment.mutate(comment.id, {
                                            onError: (error) => {
                                                toast.error("Failed to delete comment", {
                                                    description: getErrorMessage(error),
                                                });
                                            },
                                        });
                                    }}
                                >
                                    Delete
                                </Button>
                            </div>
                        ) : null}
                    </div>

                    {isEditing ? (
                        <div className="mt-2">
                            <CommentInput
                                projectId={projectId}
                                initialValue={editingContent}
                                clearOnSubmit={false}
                                submitLabel="Save"
                                isSubmitting={updateComment.isPending}
                                onSubmit={(content) => handleSaveEdit(comment.id, content)}
                                onCancel={() => {
                                    setEditingCommentId(null);
                                    setEditingContent("");
                                }}
                            />
                        </div>
                    ) : (
                        <p className="mt-2 whitespace-pre-wrap text-sm">
                            {formatCommentContentForDisplay(comment.content)}
                        </p>
                    )}

                    <div className="mt-2">
                        <Button
                            type="button"
                            size="sm"
                            variant="ghost"
                            onClick={() => {
                                setReplyingToId((current) => (current === comment.id ? null : comment.id));
                                setEditingCommentId(null);
                            }}
                        >
                            Reply
                        </Button>
                    </div>

                    {isReplying ? (
                        <div className="mt-2">
                            <CommentInput
                                projectId={projectId}
                                submitLabel="Reply"
                                isSubmitting={createComment.isPending}
                                onSubmit={async (content) => {
                                    await handleCreate(content, comment.id);
                                    setReplyingToId(null);
                                }}
                                onCancel={() => setReplyingToId(null)}
                            />
                        </div>
                    ) : null}
                </Card>

                {comment.replies.length > 0 ? (
                    <ul className="space-y-2" style={{ marginLeft: `${Math.min(depth + 1, 4) * 16}px` }}>
                        {comment.replies.map((reply) => renderComment(reply, depth + 1))}
                    </ul>
                ) : null}
            </li>
        );
    }

    return (
        <section className="space-y-3">
            <h3 className="text-sm font-semibold uppercase tracking-wide text-muted-foreground">Comments</h3>

            <CommentInput
                projectId={projectId}
                isSubmitting={createComment.isPending}
                onSubmit={(content) => handleCreate(content)}
            />

            {commentsQuery.isLoading ? (
                <p className="text-sm text-muted-foreground">Loading comments...</p>
            ) : commentsQuery.isError ? (
                <p className="text-sm text-muted-foreground">{getErrorMessage(commentsQuery.error)}</p>
            ) : commentsQuery.data?.data.length ? (
                <ul className="space-y-2">
                    {commentsQuery.data.data.map((comment) => renderComment(comment))}
                </ul>
            ) : (
                <p className="text-sm text-muted-foreground">No comments yet.</p>
            )}
        </section>
    );
}
