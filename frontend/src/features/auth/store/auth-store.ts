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

    checkSession: async () => {
      try {
        const { authService } = await import("@/features/auth/api/auth.service");
        const user = await authService.me();
        saveAuth(user);
        set({ user, isAuthenticated: true, isInitialized: true });
      } catch {
        clearAuth();
        set({ user: null, isAuthenticated: false, isInitialized: true });
      }
    },
  };
});
