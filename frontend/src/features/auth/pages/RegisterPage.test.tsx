import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router";
import { beforeEach, describe, expect, it, vi } from "vitest";

import RegisterPage from "@/features/auth/pages/RegisterPage";

const mocks = vi.hoisted(() => ({
  registerMutate: vi.fn(),
}));

vi.mock("@/features/auth/hooks/useAuth", () => ({
  useRegister: vi.fn(() => ({
    mutate: mocks.registerMutate,
    isPending: false,
    isError: false,
    error: null,
  })),
}));

describe("RegisterPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("prevents submit when the password is missing an uppercase letter", async () => {
    const user = userEvent.setup();

    render(
      <MemoryRouter initialEntries={["/register"]}>
        <Routes>
          <Route path="/register" element={<RegisterPage />} />
        </Routes>
      </MemoryRouter>,
    );

    await user.type(screen.getByLabelText("Full Name"), "Weak Password User");
    await user.type(screen.getByLabelText("Email"), "register-weak@example.com");
    await user.type(screen.getByLabelText("Password"), "lowercase123!");
    await user.type(screen.getByLabelText("Confirm Password"), "lowercase123!");
    await user.click(screen.getByRole("button", { name: "Sign Up" }));

    await waitFor(() => {
      expect(screen.getByText("Password must contain at least one uppercase letter")).toBeInTheDocument();
    });
    expect(mocks.registerMutate).not.toHaveBeenCalled();
  });
});
