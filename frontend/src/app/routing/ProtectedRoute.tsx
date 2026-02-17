import { Navigate, Outlet } from "react-router";
import { useAuthStore } from "@/features/auth/store/auth-store";

// ----------------------------------------------------------------------
// PROTECTED ROUTE
// ----------------------------------------------------------------------
// Only allows logged-in users.
// If you are NOT logged in, it sends you to /login.

export function ProtectedRoute() {
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
    // "replace" means: Don't let them click "Back" to return here.
    return <Navigate to="/login" replace />;
  }

  // "Outlet" means: Render the child routes (the actual page).
  return <Outlet />;
}
