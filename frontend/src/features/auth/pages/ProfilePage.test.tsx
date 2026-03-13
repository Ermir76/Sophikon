import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router";
import { beforeEach, describe, expect, it, vi } from "vitest";

import ProfilePage from "@/features/auth/pages/ProfilePage";

const mocks = vi.hoisted(() => ({
  updateProfileMutate: vi.fn(),
  changePasswordMutate: vi.fn(),
  uploadAvatarMutate: vi.fn(),
  deleteAvatarMutate: vi.fn(),
  authState: {
    user: {
      id: "u1",
      email: "profile@example.com",
      full_name: "Profile User",
      email_verified: true,
      timezone: "UTC",
      locale: "en-US",
      preferences: {},
      avatar_url: null,
    },
  },
}));

vi.mock("@/features/auth/store/auth-store", () => ({
  useAuthStore: vi.fn((selector: (state: unknown) => unknown) =>
    selector(mocks.authState)),
}));

vi.mock("@/features/auth/hooks/useAuth", () => ({
  useUpdateProfile: vi.fn(() => ({
    mutate: mocks.updateProfileMutate,
    isPending: false,
    isError: false,
    isSuccess: false,
    error: null,
  })),
  useChangePassword: vi.fn(() => ({
    mutate: mocks.changePasswordMutate,
    isPending: false,
    isError: false,
    isSuccess: false,
    error: null,
  })),
  useUploadAvatar: vi.fn(() => ({
    mutate: mocks.uploadAvatarMutate,
    isPending: false,
    isError: false,
    error: null,
  })),
  useDeleteAvatar: vi.fn(() => ({
    mutate: mocks.deleteAvatarMutate,
    isPending: false,
    isError: false,
    error: null,
  })),
}));

describe("ProfilePage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    globalThis.ResizeObserver = class ResizeObserver {
      observe() {}
      unobserve() {}
      disconnect() {}
    };
  });

  it("renders profile/security tabs and submits profile patch", async () => {
    const user = userEvent.setup();

    render(
      <MemoryRouter>
        <ProfilePage />
      </MemoryRouter>,
    );

    expect(screen.getByRole("tab", { name: "Profile" })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: "Security" })).toBeInTheDocument();

    const fullNameInput = screen.getByLabelText("Full Name");
    await user.clear(fullNameInput);
    await user.type(fullNameInput, "Updated Name");
    await user.click(screen.getByRole("button", { name: "Save Changes" }));

    await waitFor(() => {
      expect(mocks.updateProfileMutate).toHaveBeenCalledWith({
        full_name: "Updated Name",
      });
    });
  });

  it("submits change-password form and keeps recovery route visible", async () => {
    const user = userEvent.setup();

    render(
      <MemoryRouter>
        <ProfilePage />
      </MemoryRouter>,
    );

    await user.click(screen.getByRole("tab", { name: "Security" }));

    await user.type(screen.getByLabelText("Current Password"), "StrongPassword123!");
    await user.type(screen.getByLabelText("New Password"), "StrongPassword456!");
    await user.type(screen.getByLabelText("Confirm New Password"), "StrongPassword456!");
    await user.click(screen.getByRole("button", { name: "Change Password" }));

    await waitFor(() => {
      expect(mocks.changePasswordMutate).toHaveBeenCalled();
    });
    expect(mocks.changePasswordMutate.mock.calls[0]?.[0]).toEqual({
      current_password: "StrongPassword123!",
      new_password: "StrongPassword456!",
    });

    expect(screen.getByRole("link", { name: "Go to password reset" })).toHaveAttribute(
      "href",
      "/forgot-password",
    );
  });
});
