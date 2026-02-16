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
const logoutMock = vi.fn();
vi.mock("@/store/auth-store", () => ({
    useAuthStore: {
        getState: vi.fn(() => ({ logout: logoutMock })),
    },
}));

// Now import api and axios
import { api } from "./api";
import axios from "axios";

describe("API Interceptors", () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

    afterEach(() => {
        delete api.defaults.adapter;
    });

    it("401 triggers token refresh", async () => {
        // Mock refresh success
        (axios.post as any).mockResolvedValue({ status: 200 });

        // Mock adapter for api requests
        const adapterMock = vi.fn().mockImplementation(async (config: InternalAxiosRequestConfig) => {
            if (config.url === "/test" && !(config as any)._retry) {
                // First attempt: 401
                const error: any = new Error("Request failed with status code 401");
                error.response = { status: 401, config };
                error.config = config;
                error.isAxiosError = true;
                throw error;
            }
            if ((config as any)._retry) {
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
        (axios.post as any).mockResolvedValue({ status: 200 });

        const adapterMock = vi.fn().mockImplementation(async (config: InternalAxiosRequestConfig) => {
            if (config.url === "/test" && !(config as any)._retry) {
                const error: any = new Error("401");
                error.response = { status: 401, config };
                error.config = config;
                error.isAxiosError = true;
                throw error;
            }
            if ((config as any)._retry) {
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
        (axios.post as any).mockRejectedValue(new Error("Refresh failed"));

        const adapterMock = vi.fn().mockImplementation(async (config: InternalAxiosRequestConfig) => {
            const error: any = new Error("401");
            error.response = { status: 401, config };
            error.config = config;
            error.isAxiosError = true;
            throw error;
        });
        api.defaults.adapter = adapterMock;

        await expect(api.get("/test")).rejects.toThrow("Refresh failed");

        expect(logoutMock).toHaveBeenCalled();
    });

    it("does not retry if already retried", async () => {
        const adapterMock = vi.fn().mockImplementation(async (config: InternalAxiosRequestConfig) => {
            const error: any = new Error("401");
            error.response = { status: 401 };
            // Simulate that the config ALREADY had _retry: true
            config = { ...config, _retry: true } as any;
            error.config = config;
            error.isAxiosError = true;
            throw error;
        });
        api.defaults.adapter = adapterMock;

        await expect(api.get("/test")).rejects.toThrow("401");

        expect(axios.post).not.toHaveBeenCalled(); // No refresh
    });
});
