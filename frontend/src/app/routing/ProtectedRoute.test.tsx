import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes, useLocation } from "react-router";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ProtectedRoute } from "@/app/routing/ProtectedRoute";

vi.mock("@/features/auth", () => ({
  useAuthStore: vi.fn(),
}));

import { useAuthStore } from "@/features/auth";

function LoginLocation() {
  const location = useLocation();
  return <div>{`${location.pathname}${location.search}`}</div>;
}

describe("ProtectedRoute", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("redirects unauthenticated users to login with next", () => {
    vi.mocked(useAuthStore).mockImplementation(
      ((selector: (state: unknown) => unknown) =>
        selector({ isAuthenticated: false, isInitialized: true } as never)) as never,
    );

    render(
      <MemoryRouter initialEntries={["/project-invitations/accept?token=abc"]}>
        <Routes>
          <Route path="/login" element={<LoginLocation />} />
          <Route element={<ProtectedRoute />}>
            <Route path="/project-invitations/accept" element={<div>Protected</div>} />
          </Route>
        </Routes>
      </MemoryRouter>,
    );

    expect(
      screen.getByText("/login?next=%2Fproject-invitations%2Faccept%3Ftoken%3Dabc"),
    ).toBeInTheDocument();
  });
});
