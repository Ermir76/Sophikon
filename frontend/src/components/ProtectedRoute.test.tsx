import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { MemoryRouter, Route, Routes } from "react-router";
import { ProtectedRoute } from "./ProtectedRoute";
import { useAuthStore } from "@/store/auth-store";

// Mock the auth store
vi.mock("@/store/auth-store");

describe("ProtectedRoute", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("shows loading spinner when not yet initialized", () => {
    // @ts-ignore
    useAuthStore.mockReturnValueOnce(false); // isInitialized
    // @ts-ignore
    useAuthStore.mockReturnValueOnce(false); // isAuthenticated (doesn't matter here)

    // Actually, useAuthStore is a hook selector.
    // The implementation of ProtectedRoute uses it twice:
    // const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
    // const isInitialized = useAuthStore((state) => state.isInitialized);

    // We need to mock the implementation of useAuthStore to handle selector
    vi.mocked(useAuthStore).mockImplementation((selector: any) => {
      const state = {
        isAuthenticated: false,
        isInitialized: false,
      };
      return selector(state);
    });

    render(
      <MemoryRouter>
        <ProtectedRoute />
      </MemoryRouter>,
    );

    // Look for the spinner (it has specific classes)
    // Or just check that Outlet is not rendered and Navigate is not rendered
    // The spinner div has "animate-spin" class
    const spinner = document.querySelector(".animate-spin");
    expect(spinner).toBeInTheDocument();
  });

  it("redirects to login when initialized but not authenticated", () => {
    vi.mocked(useAuthStore).mockImplementation((selector: any) => {
      const state = {
        isAuthenticated: false,
        isInitialized: true,
      };
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
    vi.mocked(useAuthStore).mockImplementation((selector: any) => {
      const state = {
        isAuthenticated: true,
        isInitialized: true,
      };
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
