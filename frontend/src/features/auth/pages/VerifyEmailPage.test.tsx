import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router";
import { beforeEach, describe, expect, it, vi } from "vitest";

import VerifyEmailPage from "@/features/auth/pages/VerifyEmailPage";

const mocks = vi.hoisted(() => ({
  resendMutate: vi.fn(),
  resendState: {
    mutate: vi.fn(),
    reset: vi.fn(),
    isPending: false,
    isSuccess: false,
    isError: false,
    error: null,
  },
  authState: {
    checkSession: vi.fn(),
    user: null,
  },
}));

vi.mock("@/features/auth/hooks/useAuth", () => ({
  useResendVerificationEmail: vi.fn(() => mocks.resendState),
}));

vi.mock("@/features/auth/store/auth-store", () => ({
  useAuthStore: vi.fn((selector) => selector(mocks.authState)),
}));

describe("VerifyEmailPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mocks.resendState = {
      mutate: mocks.resendMutate,
      reset: vi.fn(),
      isPending: false,
      isSuccess: false,
      isError: false,
      error: null,
    };
    mocks.authState = {
      checkSession: vi.fn(),
      user: null,
    };
  });

  it("shows public resend recovery for invalid links", () => {
    render(
      <MemoryRouter initialEntries={["/verify-email"]}>
        <Routes>
          <Route path="/verify-email" element={<VerifyEmailPage />} />
        </Routes>
      </MemoryRouter>,
    );

    expect(screen.getByRole("heading", { name: "Invalid Link" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Resend Verification Email" })).toBeInTheDocument();
  });

  it("submits public resend verification with entered email", async () => {
    const user = userEvent.setup();

    render(
      <MemoryRouter initialEntries={["/verify-email?status=error"]}>
        <Routes>
          <Route path="/verify-email" element={<VerifyEmailPage />} />
        </Routes>
      </MemoryRouter>,
    );

    await user.type(screen.getByPlaceholderText("name@example.com"), "recover@example.com");
    await user.click(screen.getByRole("button", { name: "Resend Verification Email" }));

    expect(mocks.resendMutate).toHaveBeenCalledWith({ email: "recover@example.com" });
  });

  it("prefills the email from auth state when available", () => {
    mocks.authState.user = { email: "member@example.com" };

    render(
      <MemoryRouter initialEntries={["/verify-email?status=error"]}>
        <Routes>
          <Route path="/verify-email" element={<VerifyEmailPage />} />
        </Routes>
      </MemoryRouter>,
    );

    expect(screen.getByDisplayValue("member@example.com")).toBeInTheDocument();
  });

  it("renders resend failure feedback", () => {
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
