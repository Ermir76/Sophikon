import { describe, it, expect, vi, beforeEach } from "vitest";
import { act, render, waitFor } from "@testing-library/react";
import { BrowserRouter } from "react-router";
import { QueryClientProvider, QueryClient } from "@tanstack/react-query";
import { ThemeProvider } from "next-themes";
import App from "./App";
import { authService } from "@/features/auth/api/auth.service";
import { useAuthStore } from "@/features/auth";

// Mock the actual module that checkSession dynamically imports
vi.mock("@/features/auth/api/auth.service", () => ({
  authService: {
    me: vi.fn(),
    login: vi.fn(),
    register: vi.fn(),
    refresh: vi.fn(),
  },
}));

vi.mock("@/shared/api/api", () => ({
  API_BASE: "/api/v1",
  api: {
    get: vi.fn(),
    post: vi.fn(),
    patch: vi.fn(),
    delete: vi.fn(),
    interceptors: {
      request: { use: vi.fn(), eject: vi.fn() },
      response: { use: vi.fn(), eject: vi.fn() },
    },
  },
}));

function renderApp() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <ThemeProvider attribute="class" defaultTheme="system">
          <App />
        </ThemeProvider>
      </BrowserRouter>
    </QueryClientProvider>,
  );
}

describe("App", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    class MockWebSocket {
      addEventListener = vi.fn();
      close = vi.fn();

      constructor(public readonly url: string) {}
    }

    vi.stubGlobal("WebSocket", MockWebSocket);
    useAuthStore.setState({
      user: null,
      isAuthenticated: false,
      isInitialized: false,
    });
    localStorage.clear();
  });

  it("calls checkSession on mount to verify auth state", async () => {
    (authService.me as ReturnType<typeof vi.fn>).mockRejectedValue(
      new Error("Unauthorized"),
    );

    renderApp();

    await waitFor(() => {
      expect(authService.me).toHaveBeenCalledTimes(1);
    });
  });

  it("refreshes the session proactively while authenticated", async () => {
    const user = {
      id: "1",
      email: "test@example.com",
      full_name: "Test User",
      email_verified: true,
    };
    let refreshTimerCallback: TimerHandler | undefined;

    (authService.me as ReturnType<typeof vi.fn>).mockResolvedValue(user);
    (authService.refresh as ReturnType<typeof vi.fn>).mockResolvedValue({ user });
    vi.spyOn(window, "setInterval").mockImplementation(((callback) => {
      refreshTimerCallback = callback;
      return 1;
    }) as typeof window.setInterval);
    vi.spyOn(window, "clearInterval").mockImplementation(() => {});

    renderApp();

    await waitFor(() => {
      expect(authService.me).toHaveBeenCalledTimes(1);
      expect(useAuthStore.getState().isAuthenticated).toBe(true);
      expect(refreshTimerCallback).toBeDefined();
    });

    await act(async () => {
      (refreshTimerCallback as () => void)();
    });

    await waitFor(() => {
      expect(authService.refresh).toHaveBeenCalledTimes(1);
    });
  });
});
