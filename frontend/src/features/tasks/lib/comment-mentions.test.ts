import { describe, expect, it } from "vitest";

import {
    buildMentionToken,
    formatCommentContentForDisplay,
    getMentionQueryMatch,
    MENTION_TOKEN_REGEX,
} from "@/features/tasks/lib/comment-mentions";

describe("comment mention helpers", () => {
    it("builds and parses an ID-backed mention token", () => {
        const token = buildMentionToken("Jane Doe", "00000000-0000-0000-0000-000000000001");
        expect(token).toBe("@[Jane%20Doe](user:00000000-0000-0000-0000-000000000001)");
        expect(token.match(MENTION_TOKEN_REGEX)).not.toBeNull();
    });

    it("formats mention tokens for plain display", () => {
        const content = "Hi @[Jane%20Doe](user:00000000-0000-0000-0000-000000000001)";
        expect(formatCommentContentForDisplay(content)).toBe("Hi @Jane Doe");
    });

    it("returns mention query match near cursor", () => {
        const content = "Please review @jan";
        const match = getMentionQueryMatch(content, content.length);
        expect(match).toEqual({
            start: 14,
            end: 18,
            query: "jan",
        });
    });

    it("returns null when cursor is not on a mention query", () => {
        const content = "Hello team";
        expect(getMentionQueryMatch(content, content.length)).toBeNull();
    });
});
