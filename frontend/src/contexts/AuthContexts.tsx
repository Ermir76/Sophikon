import {
  createContext, // creates the shared state container
  useContext, // hook to read from it
  useState, // to store user + token in React state
  useEffect, // to load saved auth on first render
  type ReactNode, // type for children prop
} from "react";
import {
  saveAuth, // saves tokens + user to localStorage
  clearAuth, // removes all auth data from localStorage
  getAccessToken, // reads the access token from localStorage
  getUser, // reads + parses the user from localStorage
  type AuthUser, // user type — single source of truth from auth.ts
} from "@/lib/auth";

// ---------- TYPES ----------

// Shape of what the context provides to all components
// This is the "contract" — every component knows these exist
interface AuthContextType {
  user: AuthUser | null; // current user, or null if logged out
  token: string | null; // JWT access token, or null
  isAuthenticated: boolean; // shortcut: is there a token?
  login: (token: string, refreshToken: string, user: AuthUser) => void; // call after successful login
  logout: () => void; // call to sign out
}

// ---------- CREATE CONTEXT ----------

// Create the "bulletin board" with undefined as default
// undefined because we'll throw an error if someone tries
// to use it outside of the Provider
const AuthContext = createContext<AuthContextType | undefined>(undefined);

// ---------- PROVIDER COMPONENT ----------

// This wraps your entire app. It OWNS the auth state.
// Any component inside it can access user/token/login/logout.
export function AuthProvider({ children }: { children: ReactNode }) {
  // React state — when these change, all consumers re-render
  const [user, setUser] = useState<AuthUser | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const isAuthenticated = !!token; // derived state

  // ---------- LOAD SAVED AUTH ON FIRST RENDER ----------

  useEffect(() => {
    // Reuse auth.ts helpers instead of raw localStorage calls
    const storedToken = getAccessToken();
    const storedUser = getUser();

    if (storedToken && storedUser) {
      setToken(storedToken);
      setUser(storedUser);
    }
  }, []); // empty array = run only once on mount

  // ---------- LOGIN FUNCTION ----------

  const login = (
    accessToken: string,
    refreshToken: string,
    userData: AuthUser,
  ) => {
    // Save to localStorage via auth.ts (single source of truth)
    saveAuth(accessToken, refreshToken, userData);

    // Update React state (triggers re-renders)
    setToken(accessToken);
    setUser(userData);
  };

  // ---------- LOGOUT FUNCTION ----------

  const logout = () => {
    // Clear localStorage via auth.ts
    clearAuth();

    // Clear React state
    setToken(null);
    setUser(null);
  };

  // ---------- PROVIDER VALUE ----------

  // This is the "contract" object that gets passed down
  const value: AuthContextType = {
    user,
    token,
    isAuthenticated,
    login,
    logout,
  };

  // Render the children inside the Context.Provider
  // This makes `value` available to all components inside AuthProvider
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

// ---------- CUSTOM HOOK ----------

// Instead of useContext(AuthContext) everywhere, we make a clean hook.
// It also throws a helpful error if used outside the Provider.
export function useAuth() {
  const context = useContext(AuthContext);

  if (!context) {
    throw new Error("useAuth must be used inside <AuthProvider>");
  }

  return context;
}

// ---------- TODO: FUTURE OPTIMIZATIONS ----------
// TODO: Memoize the context value with useMemo to prevent unnecessary re-renders
// TODO: Initialize state from localStorage inside useState(() => ...) instead of useEffect to avoid double render
// TODO: Move token handling to HTTP-only cookies for better security (requires backend changes)
