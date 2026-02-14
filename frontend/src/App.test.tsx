import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, waitFor } from "@testing-library/react";
import { BrowserRouter } from "react-router";
import { QueryClientProvider, QueryClient } from "@tanstack/react-query";
import { ThemeProvider } from "next-themes";
import App from "./App";
import { authService } from "@/services/auth";

// Mock the services that the store calls
vi.mock("@/services/auth", () => ({
  authService: {
    me: vi.fn(),
    login: vi.fn(),
    register: vi.fn(),
    refresh: vi.fn(),
  },
}));

vi.mock("@/services/api", () => ({
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
});
