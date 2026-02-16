import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { type ReactNode } from "react";
import { useLogin, useRegister } from "./useAuth";

// Mocks
const mockLogin = vi.fn();
const mockNavigate = vi.fn();

vi.mock("@/services/auth", () => ({
    authService: {
        login: vi.fn(),
        register: vi.fn(),
    },
}));

vi.mock("@/store/auth-store", () => ({
    useAuthStore: vi.fn((selector) => selector({ login: mockLogin })),
}));

vi.mock("react-router", () => ({
    useNavigate: vi.fn(() => mockNavigate),
}));

import { authService } from "@/services/auth";

function createWrapper() {
    const qc = new QueryClient({
        defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
    });
    return ({ children }: { children: ReactNode }) => (
        <QueryClientProvider client= { qc } > { children } </QueryClientProvider>
  );
}

describe("useAuth Hooks", () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

    it("useLogin — calls authService.login, updates store", async () => {
        const user = { id: "1", email: "a@b.com", full_name: "A" };
        (authService.login as any).mockResolvedValue({ user });

        const { result } = renderHook(() => useLogin(), { wrapper: createWrapper() });

        await result.current.mutateAsync({ email: "a@b.com", password: "pass" });

        expect(authService.login).toHaveBeenCalledWith({ email: "a@b.com", password: "pass" });
        expect(mockLogin).toHaveBeenCalledWith(user);
        expect(mockNavigate).toHaveBeenCalledWith("/");
    });

    it("useRegister — calls authService.register, updates store", async () => {
        const user = { id: "1", email: "a@b.com", full_name: "A" };
        (authService.register as any).mockResolvedValue({ user });

        const { result } = renderHook(() => useRegister(), { wrapper: createWrapper() });

        await result.current.mutateAsync({ email: "a@b.com", password: "pass", full_name: "A" });

        expect(authService.register).toHaveBeenCalledWith({ email: "a@b.com", password: "pass", full_name: "A" });
        expect(mockLogin).toHaveBeenCalledWith(user);
        expect(mockNavigate).toHaveBeenCalledWith("/");
    });
});
