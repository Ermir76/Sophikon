import { api, API_BASE } from "@/shared/api/api";
import type { AuthUser } from "@/features/auth/lib/auth";

// ----------------------------------------------------------------------
// AUTH SERVICE
// ----------------------------------------------------------------------
// This service handles the specific API calls for logging in and registering.
// It uses our `api.ts` helper to make the requests.
//
// API Endpoints:
// POST /auth/login                    -> Send email/password, get back tokens + user
// POST /auth/register                 -> Send user details, get back tokens + user
// POST /auth/refresh                  -> Send refresh token, get back new access token
// GET  /auth/verify-email             -> Backend handles via redirect (no frontend call)
// POST /auth/send-verification-email  -> Send/resend verification email
// ----------------------------------------------------------------------

/**
 * The data we send to the backend to log in.
 */
export interface LoginRequest {
  email: string;
  password: string;
  remember_me: boolean;
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

/**
 * Generic message response from the backend.
 * Backend: app/schema/auth.py -> MessageResponse
 */
export interface MessageResponse {
  message: string;
}

export interface PasswordResetRequest {
  email: string;
}

export interface PasswordResetConfirmRequest {
  token: string;
  new_password: string;
}

export interface ChangePasswordRequest {
  current_password: string;
  new_password: string;
}

export interface UpdateProfileRequest {
  full_name?: string;
  avatar_url?: string | null;
  timezone?: string;
  locale?: string;
}

export interface AiModelOption {
  model_id: string;
  label: string;
  recommended: boolean;
}

export interface AiProviderOption {
  provider_id: string;
  display_name: string;
  requires_env_key: string;
  available: boolean;
  models: AiModelOption[];
}

export interface AiModelDefaults {
  provider: string;
  model: string;
  mode: string;
}

export interface AiPreferencesResponse {
  auto_approve: Record<string, boolean>;
  provider: string | null;
  model: string | null;
  providers: AiProviderOption[];
  defaults: AiModelDefaults | null;
}

export interface AiPreferencesPatchRequest {
  auto_approve?: Record<string, boolean>;
  provider?: string | null;
  model?: string | null;
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

  /**
   * SEND / RESEND VERIFICATION EMAIL
   */
  async sendVerificationEmail() {
    const response = await api.post<MessageResponse>("/auth/send-verification-email");
    return response.data;
  },

  async requestPasswordReset(data: PasswordResetRequest) {
    const response = await api.post<MessageResponse>("/auth/password-reset", data);
    return response.data;
  },

  async confirmPasswordReset(data: PasswordResetConfirmRequest) {
    const response = await api.post<MessageResponse>("/auth/password-reset/confirm", data);
    return response.data;
  },

  async updateProfile(data: UpdateProfileRequest) {
    const response = await api.patch<AuthUser>("/users/me", data);
    return response.data;
  },

  async changePassword(data: ChangePasswordRequest) {
    const response = await api.post<MessageResponse>("/auth/change-password", data);
    return response.data;
  },

  async uploadAvatar(file: File) {
    const formData = new FormData();
    formData.append("file", file);
    const response = await api.post<AuthUser>("/users/me/avatar", formData);
    return response.data;
  },

  async deleteAvatar() {
    const response = await api.delete<AuthUser>("/users/me/avatar");
    return response.data;
  },

  async getAiPreferences(): Promise<AiPreferencesResponse> {
    const response = await api.get<AiPreferencesResponse>("/users/me/ai-preferences");
    return response.data;
  },

  async updateAiPreferences(data: AiPreferencesPatchRequest): Promise<AiPreferencesResponse> {
    const response = await api.patch<AiPreferencesResponse>("/users/me/ai-preferences", data);
    return response.data;
  },

  startGoogleOAuth(nextPath?: string | null) {
    const oauthUrl = new URL(
      `${API_BASE.replace(/\/$/, "")}/auth/oauth/google`,
      window.location.origin,
    );
    if (nextPath && nextPath.startsWith("/")) {
      oauthUrl.searchParams.set("next", nextPath);
    }
    window.location.assign(oauthUrl.toString());
  },
};
