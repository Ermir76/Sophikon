import { describe, expect, it } from "vitest";

import {
  PASSWORD_TOO_LONG_MESSAGE,
  PASSWORD_NUMBER_MESSAGE,
  PASSWORD_SPECIAL_MESSAGE,
  PASSWORD_UPPERCASE_MESSAGE,
  createPasswordSchema,
  getPasswordChecklist,
} from "@/features/auth/lib/passwordPolicy";

describe("passwordPolicy", () => {
  it("rejects passwords that miss required character classes", () => {
    expect(createPasswordSchema().safeParse("lowercase123!").error?.issues[0]?.message).toBe(
      PASSWORD_UPPERCASE_MESSAGE,
    );
    expect(createPasswordSchema().safeParse("MissingNumber!").error?.issues[0]?.message).toBe(
      PASSWORD_NUMBER_MESSAGE,
    );
    expect(createPasswordSchema().safeParse("MissingSpecial123").error?.issues[0]?.message).toBe(
      PASSWORD_SPECIAL_MESSAGE,
    );
  });

  it("rejects passwords that are too long in UTF-8 bytes", () => {
    expect(createPasswordSchema().safeParse("A".repeat(70) + "12!🙂").error?.issues[0]?.message).toBe(
      PASSWORD_TOO_LONG_MESSAGE,
    );
  });

  it("builds checklist state from the current password", () => {
    expect(getPasswordChecklist("StrongPassword123!")).toEqual([
      { label: "At least 8 characters", valid: true },
      { label: "One uppercase letter", valid: true },
      { label: "One number", valid: true },
      { label: "One special character", valid: true },
    ]);
  });
});
