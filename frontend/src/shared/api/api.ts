import axios, { AxiosError, type InternalAxiosRequestConfig } from "axios";
import { useAuthStore } from "@/features/auth/store/auth-store";

// Use the environment variable, or fallback (useful for local dev proxy)
export const API_BASE = import.meta.env.VITE_API_BASE_URL || "/api/v1";

export const api = axios.create({
  baseURL: API_BASE,
  withCredentials: true,
});

const BLOCKED_UNVERIFIED_SESSION_KEY = "auth.blocked-unverified-email";
const DEACTIVATED_ACCOUNT_SESSION_KEY = "auth.deactivated-account";
const DEACTIVATED_ACCOUNT_ERROR_CODE = "ACCOUNT_DEACTIVATED";

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
  "/auth/resend-verification-email",
  "/auth/password-reset",
  "/auth/password-reset/confirm",
];

const VERIFICATION_RECOVERY_PATHS = new Set([
  "/login",
  "/register",
  "/verify-email",
  "/forgot-password",
  "/reset-password",
]);

function shouldRedirectToVerificationRecovery(): boolean {
  return !VERIFICATION_RECOVERY_PATHS.has(window.location.pathname);
}

export function getVerificationRecoveryRedirectHref(
  location: Pick<Location, "pathname" | "search" | "hash"> = window.location,
): string | null {
  if (VERIFICATION_RECOVERY_PATHS.has(location.pathname)) {
    return null;
  }

  const next = encodeURIComponent(
    `${location.pathname}${location.search}${location.hash}`,
  );
  return `/login?next=${next}`;
}

function markDeactivatedAccountNotice(): void {
  window.sessionStorage.setItem(DEACTIVATED_ACCOUNT_SESSION_KEY, "1");
}

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
    const errorCode =
      typeof error.response?.data === "object" &&
      error.response?.data !== null &&
      "error" in error.response.data &&
      typeof error.response.data.error === "object" &&
      error.response.data.error !== null &&
      "code" in error.response.data.error
        ? String(error.response.data.error.code)
        : null;
    const responseBlockedEmail =
      typeof error.response?.data === "object" &&
      error.response?.data !== null &&
      "error" in error.response.data &&
      typeof error.response.data.error === "object" &&
      error.response.data.error !== null &&
      "email" in error.response.data.error
        ? String(error.response.data.error.email)
        : null;

    if (errorCode === "EMAIL_VERIFICATION_REQUIRED") {
      let blockedEmail = responseBlockedEmail;
      if (!blockedEmail) {
        const { getUser } = await import("@/features/auth/lib/auth");
        blockedEmail = getUser()?.email ?? null;
      }
      if (blockedEmail) {
        window.sessionStorage.setItem(BLOCKED_UNVERIFIED_SESSION_KEY, blockedEmail);
      }

      const { clearAuth } = await import("@/features/auth/lib/auth");
      clearAuth();
      useAuthStore.setState({
        user: null,
        isAuthenticated: false,
        isInitialized: true,
      });

      if (shouldRedirectToVerificationRecovery()) {
        const recoveryHref = getVerificationRecoveryRedirectHref();
        if (recoveryHref) {
          window.location.assign(recoveryHref);
        }
      }
    }

    if (errorCode === DEACTIVATED_ACCOUNT_ERROR_CODE) {
      markDeactivatedAccountNotice();

      const { clearAuth } = await import("@/features/auth/lib/auth");
      clearAuth();
      useAuthStore.setState({
        user: null,
        isAuthenticated: false,
        isInitialized: true,
      });

      const recoveryHref = getVerificationRecoveryRedirectHref();
      if (recoveryHref) {
        window.location.assign(recoveryHref);
      }
    }

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

export function consumeBlockedUnverifiedEmail(): string | null {
  const email = window.sessionStorage.getItem(BLOCKED_UNVERIFIED_SESSION_KEY);
  if (email) {
    window.sessionStorage.removeItem(BLOCKED_UNVERIFIED_SESSION_KEY);
  }
  return email;
}

export function consumeDeactivatedAccountNotice(): boolean {
  const marker = window.sessionStorage.getItem(DEACTIVATED_ACCOUNT_SESSION_KEY);
  if (marker) {
    window.sessionStorage.removeItem(DEACTIVATED_ACCOUNT_SESSION_KEY);
    return true;
  }
  return false;
}
