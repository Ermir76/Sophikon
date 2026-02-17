import { Suspense, useEffect, useRef } from "react";
import { Outlet, useLocation } from "react-router";

import { AppHeader } from "@/shared/layout/AppHeader";
import { AppSidebar } from "@/shared/layout/AppSidebar";
import { SidebarInset, SidebarProvider } from "@/shared/ui/sidebar";
import { PageLoader } from "@/shared/components/PageLoader";

export function AppLayout() {
  const mainRef = useRef<HTMLElement>(null);
  const location = useLocation();

  useEffect(() => {
    // Focus main content on route change for screen readers
    mainRef.current?.focus();
  }, [location.pathname]);

  return (
    <SidebarProvider>
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:absolute focus:z-50 focus:p-4 focus:bg-background focus:text-foreground"
      >
        Skip to content
      </a>
      <AppSidebar />
      <SidebarInset>
        <AppHeader />
        <main
          id="main-content"
          ref={mainRef}
          tabIndex={-1}
          className="flex-1 overflow-auto outline-none"
        >
          <Suspense fallback={<PageLoader />}>
            <Outlet />
          </Suspense>
        </main>
      </SidebarInset>
    </SidebarProvider>
  );
}
