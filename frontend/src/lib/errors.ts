import { isAxiosError } from "axios";

export function getErrorMessage(err: unknown): string {
  if (isAxiosError(err) && err.response?.data?.detail) {
    return err.response.data.detail;
  }
  if (err instanceof Error) {
    return err.message;
  }
  return "Something went wrong. Please try again.";
}
