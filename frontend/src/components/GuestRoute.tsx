import { Navigate, Outlet } from "react-router";
import { useAuth } from "@/contexts/AuthContexts";

// ----------------------------------------------------------------------
// GUEST ROUTE
// ----------------------------------------------------------------------
// Only allows GUESTS (people who are NOT logged in).
// If you ARE logged in, it sends you to the dashboard.
// Used for: Login Page, Register Page (why register if you already have an account?)

export function GuestRoute() {
  const { isAuthenticated } = useAuth();

  if (isAuthenticated) {
    return <Navigate to="/" replace />;
  }

  return <Outlet />;
}
