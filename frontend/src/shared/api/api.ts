import axios, { AxiosError, type InternalAxiosRequestConfig } from "axios";
import { useAuthStore } from "@/features/auth/store/auth-store";

// Use the environment variable, or fallback (useful for local dev proxy)
export const API_BASE = import.meta.env.VITE_API_BASE_URL || "/api/v1";

export const api = axios.create({
  baseURL: API_BASE,
  withCredentials: true,
});

interface RetryableRequest extends InternalAxiosRequestConfig {
  _retry?: boolean;
}

let refreshPromise: Promise<void> | null = null;

// Auth endpoints should never trigger token refresh
const AUTH_PATHS = [
  "/auth/login",
  "/auth/register",
  "/auth/logout",
  "/auth/refresh",
  "/auth/me",
  "/auth/send-verification-email",
  "/auth/password-reset",
  "/auth/password-reset/confirm",
];

export async function refreshSessionOnce(): Promise<void> {
  if (!refreshPromise) {
    refreshPromise = axios
      .post(
        `${API_BASE}/auth/refresh`,
        {},
        { withCredentials: true },
      )
      .then(() => undefined)
      .finally(() => {
        refreshPromise = null;
      });
  }

  return refreshPromise;
}

// Response Interceptor: Handle Errors (401)
api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as RetryableRequest;
    const requestPath = originalRequest?.url || "";

    // Skip refresh for auth endpoints and already-retried requests
    const isAuthEndpoint = AUTH_PATHS.some((p) => requestPath.includes(p));
    if (
      error.response?.status === 401 &&
      originalRequest &&
      !originalRequest._retry &&
      !isAuthEndpoint
    ) {
      originalRequest._retry = true;

      try {
        await refreshSessionOnce();

        return api(originalRequest);
      } catch (refreshError) {
        // Refresh failed — clear local state without calling backend logout
        const { clearAuth } = await import("@/features/auth/lib/auth");
        clearAuth();
        useAuthStore.setState({
          user: null,
          isAuthenticated: false,
          isInitialized: true,
        });
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  },
);
