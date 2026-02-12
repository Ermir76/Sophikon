import { Navigate, Outlet } from "react-router";
import { useAuth } from "@/contexts/AuthContexts";

// ----------------------------------------------------------------------
// PROTECTED ROUTE
// ----------------------------------------------------------------------
// Only allows logged-in users.
// If you are NOT logged in, it sends you to /login.

export function ProtectedRoute() {
  const { isAuthenticated } = useAuth();

  if (!isAuthenticated) {
    // "replace" means: Don't let them click "Back" to return here.
    return <Navigate to="/login" replace />;
  }

  // "Outlet" means: Render the child routes (the actual page).
  return <Outlet />;
}
