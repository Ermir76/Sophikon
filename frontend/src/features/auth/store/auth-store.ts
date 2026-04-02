import { create } from "zustand";
import { type AuthUser, getUser, saveAuth, clearAuth } from "@/features/auth/lib/auth";

export interface AuthState {
  user: AuthUser | null;
  isAuthenticated: boolean;
  isInitialized: boolean;
  login: (user: AuthUser) => void;
  logout: () => void;
  checkSession: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set) => {
  // Synchronously initialize state from localStorage
  const initialUser = getUser();
  const isUnauthorizedError = (error: unknown): boolean =>
    typeof error === "object" &&
    error !== null &&
    "response" in error &&
    (error as { response?: { status?: number } }).response?.status === 401;

  return {
    user: initialUser,
    isAuthenticated: !!initialUser, // Optimistic, but verified by checkSession
    isInitialized: false,

    login: (user) => {
      saveAuth(user);
      set({
        user,
        isAuthenticated: true,
        isInitialized: true,
      });
    },

    /**
     * @architecture intentional deviation
     * Dynamic imports are used here to break circular dependency deadlocks with api/react-query
     * during the initial application bootstrap phase.
     */
    logout: async () => {
      // Call backend to clear cookies
      try {
        const { api } = await import("@/shared/api/api");
        await api.post("/auth/logout");
      } catch (e) {
        console.error("Logout failed on backend", e);
      }

      // Clear React Query cache to prevent stale data leaking to the next user
      const { queryClient } = await import("@/config/react-query");
      queryClient.clear();

      clearAuth();
      set({
        user: null,
        isAuthenticated: false,
        isInitialized: true,
      });
    },

    /**
     * @architecture intentional deviation
     * Dynamic import is used here to avoid circular dependency deadlocks with auth.service
     * which itself depends on this store during bootstrap.
     */
    checkSession: async () => {
      try {
        const { authService } = await import("@/features/auth/api/auth.service");
        const user = await authService.me();
        saveAuth(user);
        set({ user, isAuthenticated: true, isInitialized: true });
      } catch (error) {
        if (isUnauthorizedError(error)) {
          try {
            const [{ refreshSessionOnce }, { authService }] = await Promise.all([
              import("@/shared/api/api"),
              import("@/features/auth/api/auth.service"),
            ]);
            await refreshSessionOnce();
            const user = await authService.me();
            saveAuth(user);
            set({ user, isAuthenticated: true, isInitialized: true });
            return;
          } catch {
            // Fall through to local auth clear when refresh recovery fails.
          }
        }

        clearAuth();
        set({ user: null, isAuthenticated: false, isInitialized: true });
      }
    },
  };
});
