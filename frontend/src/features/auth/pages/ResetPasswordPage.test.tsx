import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router";
import { describe, expect, it, vi } from "vitest";

import ResetPasswordPage from "@/features/auth/pages/ResetPasswordPage";

vi.mock("@/features/auth/hooks/useAuth", () => ({
  useConfirmPasswordReset: vi.fn(() => ({
    mutate: vi.fn(),
    isPending: false,
    isError: false,
    error: null,
  })),
}));

describe("ResetPasswordPage", () => {
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
});
