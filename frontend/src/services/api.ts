import { getAccessToken, clearAuth } from "@/lib/auth";

// ----------------------------------------------------------------------
// API SERVICE
// ----------------------------------------------------------------------
// This file is the "middleman" between our React components and the Backend.
// Instead of components calling `fetch` directly, they use this `api` helper.
//
// CONCEPTS:
// 1. Async/Await: Fetching data is slow (it goes over the internet).
//    `async` means "this function takes time".
//    `await` means "pause here until the data comes back".
// 2. Generics <T>: This is a Typescript superpower.
//    It lets us say "This function returns some data, but I don't know what
//    shape it is yet. The caller will tell me."
//    Example: api.get<User>("/me") -> T becomes User.
// 3. Headers: Meta-information sent with the request.
//    We use this to send the "Authorization" token.
// ----------------------------------------------------------------------

const API_BASE = "/api/v1"; // The root URL for our backend

/**
 * A wrapper around the built-in `fetch` function.
 * It automatically adds the Auth Token and handles errors.
 */
async function request<T>(
  endpoint: string,
  options: RequestInit = {},
): Promise<T> {
  // 1. Get the token from our Auth Helper (Local Storage)
  const token = getAccessToken();

  // 2. Set up default headers
  const headers: HeadersInit = {
    "Content-Type": "application/json", // We are sending/receiving JSON
    ...options.headers, // Merge any custom headers passed in options
  };

  // 3. If we have a token, add it to the headers.
  //    This is like showing your ID card at the door.
  if (token) {
    (headers as Record<string, string>)["Authorization"] = `Bearer ${token}`;
  }

  // 4. Make the actual request
  const res = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers,
  });

  // 5. Handle "Unauthorized" (401) errors specially.
  //    If the backend says "Who are you?", our token is probably invalid/expired.
  if (res.status === 401) {
    clearAuth(); // Delete the bad token
    window.location.href = "/app/login"; // Redirect to login page
    // (Note: In a pure React way, we'd use a router, but this works for now!)
    throw new Error("Unauthorized");
  }

  // 6. Handle other errors (404, 500, etc.)
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Request failed: ${res.status}`);
  }

  // 7. Success! Return the data.
  //    We promise (Promise<T>) that the result matches the shape T.
  return res.json() as Promise<T>;
}

// We export a simple object with methods for GET, POST, PUT, DELETE.
// This makes using the API very readable in our components:
// api.get("/users")
// api.post("/login", { email, password })
export const api = {
  get: <T>(endpoint: string) => request<T>(endpoint),

  post: <T>(endpoint: string, data: unknown) =>
    request<T>(endpoint, {
      method: "POST",
      body: JSON.stringify(data),
    }),

  put: <T>(endpoint: string, data: unknown) =>
    request<T>(endpoint, {
      method: "PUT",
      body: JSON.stringify(data),
    }),

  delete: <T>(endpoint: string) => request<T>(endpoint, { method: "DELETE" }),
};
