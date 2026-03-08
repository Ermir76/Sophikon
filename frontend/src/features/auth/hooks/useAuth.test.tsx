import { act, renderHook } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import type { ReactNode } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { useLogin, useRegister } from "@/features/auth/hooks/useAuth";

const navigateMock = vi.fn();
const loginStoreMock = vi.fn();

vi.mock("react-router", async () => {
  const actual = await vi.importActual<typeof import("react-router")>("react-router");
  return {
    ...actual,
    useNavigate: () => navigateMock,
  };
});

vi.mock("@/features/auth/api/auth.service", () => ({
  authService: {
    login: vi.fn(),
    register: vi.fn(),
  },
}));

vi.mock("@/features/auth/store/auth-store", () => ({
  useAuthStore: vi.fn((selector) => selector({ login: loginStoreMock })),
}));

import { authService } from "@/features/auth/api/auth.service";

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { mutations: { retry: false } },
  });

  return ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
}

describe("auth hooks", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("navigates to next path after successful login", async () => {
    vi.mocked(authService.login).mockResolvedValue({
      user: { id: "u1", email: "user@example.com" },
      access_token: "a",
      refresh_token: "r",
    } as never);

    const { result } = renderHook(() => useLogin("/project-invitations/accept?token=abc"), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      await result.current.mutateAsync({
        email: "user@example.com",
        password: "StrongPassword123!",
      });
    });

    expect(loginStoreMock).toHaveBeenCalledWith({ id: "u1", email: "user@example.com" });
    expect(navigateMock).toHaveBeenCalledWith(
      "/project-invitations/accept?token=abc",
      { replace: true },
    );
  });

  it("falls back to root for unsafe redirect targets", async () => {
    vi.mocked(authService.login).mockResolvedValue({
      user: { id: "u2", email: "user2@example.com" },
      access_token: "a",
      refresh_token: "r",
    } as never);

    const { result } = renderHook(() => useLogin("https://bad.example.com"), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      await result.current.mutateAsync({
        email: "user2@example.com",
        password: "StrongPassword123!",
      });
    });

    expect(navigateMock).toHaveBeenCalledWith("/", { replace: true });
  });

  it("navigates to next path after successful registration", async () => {
    vi.mocked(authService.register).mockResolvedValue({
      user: { id: "u3", email: "new@example.com" },
    } as never);

    const { result } = renderHook(
      () => useRegister("/project-invitations/accept?token=abc"),
      { wrapper: createWrapper() },
    );

    await act(async () => {
      await result.current.mutateAsync({
        email: "new@example.com",
        password: "StrongPassword123!",
        full_name: "New User",
      });
    });

    expect(loginStoreMock).toHaveBeenCalledWith({ id: "u3", email: "new@example.com" });
    expect(navigateMock).toHaveBeenCalledWith(
      "/project-invitations/accept?token=abc",
      { replace: true },
    );
  });
});
