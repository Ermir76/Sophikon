import { create } from "zustand";
import {
  type AuthUser,
  getAccessToken,
  getUser,
  saveAuth,
  clearAuth,
} from "@/lib/auth";

interface AuthState {
  user: AuthUser | null;
  token: string | null;
  isAuthenticated: boolean;
  login: (accessToken: string, refreshToken: string, user: AuthUser) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>((set) => {
  // Synchronously initialize state from localStorage
  const initialToken = getAccessToken();
  const initialUser = getUser();

  return {
    user: initialUser,
    token: initialToken,
    isAuthenticated: !!initialToken,

    login: (accessToken, refreshToken, user) => {
      saveAuth(accessToken, refreshToken, user);
      set({
        token: accessToken,
        user,
        isAuthenticated: true,
      });
    },

    logout: () => {
      clearAuth();
      set({
        token: null,
        user: null,
        isAuthenticated: false,
      });
    },
  };
});
