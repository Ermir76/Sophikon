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
const ACCESS_TOKEN_KEY = "sophikon_access_token";
const REFRESH_TOKEN_KEY = "sophikon_refresh_token";
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
 * Saves all authentication data to the browser.
 * Call this after a successful login.
 *
 * @param accessToken - The short-lived token for API requests
 * @param refreshToken - The long-lived token to get new access tokens
 * @param user - The user's profile information
 */
export function saveAuth(
  accessToken: string,
  refreshToken: string,
  user: AuthUser,
) {
  // localStorage.setItem("key", "value") saves data.
  localStorage.setItem(ACCESS_TOKEN_KEY, accessToken);
  localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);

  // We cannot save an Object directly to Local Storage.
  // We must "stringify" it (turn it into text) first.
  localStorage.setItem(USER_KEY, JSON.stringify(user));
}

/**
 * Retrieves the Access Token.
 * Used by API calls to prove who you are.
 */
export function getAccessToken(): string | null {
  return localStorage.getItem(ACCESS_TOKEN_KEY);
}

/**
 * Retrieves the Refresh Token.
 * Used to get a new Access Token when the old one expires.
 */
export function getRefreshToken(): string | null {
  return localStorage.getItem(REFRESH_TOKEN_KEY);
}

/**
 * Retrieves the User object.
 * This is "deserialization" - turning text back into an Object.
 */
export function getUser(): AuthUser | null {
  const raw = localStorage.getItem(USER_KEY);

  // If there is no data, return null (no user logged in).
  if (!raw) return null;

  try {
    // JSON.parse turns the text string back into a Javascript Object.
    // We use "as AuthUser" to tell Typescript "Trust me, this is a User".
    return JSON.parse(raw) as AuthUser;
  } catch {
    // If the data is corrupted (someone messed with Local Storage),
    // we return null to be safe.
    return null;
  }
}

/**
 * Clears all authentication data.
 * Call this when the user logs out.
 */
export function clearAuth() {
  localStorage.removeItem(ACCESS_TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}

/**
 * Checks if the user is logged in.
 * Currently, we just check if an access token exists.
 * In a real app, we might also check if it's expired.
 */
export function isAuthenticated(): boolean {
  // The "!!" converts a value to a boolean (true/false).
  // if getAccessToken() returns a string -> true
  // if getAccessToken() returns null -> false
  return !!getAccessToken();
}
