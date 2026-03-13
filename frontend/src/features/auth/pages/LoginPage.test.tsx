import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router";
import { beforeEach, describe, expect, it, vi } from "vitest";

import LoginPage from "@/features/auth/pages/LoginPage";

const mocks = vi.hoisted(() => ({
  loginMutate: vi.fn(),
  startGoogleOAuth: vi.fn(),
}));

vi.mock("@/features/auth/hooks/useAuth", () => ({
  useLogin: vi.fn(() => ({
    mutate: mocks.loginMutate,
    isPending: false,
    isError: false,
    error: null,
  })),
}));

vi.mock("@/features/auth/api/auth.service", () => ({
  authService: {
    startGoogleOAuth: mocks.startGoogleOAuth,
  },
}));

describe("LoginPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
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
});
