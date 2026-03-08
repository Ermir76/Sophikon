import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router";
import { beforeEach, describe, expect, it, vi } from "vitest";

import LoginPage from "@/features/auth/pages/LoginPage";
import RegisterPage from "@/features/auth/pages/RegisterPage";

vi.mock("@/features/auth/hooks/useAuth", () => ({
  useLogin: vi.fn(() => ({
    isError: false,
    isPending: false,
    mutate: vi.fn(),
  })),
  useRegister: vi.fn(() => ({
    isError: false,
    isPending: false,
    mutate: vi.fn(),
  })),
}));

describe("auth redirect links", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    globalThis.ResizeObserver = class ResizeObserver {
      observe() {}
      unobserve() {}
      disconnect() {}
    };
  });

  it("preserves next when navigating from login to register", () => {
    render(
      <MemoryRouter initialEntries={["/login?next=%2Fproject-invitations%2Faccept%3Ftoken%3Dabc"]}>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
        </Routes>
      </MemoryRouter>,
    );

    expect(screen.getByRole("link", { name: "Sign up" })).toHaveAttribute(
      "href",
      "/register?next=%2Fproject-invitations%2Faccept%3Ftoken%3Dabc",
    );
  });

  it("preserves next when navigating from register to login", () => {
    render(
      <MemoryRouter initialEntries={["/register?next=%2Fproject-invitations%2Faccept%3Ftoken%3Dabc"]}>
        <Routes>
          <Route path="/register" element={<RegisterPage />} />
        </Routes>
      </MemoryRouter>,
    );

    expect(screen.getByRole("link", { name: "Sign in" })).toHaveAttribute(
      "href",
      "/login?next=%2Fproject-invitations%2Faccept%3Ftoken%3Dabc",
    );
  });
});
