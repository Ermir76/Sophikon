import { isAxiosError } from "axios";

import {
  BACKEND_PASSWORD_MAX_BYTES_MESSAGE,
  PASSWORD_TOO_LONG_MESSAGE,
} from "@/features/auth/lib/passwordPolicy";

function normalizeKnownErrorMessage(message: string): string {
  if (message === BACKEND_PASSWORD_MAX_BYTES_MESSAGE) {
    return PASSWORD_TOO_LONG_MESSAGE;
  }
  return message;
}

export function getErrorMessage(err: unknown): string {
  if (isAxiosError(err) && err.response?.data?.detail) {
    return normalizeKnownErrorMessage(err.response.data.detail);
  }
  if (isAxiosError(err) && err.response?.data?.error?.message) {
    return normalizeKnownErrorMessage(err.response.data.error.message);
  }
  if (err instanceof Error) {
    return normalizeKnownErrorMessage(err.message);
  }
  return "Something went wrong. Please try again.";
}
