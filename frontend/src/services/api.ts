import axios, { AxiosError, type InternalAxiosRequestConfig } from "axios";
import { useAuthStore } from "@/store/auth-store";

// Use the environment variable, or fallback (useful for local dev proxy)
const API_BASE = import.meta.env.VITE_API_BASE_URL || "/api/v1";

export const api = axios.create({
  baseURL: API_BASE,
  headers: {
    "Content-Type": "application/json",
  },
  withCredentials: true,
});

interface RetryableRequest extends InternalAxiosRequestConfig {
  _retry?: boolean;
}

// Response Interceptor: Handle Errors (401)
api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as RetryableRequest;

    // Check if 401 and we haven't retried yet
    if (
      error.response?.status === 401 &&
      originalRequest &&
      !originalRequest._retry
    ) {
      // Mark as retried to avoid infinite loops
      originalRequest._retry = true;

      try {
        // Attempt to refresh the token (cookie-based)
        await axios.post(
          `${API_BASE}/auth/refresh`,
          {},
          { withCredentials: true },
        );

        // Retry the original request
        return api(originalRequest);
      } catch (refreshError) {
        // Refresh failed (or no refresh token), force logout
        useAuthStore.getState().logout();
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  },
);
