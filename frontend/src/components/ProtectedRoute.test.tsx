import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { MemoryRouter, Route, Routes } from "react-router";
import { ProtectedRoute } from "./ProtectedRoute";
import { useAuthStore, type AuthState } from "@/store/auth-store";

// Mock the auth store
vi.mock("@/store/auth-store");

// Use the actual AuthState type to satisfy the mock signature
type StateSelector = (state: AuthState) => unknown;

describe("ProtectedRoute", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("shows loading spinner when not yet initialized", () => {
    vi.mocked(useAuthStore).mockImplementation((selector: StateSelector) => {
      const state = {
        isAuthenticated: false,
        isInitialized: false,
      } as unknown as AuthState;
      return selector(state);
    });

    render(
      <MemoryRouter>
        <ProtectedRoute />
      </MemoryRouter>,
    );

    const spinner = document.querySelector(".animate-spin");
    expect(spinner).toBeInTheDocument();
  });

  it("redirects to login when initialized but not authenticated", () => {
    vi.mocked(useAuthStore).mockImplementation((selector: StateSelector) => {
      const state = {
        isAuthenticated: false,
        isInitialized: true,
      } as unknown as AuthState;
      return selector(state);
    });

    render(
      <MemoryRouter initialEntries={["/protected"]}>
        <Routes>
          <Route path="/login" element={<div>Login Page</div>} />
          <Route element={<ProtectedRoute />}>
            <Route path="/protected" element={<div>Protected Content</div>} />
          </Route>
        </Routes>
      </MemoryRouter>,
    );

    expect(screen.getByText("Login Page")).toBeInTheDocument();
    expect(screen.queryByText("Protected Content")).not.toBeInTheDocument();
  });

  it("renders child routes when initialized and authenticated", () => {
    vi.mocked(useAuthStore).mockImplementation((selector: StateSelector) => {
      const state = {
        isAuthenticated: true,
        isInitialized: true,
      } as unknown as AuthState;
      return selector(state);
    });

    render(
      <MemoryRouter initialEntries={["/protected"]}>
        <Routes>
          <Route path="/login" element={<div>Login Page</div>} />
          <Route element={<ProtectedRoute />}>
            <Route path="/protected" element={<div>Protected Content</div>} />
          </Route>
        </Routes>
      </MemoryRouter>,
    );

    expect(screen.getByText("Protected Content")).toBeInTheDocument();
    expect(screen.queryByText("Login Page")).not.toBeInTheDocument();
  });
});
