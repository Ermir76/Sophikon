import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router";
import { beforeEach, describe, expect, it, vi } from "vitest";

import VerifyEmailPage from "@/features/auth/pages/VerifyEmailPage";

const mocks = vi.hoisted(() => ({
  resendMutate: vi.fn(),
  resendState: {
    mutate: vi.fn(),
    isPending: false,
    isSuccess: false,
    isError: false,
    error: null,
  },
  authState: {
    checkSession: vi.fn(),
    isAuthenticated: false,
  },
}));

vi.mock("@/features/auth/hooks/useAuth", () => ({
  useSendVerificationEmail: vi.fn(() => mocks.resendState),
}));

vi.mock("@/features/auth/store/auth-store", () => ({
  useAuthStore: vi.fn((selector) => selector(mocks.authState)),
}));

describe("VerifyEmailPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mocks.resendState = {
      mutate: mocks.resendMutate,
      isPending: false,
      isSuccess: false,
      isError: false,
      error: null,
    };
    mocks.authState = {
      checkSession: vi.fn(),
      isAuthenticated: false,
    };
  });

  it("shows login recovery CTA for guests on invalid links", () => {
    render(
      <MemoryRouter initialEntries={["/verify-email"]}>
        <Routes>
          <Route path="/verify-email" element={<VerifyEmailPage />} />
        </Routes>
      </MemoryRouter>,
    );

    expect(screen.getByRole("heading", { name: "Invalid Link" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Go to Login" })).toHaveAttribute(
      "href",
      "/login",
    );
  });

  it("submits resend verification for authenticated users", async () => {
    const user = userEvent.setup();
    mocks.authState.isAuthenticated = true;

    render(
      <MemoryRouter initialEntries={["/verify-email?status=error"]}>
        <Routes>
          <Route path="/verify-email" element={<VerifyEmailPage />} />
        </Routes>
      </MemoryRouter>,
    );

    await user.click(screen.getByRole("button", { name: "Resend Verification Email" }));

    expect(mocks.resendMutate).toHaveBeenCalledTimes(1);
  });

  it("renders resend failure feedback for authenticated users", () => {
    mocks.authState.isAuthenticated = true;
    mocks.resendState.isError = true;
    mocks.resendState.error = {
      isAxiosError: true,
      response: {
        data: {
          error: {
            message: "Too many resend attempts. Try again later.",
          },
        },
      },
    };

    render(
      <MemoryRouter initialEntries={["/verify-email?status=error"]}>
        <Routes>
          <Route path="/verify-email" element={<VerifyEmailPage />} />
        </Routes>
      </MemoryRouter>,
    );

    expect(
      screen.getByText("Too many resend attempts. Try again later."),
    ).toBeInTheDocument();
  });
});
