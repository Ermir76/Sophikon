import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { NotificationsSection } from "@/features/settings/components/sections/NotificationsSection";

const mocks = vi.hoisted(() => ({
  mutate: vi.fn(),
}));

vi.mock("sonner", () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
  },
}));

vi.mock("@/features/notifications", () => ({
  useNotificationSettings: vi.fn(() => ({
    data: {
      email_task_assigned: true,
      email_mentioned: false,
      email_deadline_approaching: true,
      push_enabled: true,
    },
    isLoading: false,
    isError: false,
    error: null,
    refetch: vi.fn(),
  })),
  useUpdateNotificationSettings: vi.fn(() => ({
    mutate: mocks.mutate,
    isPending: false,
  })),
}));

vi.mock("@/shared/ui/switch", () => ({
  Switch: ({
    id,
    checked,
    onCheckedChange,
    disabled,
  }: {
    id: string;
    checked: boolean;
    onCheckedChange: (value: boolean) => void;
    disabled?: boolean;
  }) => (
    <button
      type="button"
      role="switch"
      id={id}
      aria-checked={checked}
      disabled={disabled}
      onClick={() => onCheckedChange(!checked)}
    />
  ),
}));

describe("NotificationsSection", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("updates notification settings when a toggle changes", async () => {
    const user = userEvent.setup();

    render(<NotificationsSection />);

    await user.click(screen.getByRole("switch", { name: "Mentions" }));

    expect(mocks.mutate).toHaveBeenCalledWith(
      { email_mentioned: true },
      expect.objectContaining({
        onError: expect.any(Function),
        onSuccess: expect.any(Function),
      }),
    );
  });
});
