import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { type InternalAxiosRequestConfig } from "axios";

// Mock axios BEFORE importing api
vi.mock("axios", async () => {
    const actual = await vi.importActual<typeof import("axios")>("axios");
    return {
        ...actual,
        default: {
            ...actual.default,
            post: vi.fn(),
            create: actual.default.create,
        },
    };
});

// Mock auth store
const { setStateMock, clearAuthMock, getUserMock } = vi.hoisted(() => ({
    setStateMock: vi.fn(),
    clearAuthMock: vi.fn(),
    getUserMock: vi.fn(() => ({ email: "stored@example.com" })),
}));
vi.mock("@/features/auth/store/auth-store", () => ({
    useAuthStore: {
        setState: setStateMock,
    },
}));

// Mock clearAuth
vi.mock("@/features/auth/lib/auth", () => ({
    clearAuth: clearAuthMock,
    getUser: getUserMock,
}));

// Now import api and axios
import { api, consumeBlockedUnverifiedEmail, refreshSessionOnce } from "./api";
import axios from "axios";

type RetryableConfig = InternalAxiosRequestConfig & { _retry?: boolean };

describe("API Interceptors", () => {
    beforeEach(() => {
        vi.clearAllMocks();
        window.sessionStorage.clear();
    });

    afterEach(() => {
        delete api.defaults.adapter;
    });

    it("401 triggers token refresh", async () => {
        // Mock refresh success
        vi.mocked(axios.post).mockResolvedValue({ status: 200 });

        // Mock adapter for api requests
        const adapterMock = vi.fn().mockImplementation(async (config: RetryableConfig) => {
            if (config.url === "/test" && !config._retry) {
                // First attempt: 401
                throw Object.assign(new Error("Request failed with status code 401"), {
                    response: { status: 401, config },
                    config,
                    isAxiosError: true,
                });
            }
            if (config._retry) {
                // Retry: 200
                return { data: "success", status: 200, headers: {} };
            }
            return { status: 404 };
        });

        api.defaults.adapter = adapterMock;

        await api.get("/test");

        expect(axios.post).toHaveBeenCalledWith(expect.stringContaining("/auth/refresh"), {}, expect.anything());
    });

    it("successful refresh retries original request", async () => {
        vi.mocked(axios.post).mockResolvedValue({ status: 200 });

        const adapterMock = vi.fn().mockImplementation(async (config: RetryableConfig) => {
            if (config.url === "/test" && !config._retry) {
                throw Object.assign(new Error("401"), {
                    response: { status: 401, config },
                    config,
                    isAxiosError: true,
                });
            }
            if (config._retry) {
                return { data: "retry-success", status: 200, headers: {} };
            }
        });
        api.defaults.adapter = adapterMock;

        const response = await api.get("/test");

        expect(response.data).toBe("retry-success");
        expect(adapterMock).toHaveBeenCalledTimes(2); // Initial + Retry
    });

    it("failed refresh triggers logout", async () => {
        // Mock refresh fail
        vi.mocked(axios.post).mockRejectedValue(new Error("Refresh failed"));

        const adapterMock = vi.fn().mockImplementation(async (config: RetryableConfig) => {
            throw Object.assign(new Error("401"), {
                response: { status: 401, config },
                config,
                isAxiosError: true,
            });
        });
        api.defaults.adapter = adapterMock;

        await expect(api.get("/test")).rejects.toThrow("Refresh failed");

        expect(setStateMock).toHaveBeenCalledWith({
            user: null,
            isAuthenticated: false,
            isInitialized: true,
        });
    });

    it("coalesces concurrent refresh attempts into a single request", async () => {
        let resolveRefresh: (() => void) | undefined;
        vi.mocked(axios.post).mockImplementation(
            () =>
                new Promise((resolve) => {
                    resolveRefresh = () => resolve({ status: 200 });
                }),
        );

        const firstRefresh = refreshSessionOnce();
        const secondRefresh = refreshSessionOnce();

        expect(axios.post).toHaveBeenCalledTimes(1);

        resolveRefresh?.();
        await Promise.all([firstRefresh, secondRefresh]);

        vi.mocked(axios.post).mockResolvedValueOnce({ status: 200 });
        await refreshSessionOnce();
        expect(axios.post).toHaveBeenCalledTimes(2);
    });

    it("does not retry if already retried", async () => {
        const adapterMock = vi.fn().mockImplementation(async (config: RetryableConfig) => {
            // Simulate that the config ALREADY had _retry: true
            const retryConfig: RetryableConfig = { ...config, _retry: true };
            throw Object.assign(new Error("401"), {
                response: { status: 401 },
                config: retryConfig,
                isAxiosError: true,
            });
        });
        api.defaults.adapter = adapterMock;

        await expect(api.get("/test")).rejects.toThrow("401");

        expect(axios.post).not.toHaveBeenCalled(); // No refresh
    });

    it("captures blocked unverified email from stored auth state", async () => {
        const adapterMock = vi.fn().mockImplementation(async (config: RetryableConfig) => {
            throw Object.assign(new Error("403"), {
                response: {
                    status: 403,
                    data: {
                        error: {
                            code: "EMAIL_VERIFICATION_REQUIRED",
                            message: "Email verification expired.",
                        },
                    },
                },
                config,
                isAxiosError: true,
            });
        });
        api.defaults.adapter = adapterMock;

        await expect(api.get("/projects")).rejects.toThrow("403");

        expect(consumeBlockedUnverifiedEmail()).toBe("stored@example.com");
    });
});
