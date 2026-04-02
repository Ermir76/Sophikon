import { z } from "zod";

export const PASSWORD_MIN_LENGTH_MESSAGE = "Password must be at least 8 characters.";
export const PASSWORD_TOO_LONG_MESSAGE = "Password is too long. Please use a shorter password.";
export const PASSWORD_UPPERCASE_MESSAGE = "Password must contain at least one uppercase letter";
export const PASSWORD_NUMBER_MESSAGE = "Password must contain at least one number";
export const PASSWORD_SPECIAL_MESSAGE = "Password must contain at least one special character";
export const BACKEND_PASSWORD_MAX_BYTES_MESSAGE = "Password must be at most 72 bytes";

const PASSWORD_UPPERCASE_RE = /[A-Z]/;
const PASSWORD_NUMBER_RE = /[0-9]/;
const PASSWORD_SPECIAL_RE = /[^a-zA-Z0-9]/;
const PASSWORD_MAX_BYTES = 72;
const textEncoder = new TextEncoder();

type PasswordChecklistItem = {
  label: string;
  valid: boolean;
};

export function createPasswordSchema() {
  return z
    .string()
    .min(8, PASSWORD_MIN_LENGTH_MESSAGE)
    .refine((value) => textEncoder.encode(value).length <= PASSWORD_MAX_BYTES, {
      message: PASSWORD_TOO_LONG_MESSAGE,
    })
    .regex(PASSWORD_UPPERCASE_RE, PASSWORD_UPPERCASE_MESSAGE)
    .regex(PASSWORD_NUMBER_RE, PASSWORD_NUMBER_MESSAGE)
    .regex(PASSWORD_SPECIAL_RE, PASSWORD_SPECIAL_MESSAGE);
}

export function getPasswordChecklist(password: string): PasswordChecklistItem[] {
  return [
    { label: "At least 8 characters", valid: password.length >= 8 },
    { label: "One uppercase letter", valid: PASSWORD_UPPERCASE_RE.test(password) },
    { label: "One number", valid: PASSWORD_NUMBER_RE.test(password) },
    { label: "One special character", valid: PASSWORD_SPECIAL_RE.test(password) },
  ];
}
