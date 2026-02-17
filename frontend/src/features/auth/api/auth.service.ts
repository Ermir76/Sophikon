import { api } from "@/shared/api/api";
import type { AuthUser } from "@/features/auth/lib/auth";

// ----------------------------------------------------------------------
// AUTH SERVICE
// ----------------------------------------------------------------------
// This service handles the specific API calls for logging in and registering.
// It uses our `api.ts` helper to make the requests.
//
// API Endpoints:
// POST /auth/login    -> Send email/password, get back tokens + user
// POST /auth/register -> Send user details, get back tokens + user
// POST /auth/refresh  -> Send refresh token, get back new access token
// ----------------------------------------------------------------------

/**
 * The data we send to the backend to log in.
 */
export interface LoginRequest {
  email: string;
  password: string;
}

/**
 * The data we send to the backend to register a new user.
 */
export interface RegisterRequest {
  email: string;
  password: string;
  full_name: string;
}

/**
 * The data the backend sends back when we log in or register.
 * Backend: app/schema/auth.py -> AuthResponse
 *
 * Tokens are set via httpOnly cookies; the frontend only uses `user`.
 */
export interface AuthResponse {
  user: AuthUser;
}

export const authService = {
  /**
   * LOG IN
   */
  async login(data: LoginRequest) {
    const response = await api.post<AuthResponse>("/auth/login", data);
    return response.data;
  },

  /**
   * REGISTER
   */
  async register(data: RegisterRequest) {
    const response = await api.post<AuthResponse>("/auth/register", data);
    return response.data;
  },

  /**
   * REFRESH TOKEN
   */
  async refresh() {
    const response = await api.post<AuthResponse>("/auth/refresh");
    return response.data;
  },

  /**
   * GET CURRENT USER
   */
  async me() {
    const response = await api.get<AuthResponse["user"]>("/auth/me");
    return response.data;
  },
};
