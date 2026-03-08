const UUID_PATTERN =
    "[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}";

export const MENTION_TOKEN_REGEX = new RegExp(
    `@\\[(?<label>[^\\]]+)\\]\\(user:(?<userId>${UUID_PATTERN})\\)`,
    "g",
);

export interface MentionQueryMatch {
    start: number;
    end: number;
    query: string;
}

function decodeMentionLabel(label: string) {
    try {
        return decodeURIComponent(label);
    } catch {
        return label;
    }
}

export function buildMentionToken(label: string, userId: string) {
    return `@[${encodeURIComponent(label)}](user:${userId})`;
}

export function formatCommentContentForDisplay(content: string) {
    return content.replace(
        MENTION_TOKEN_REGEX,
        (_match, label: string) => `@${decodeMentionLabel(label)}`,
    );
}

export function getMentionQueryMatch(content: string, cursor: number): MentionQueryMatch | null {
    const beforeCursor = content.slice(0, cursor);
    const match = /(^|\s)@([^\s@]*)$/.exec(beforeCursor);
    if (!match) {
        return null;
    }
    const query = match[2] ?? "";
    const end = cursor;
    const start = cursor - query.length - 1;
    return { start, end, query };
}
