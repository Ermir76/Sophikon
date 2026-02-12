import axios, { AxiosError } from "axios";
import { useAuthStore } from "@/store/auth-store";

// Use the environment variable, or fallback (useful for local dev proxy)
const API_BASE = import.meta.env.VITE_API_BASE_URL || "/api/v1";

export const api = axios.create({
  baseURL: API_BASE,
  headers: {
    "Content-Type": "application/json",
  },
});

// Request Interceptor: Attach Token
api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().token;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response Interceptor: Handle Errors (401)
api.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      useAuthStore.getState().logout();
      window.location.href = "/app/login"; // Redirect to login
    }
    return Promise.reject(error);
  },
);
