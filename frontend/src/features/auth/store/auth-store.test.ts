import { describe, it, expect, vi, beforeEach } from "vitest";
import { useAuthStore } from "./auth-store";
import * as authLib from "@/features/auth/lib/auth";

// Mock dependencies
vi.mock("@/shared/api/api", () => ({
  api: {
    post: vi.fn(),
  },
}));

vi.mock("@/features/auth/api/auth.service", () => ({
  authService: {
    me: vi.fn(),
  },
}));

vi.mock("@/features/auth/lib/auth", async (importOriginal) => {
  const actual = await importOriginal<typeof authLib>();
  return {
    ...actual,
    getUser: vi.fn(),
    saveAuth: vi.fn(),
    clearAuth: vi.fn(),
  };
});

describe("Auth Store", () => {
  beforeEach(() => {
    useAuthStore.setState({
      user: null,
      isAuthenticated: false,
      isInitialized: false,
    });
    vi.clearAllMocks();
  });

  it("login updates state and saves to localStorage", () => {
    const mockUser = {
      id: "1",
      email: "test@example.com",
      full_name: "Test User",
      email_verified: true,
    };
    const { login } = useAuthStore.getState();

    login(mockUser);

    const state = useAuthStore.getState();
    expect(state.user).toEqual(mockUser);
    expect(state.isAuthenticated).toBe(true);
    expect(state.isInitialized).toBe(true);
    expect(authLib.saveAuth).toHaveBeenCalledWith(mockUser);
  });

  it("logout clears state, localStorage, and calls backend", async () => {
    const { logout } = useAuthStore.getState();
    const { api } = await import("@/shared/api/api");

    await logout();

    const state = useAuthStore.getState();
    expect(state.user).toBeNull();
    expect(state.isAuthenticated).toBe(false);
    expect(state.isInitialized).toBe(true);
    expect(authLib.clearAuth).toHaveBeenCalled();
    expect(api.post).toHaveBeenCalledWith("/auth/logout");
  });

  it("checkSession success updates state", async () => {
    const mockUser = {
      id: "1",
      email: "test@example.com",
      full_name: "Test User",
      email_verified: true,
    };
    const { authService } = await import("@/features/auth/api/auth.service");
    vi.mocked(authService.me).mockResolvedValue(mockUser);

    const { checkSession } = useAuthStore.getState();
    await checkSession();

    const state = useAuthStore.getState();
    expect(state.user).toEqual(mockUser);
    expect(state.isAuthenticated).toBe(true);
    expect(state.isInitialized).toBe(true);
    expect(authLib.saveAuth).toHaveBeenCalledWith(mockUser);
  });

  it("checkSession failure clears state", async () => {
    const { authService } = await import("@/features/auth/api/auth.service");
    vi.mocked(authService.me).mockRejectedValue(new Error("Unauthorized"));

    const { checkSession } = useAuthStore.getState();
    await checkSession();

    const state = useAuthStore.getState();
    expect(state.user).toBeNull();
    expect(state.isAuthenticated).toBe(false);
    expect(state.isInitialized).toBe(true);
    expect(authLib.clearAuth).toHaveBeenCalled();
  });
});
