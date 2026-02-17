import { Navigate, Outlet } from "react-router";
import { useAuthStore } from "@/features/auth/store/auth-store";
import { PageLoader } from "@/shared/components/PageLoader";

// ----------------------------------------------------------------------
// GUEST ROUTE
// ----------------------------------------------------------------------
// Only allows GUESTS (people who are NOT logged in).
// If you ARE logged in, it sends you to the dashboard.
// Used for: Login Page, Register Page (why register if you already have an account?)

export function GuestRoute() {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const isInitialized = useAuthStore((state) => state.isInitialized);

  if (!isInitialized) {
    return <PageLoader />;
  }

  if (isAuthenticated) {
    return <Navigate to="/" replace />;
  }

  return <Outlet />;
}
