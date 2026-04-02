import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router";
import { beforeEach, describe, expect, it, vi } from "vitest";

import LoginPage from "@/features/auth/pages/LoginPage";

const mocks = vi.hoisted(() => ({
  loginMutate: vi.fn(),
  startGoogleOAuth: vi.fn(),
  resendVerificationEmail: vi.fn(),
  consumeBlockedUnverifiedEmail: vi.fn(() => null),
  loginState: {
    mutate: vi.fn(),
    isPending: false,
    isError: false,
    error: null,
  },
}));

vi.mock("@/features/auth/hooks/useAuth", () => ({
  useLogin: vi.fn(() => mocks.loginState),
}));

vi.mock("@/features/auth/api/auth.service", () => ({
  authService: {
    startGoogleOAuth: mocks.startGoogleOAuth,
    resendVerificationEmail: mocks.resendVerificationEmail,
  },
}));

vi.mock("@/shared/api/api", () => ({
  consumeBlockedUnverifiedEmail: mocks.consumeBlockedUnverifiedEmail,
}));

describe("LoginPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mocks.loginState = {
      mutate: mocks.loginMutate,
      isPending: false,
      isError: false,
      error: null,
    };
    globalThis.ResizeObserver = class ResizeObserver {
      observe() {}
      unobserve() {}
      disconnect() {}
    };
  });

  it("builds forgot-password link with preserved next param", () => {
    render(
      <MemoryRouter initialEntries={["/login?next=%2Fprojects%2F123"]}>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
        </Routes>
      </MemoryRouter>,
    );

    expect(screen.getByRole("link", { name: "Forgot password?" })).toHaveAttribute(
      "href",
      "/forgot-password?next=%2Fprojects%2F123",
    );
  });

  it("starts Google OAuth from CTA with current next path", async () => {
    const user = userEvent.setup();

    render(
      <MemoryRouter initialEntries={["/login?next=%2Fprojects%2Fabc%3Ftab%3Dtasks"]}>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
        </Routes>
      </MemoryRouter>,
    );

    await user.click(screen.getByRole("button", { name: "Google" }));

    expect(mocks.startGoogleOAuth).toHaveBeenCalledWith("/projects/abc?tab=tasks");
  });

  it("submits remember_me when keep me logged in is checked", async () => {
    const user = userEvent.setup();

    render(
      <MemoryRouter initialEntries={["/login"]}>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
        </Routes>
      </MemoryRouter>,
    );

    await user.type(screen.getByLabelText("Email Address"), "user@example.com");
    await user.type(screen.getByPlaceholderText("********"), "StrongPassword123!");
    await user.click(screen.getByRole("checkbox", { name: "Keep me logged in" }));
    await user.click(screen.getByRole("button", { name: "Sign In" }));

    expect(mocks.loginMutate).toHaveBeenCalledWith({
      email: "user@example.com",
      password: "StrongPassword123!",
      remember_me: true,
    });
  });

  it("shows blocked verification recovery and resends using the public endpoint", async () => {
    const user = userEvent.setup();
    mocks.loginState.isError = true;
    mocks.loginState.error = {
      response: {
        data: {
          error: {
            code: "EMAIL_VERIFICATION_REQUIRED",
            message: "Email verification expired.",
          },
        },
      },
    };

    render(
      <MemoryRouter initialEntries={["/login"]}>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
        </Routes>
      </MemoryRouter>,
    );

    await user.type(screen.getByLabelText("Email Address"), "blocked@example.com");
    await user.click(screen.getByRole("button", { name: "Resend Verification Email" }));

    expect(mocks.resendVerificationEmail).toHaveBeenCalledWith({
      email: "blocked@example.com",
    });
  });

  it("hydrates blocked verification recovery from stored email", () => {
    mocks.consumeBlockedUnverifiedEmail.mockReturnValue("stored@example.com");

    render(
      <MemoryRouter initialEntries={["/login"]}>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
        </Routes>
      </MemoryRouter>,
    );

    expect(screen.getByDisplayValue("stored@example.com")).toBeInTheDocument();
    expect(
      screen.getByText("Your email verification window expired. Request a new verification email to continue."),
    ).toBeInTheDocument();
  });
});
