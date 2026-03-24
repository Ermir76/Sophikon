import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { toast } from "sonner";

import ProfilePage from "@/features/auth/pages/ProfilePage";

const mocks = vi.hoisted(() => ({
  updateProfileMutate: vi.fn(),
  changePasswordMutate: vi.fn(),
  uploadAvatarMutate: vi.fn(),
  deleteAvatarMutate: vi.fn(),
  updateAiPreferencesMutate: vi.fn(),
  aiPreferencesData: {
    auto_approve: {
      create_task: true,
    },
    provider: null,
    model: null,
    providers: [],
    defaults: null,
  },
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

vi.mock("sonner", () => ({
  toast: {
    error: vi.fn(),
    success: vi.fn(),
  },
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
  useAiPreferences: vi.fn(() => ({
    data: mocks.aiPreferencesData,
    isLoading: false,
    isError: false,
    error: null,
    refetch: vi.fn(),
  })),
  useUpdateAiPreferences: vi.fn(() => ({
    mutate: mocks.updateAiPreferencesMutate,
    isPending: false,
  })),
}));

describe("ProfilePage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mocks.aiPreferencesData = {
      auto_approve: {
        create_task: true,
      },
      provider: null,
      model: null,
      providers: [],
      defaults: null,
    };
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
    mocks.changePasswordMutate.mockImplementation(
      (
        _data: unknown,
        options?: { onSuccess?: () => void },
      ) => {
        options?.onSuccess?.();
      },
    );

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
    expect(toast.success).toHaveBeenCalledWith("Password changed successfully");
    expect(screen.getByLabelText("Current Password")).toHaveValue("");
    expect(screen.getByLabelText("New Password")).toHaveValue("");
    expect(screen.getByLabelText("Confirm New Password")).toHaveValue("");

    expect(screen.getByRole("link", { name: "Go to password reset" })).toHaveAttribute(
      "href",
      "/forgot-password",
    );
  });

  it("shows a success toast and updates the AI toggle state after saving preferences", async () => {
    const user = userEvent.setup();
    mocks.updateAiPreferencesMutate.mockImplementation(
      (
        _data: unknown,
        options?: {
          onSuccess?: (data: typeof mocks.aiPreferencesData) => void;
        },
      ) => {
        options?.onSuccess?.({
          ...mocks.aiPreferencesData,
          auto_approve: {
            ...mocks.aiPreferencesData.auto_approve,
            create_task: false,
          },
        });
      },
    );

    render(
      <MemoryRouter>
        <ProfilePage />
      </MemoryRouter>,
    );

    await user.click(screen.getByRole("tab", { name: "AI Settings" }));

    const createTaskSwitch = screen.getByRole("switch", { name: "Create task" });
    expect(createTaskSwitch).toBeChecked();

    await user.click(createTaskSwitch);

    await waitFor(() => {
      expect(mocks.updateAiPreferencesMutate).toHaveBeenCalledWith(
        { auto_approve: { create_task: false } },
        expect.objectContaining({
          onError: expect.any(Function),
          onSuccess: expect.any(Function),
        }),
      );
    });
    expect(toast.success).toHaveBeenCalledWith("Preferences saved");
    expect(createTaskSwitch).not.toBeChecked();
  });

  it("shows a safe avatar upload error message when the API returns validation details", async () => {
    const user = userEvent.setup();

    mocks.uploadAvatarMutate.mockImplementation(
      (_file: File, options?: { onError?: (error: unknown) => void }) => {
        options?.onError?.({
          isAxiosError: true,
          response: {
            data: {
              detail: [{ msg: "Input should be a valid image" }],
            },
          },
        });
      },
    );

    const { container } = render(
      <MemoryRouter>
        <ProfilePage />
      </MemoryRouter>,
    );

    const fileInput = container.querySelector('input[type="file"]');
    expect(fileInput).not.toBeNull();

    await user.upload(
      fileInput as HTMLInputElement,
      new File(["avatar"], "avatar.png", { type: "image/png" }),
    );

    expect(mocks.uploadAvatarMutate).toHaveBeenCalledTimes(1);
    expect(toast.error).toHaveBeenCalledWith(
      "Avatar upload failed. Please try a different image.",
    );
    expect(
      await screen.findByText("Avatar upload failed. Please try a different image."),
    ).toBeInTheDocument();
  });
});
