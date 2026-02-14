import { z } from "zod";

// ----------------------------------------------------------------------
// AUTHENTICATION HELPER FUNCTIONS
// ----------------------------------------------------------------------
// This file acts as a "Service" or "Helper".
// Its job is to handle the "dirty work" of saving and loading data
// from the browser's Local Storage.
//
// CONCEPTS:
// 1. Local Storage: A way to save data in the user's browser that stays
//    even after they close the window.
// 2. Tokens: Like a digital ID card.
//    - Access Token: The card you show to get into the building (API).
//    - Refresh Token: The ticket you use to get a new ID card when the old one expires.
// 3. Serialization: Converting an object (like a User) into a string (text)
//    so it can be saved in Local Storage.
// ----------------------------------------------------------------------

// Keys are the "labels" we use to find our data in Local Storage.
// Think of them like filenames in a cabinet.
const USER_KEY = "sophikon_user";

// This defines the "shape" of a User object.
// Typescript uses this to prevent us from making mistakes, like trying
// to access `user.phoneNumber` if it doesn't exist.
export interface AuthUser {
  id: string;
  email: string;
  full_name: string;
}

/**
 * Saves authenticated user data to the browser.
 * Call this after a successful login.
 *
 * @param user - The user's profile information
 */
export function saveAuth(user: AuthUser) {
  // We cannot save an Object directly to Local Storage.
  // We must "stringify" it (turn it into text) first.
  localStorage.setItem(USER_KEY, JSON.stringify(user));
}

/**
 * Retrieves the User object.
 * This is "deserialization" - turning text back into an Object.
 */
// ... (keep existing code)

const userSchema = z.object({
  id: z.string(),
  email: z.string().email(),
  full_name: z.string(),
});

export function getUser(): AuthUser | null {
  const raw = localStorage.getItem(USER_KEY);

  if (!raw) return null;

  try {
    const parsed = JSON.parse(raw);
    const result = userSchema.safeParse(parsed);

    if (result.success) {
      return result.data;
    } else {
      console.warn(
        "Invalid user data in localStorage, clearing.",
        result.error,
      );
      localStorage.removeItem(USER_KEY);
      return null;
    }
  } catch {
    return null;
  }
}

/**
 * Clears all authentication data.
 * Call this when the user logs out.
 */
export function clearAuth() {
  localStorage.removeItem(USER_KEY);
}

/**
 * Checks if the user is logged in.
 * We implicitly trust the presence of user data, but the API will enforce reality.
 */
export function isAuthenticated(): boolean {
  return !!getUser();
}
