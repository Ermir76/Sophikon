import { useEffect, useRef, useState } from "react";
import { toast } from "sonner";

import { useProjectMembers } from "@/features/projects/hooks/useProjectMembers";
import {
    buildMentionToken,
    getMentionQueryMatch,
} from "@/features/tasks/lib/comment-mentions";
import { getErrorMessage } from "@/shared/lib/errors";
import { Button } from "@/shared/ui/button";
import { Textarea } from "@/shared/ui/textarea";

interface CommentInputProps {
    projectId: string;
    onSubmit: (content: string) => Promise<void> | void;
    placeholder?: string;
    submitLabel?: string;
    initialValue?: string;
    isSubmitting?: boolean;
    onCancel?: () => void;
    clearOnSubmit?: boolean;
}

export function CommentInput({
    projectId,
    onSubmit,
    placeholder = "Write a comment...",
    submitLabel = "Comment",
    initialValue = "",
    isSubmitting = false,
    onCancel,
    clearOnSubmit = true,
}: CommentInputProps) {
    const textareaRef = useRef<HTMLTextAreaElement | null>(null);
    const [value, setValue] = useState(initialValue);
    const [cursorPosition, setCursorPosition] = useState(initialValue.length);
    const membersQuery = useProjectMembers(projectId);

    useEffect(() => {
        setValue(initialValue);
        setCursorPosition(initialValue.length);
    }, [initialValue]);

    const mentionMatch = getMentionQueryMatch(value, cursorPosition);
    const members = membersQuery.data?.items ?? [];
    const filteredMembers = mentionMatch
        ? members
            .filter((member) => {
                const name = (member.user_full_name ?? "").toLowerCase();
                const email = (member.user_email ?? "").toLowerCase();
                const query = mentionMatch.query.toLowerCase();
                return name.includes(query) || email.includes(query);
            })
            .slice(0, 6)
        : [];

    async function handleSubmit() {
        const content = value.trim();
        if (!content || isSubmitting) {
            return;
        }
        try {
            await onSubmit(content);
            if (clearOnSubmit) {
                setValue("");
                setCursorPosition(0);
            }
        } catch (error) {
            toast.error("Failed to submit comment", {
                description: getErrorMessage(error),
            });
        }
    }

    function handleMentionClick(memberId: string, label: string) {
        if (!mentionMatch) {
            return;
        }
        const token = `${buildMentionToken(label, memberId)} `;
        const nextValue =
            `${value.slice(0, mentionMatch.start)}${token}${value.slice(mentionMatch.end)}`;
        const nextCursor = mentionMatch.start + token.length;
        setValue(nextValue);
        setCursorPosition(nextCursor);
        requestAnimationFrame(() => {
            textareaRef.current?.focus();
            textareaRef.current?.setSelectionRange(nextCursor, nextCursor);
        });
    }

    return (
        <div className="space-y-2">
            <div className="relative">
                <Textarea
                    ref={textareaRef}
                    value={value}
                    placeholder={placeholder}
                    rows={3}
                    onChange={(event) => {
                        setValue(event.target.value);
                        setCursorPosition(event.target.selectionStart ?? event.target.value.length);
                    }}
                    onSelect={(event) => {
                        const target = event.target as HTMLTextAreaElement;
                        setCursorPosition(target.selectionStart ?? target.value.length);
                    }}
                />
                {mentionMatch && filteredMembers.length > 0 ? (
                    <div className="absolute left-0 right-0 top-full z-20 mt-1 rounded-md border bg-background shadow-md">
                        {filteredMembers.map((member) => (
                            <button
                                key={member.id}
                                type="button"
                                className="flex w-full items-center justify-between px-3 py-2 text-left text-sm hover:bg-muted"
                                onMouseDown={(event) => {
                                    event.preventDefault();
                                    handleMentionClick(
                                        member.user_id,
                                        member.user_full_name ?? member.user_email ?? "User",
                                    );
                                }}
                            >
                                <span>{member.user_full_name ?? "Unnamed user"}</span>
                                <span className="text-xs text-muted-foreground">{member.user_email}</span>
                            </button>
                        ))}
                    </div>
                ) : null}
            </div>
            <div className="flex justify-end gap-2">
                {onCancel ? (
                    <Button type="button" variant="outline" onClick={onCancel}>
                        Cancel
                    </Button>
                ) : null}
                <Button
                    type="button"
                    onClick={handleSubmit}
                    disabled={isSubmitting || !value.trim()}
                >
                    {submitLabel}
                </Button>
            </div>
        </div>
    );
}
