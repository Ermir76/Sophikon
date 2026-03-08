import { Navigate, Outlet, useLocation } from "react-router";
import { useAuthStore } from "@/features/auth";

// ----------------------------------------------------------------------
// PROTECTED ROUTE
// ----------------------------------------------------------------------
// Only allows logged-in users.
// If you are NOT logged in, it sends you to /login.

export function ProtectedRoute() {
  const location = useLocation();
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const isInitialized = useAuthStore((state) => state.isInitialized);

  if (!isInitialized) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
      </div>
    );
  }

  if (!isAuthenticated) {
    const next = encodeURIComponent(
      `${location.pathname}${location.search}${location.hash}`,
    );
    return <Navigate to={`/login?next=${next}`} replace />;
  }

  // "Outlet" means: Render the child routes (the actual page).
  return <Outlet />;
}
