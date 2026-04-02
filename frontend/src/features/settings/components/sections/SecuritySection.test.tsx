import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { SecuritySection } from "@/features/settings/components/sections/SecuritySection";

const mocks = vi.hoisted(() => ({
  changePasswordMutate: vi.fn(),
}));

vi.mock("@/features/auth", () => ({
  useChangePassword: vi.fn(() => ({
    mutate: mocks.changePasswordMutate,
    isPending: false,
    isError: false,
    error: null,
  })),
}));

describe("SecuritySection", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders the shared password checklist", () => {
    render(
      <MemoryRouter>
        <SecuritySection />
      </MemoryRouter>,
    );

    expect(screen.getByText("At least 8 characters")).toBeInTheDocument();
    expect(screen.getByText("One uppercase letter")).toBeInTheDocument();
    expect(screen.getByText("One number")).toBeInTheDocument();
    expect(screen.getByText("One special character")).toBeInTheDocument();
  });

  it("prevents submit when the password is missing a special character", async () => {
    const user = userEvent.setup();

    render(
      <MemoryRouter>
        <SecuritySection />
      </MemoryRouter>,
    );

    await user.type(screen.getByLabelText("Current Password"), "StrongPassword123!");
    await user.type(screen.getByLabelText("New Password"), "MissingSpecial123");
    await user.type(screen.getByLabelText("Confirm New Password"), "MissingSpecial123");
    await user.click(screen.getByRole("button", { name: "Change Password" }));

    await waitFor(() => {
      expect(screen.getByText("Password must contain at least one special character")).toBeInTheDocument();
    });
    expect(mocks.changePasswordMutate).not.toHaveBeenCalled();
  });
});
