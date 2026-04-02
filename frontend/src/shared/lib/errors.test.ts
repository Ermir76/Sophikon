import { describe, expect, it } from "vitest";

import { getErrorMessage } from "@/shared/lib/errors";

describe("getErrorMessage", () => {
  it("maps the backend password byte-limit message to friendly copy", () => {
    expect(
      getErrorMessage({
        isAxiosError: true,
        response: {
          data: {
            error: {
              message: "Password must be at most 72 bytes",
            },
          },
        },
      }),
    ).toBe("Password is too long. Please use a shorter password.");
  });
});
