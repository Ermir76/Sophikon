import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router";
import { beforeEach, describe, expect, it, vi } from "vitest";

import ResetPasswordPage from "@/features/auth/pages/ResetPasswordPage";

const mocks = vi.hoisted(() => ({
  confirmResetMutate: vi.fn(),
}));

vi.mock("@/features/auth/hooks/useAuth", () => ({
  useConfirmPasswordReset: vi.fn(() => ({
    mutate: mocks.confirmResetMutate,
    isPending: false,
    isError: false,
    error: null,
  })),
}));

describe("ResetPasswordPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("password reset confirm form handles invalid token state", () => {
    render(
      <MemoryRouter initialEntries={["/reset-password"]}>
        <Routes>
          <Route path="/reset-password" element={<ResetPasswordPage />} />
        </Routes>
      </MemoryRouter>,
    );

    expect(screen.getByRole("heading", { name: "Invalid Reset Link" })).toBeInTheDocument();
    expect(
      screen.getByText("This reset link is missing a token. Please request a new one."),
    ).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Request new reset link" })).toHaveAttribute(
      "href",
      "/forgot-password",
    );
  });

  it("prevents submit when the password is missing a number", async () => {
    const user = userEvent.setup();

    render(
      <MemoryRouter initialEntries={["/reset-password?token=test-token"]}>
        <Routes>
          <Route path="/reset-password" element={<ResetPasswordPage />} />
        </Routes>
      </MemoryRouter>,
    );

    await user.type(screen.getByLabelText("New Password"), "MissingNumber!");
    await user.type(screen.getByLabelText("Confirm Password"), "MissingNumber!");
    await user.click(screen.getByRole("button", { name: "Reset Password" }));

    await waitFor(() => {
      expect(screen.getByText("Password must contain at least one number")).toBeInTheDocument();
    });
    expect(mocks.confirmResetMutate).not.toHaveBeenCalled();
  });
});
