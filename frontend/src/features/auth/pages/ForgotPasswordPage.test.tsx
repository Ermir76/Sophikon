import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router";
import { beforeEach, describe, expect, it, vi } from "vitest";

import ForgotPasswordPage from "@/features/auth/pages/ForgotPasswordPage";

const mocks = vi.hoisted(() => ({
  requestResetMutate: vi.fn(),
}));

vi.mock("@/features/auth/hooks/useAuth", () => ({
  useRequestPasswordReset: vi.fn(() => ({
    mutate: mocks.requestResetMutate,
    isPending: false,
    isError: false,
    error: null,
  })),
}));

describe("ForgotPasswordPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mocks.requestResetMutate.mockImplementation((_payload, options) => {
      options?.onSuccess?.({
        message: "If the email exists, reset instructions were sent.",
      });
    });
  });

  it("password reset request form submit and success message", async () => {
    const user = userEvent.setup();
    render(
      <MemoryRouter initialEntries={["/forgot-password?next=%2Fprojects%2F123"]}>
        <Routes>
          <Route path="/forgot-password" element={<ForgotPasswordPage />} />
        </Routes>
      </MemoryRouter>,
    );

    await user.type(screen.getByLabelText("Email Address"), "reset@example.com");
    await user.click(screen.getByRole("button", { name: "Send Reset Link" }));

    await waitFor(() => {
      expect(mocks.requestResetMutate).toHaveBeenCalledWith(
        { email: "reset@example.com" },
        expect.any(Object),
      );
    });
    expect(
      screen.getByText("If the email exists, reset instructions were sent."),
    ).toBeInTheDocument();
  });
});
