import { Suspense, lazy } from "react";
import { Route, Routes } from "react-router";

import { AppLayout } from "@/shared/layout/AppLayout";
import { ProjectLayout } from "@/features/projects/components/ProjectLayout";
import { ProtectedRoute } from "@/app/routing/ProtectedRoute";
import { GuestRoute } from "@/app/routing/GuestRoute";
import { OrgGuard } from "@/app/routing/OrgGuard";
import { PageLoader } from "@/shared/components/PageLoader";

// Lazy imports
const LoginPage = lazy(() => import("@/features/auth/pages/LoginPage"));
const RegisterPage = lazy(() => import("@/features/auth/pages/RegisterPage"));
const AuthLayout = lazy(() => import("@/shared/layout/AuthLayout"));
const DashboardPage = lazy(
  () => import("@/features/dashboard/pages/DashboardPage"),
);
const TasksPage = lazy(() => import("@/features/tasks/pages/TasksPage"));
const GanttPage = lazy(() => import("@/features/gantt/pages/GanttPage"));
const ResourcesPage = lazy(
  () => import("@/features/resources/pages/ResourcesPage"),
);
const CalendarPage = lazy(
  () => import("@/features/calendar/pages/CalendarPage"),
);
const ProjectsPage = lazy(
  () => import("@/features/projects/pages/ProjectsPage"),
);
const ReportsPage = lazy(
  () => import("@/features/reports/pages/ReportsPage"),
);
const OrgSettingsPage = lazy(
  () => import("@/features/organizations/pages/OrgSettingsPage"),
);
const OrgMembersPage = lazy(
  () => import("@/features/organizations/pages/OrgMembersPage"),
);
const ProjectSettingsPage = lazy(
  () => import("@/features/projects/pages/ProjectSettingsPage"),
);
const ProjectOverviewPage = lazy(
  () => import("@/features/projects/pages/ProjectOverviewPage"),
);
const NotFoundPage = lazy(() => import("@/app/NotFoundPage"));
const VerifyEmailPage = lazy(
  () => import("@/features/auth/pages/VerifyEmailPage"),
);

import { useAuthStore } from "@/features/auth/store/auth-store";
import { useEffect } from "react";

function App() {
  const checkSession = useAuthStore((state) => state.checkSession);

  useEffect(() => {
    checkSession();
  }, [checkSession]);

  return (
    <Suspense fallback={<PageLoader />}>
      <Routes>
        {/*
          GUEST ROUTES
          Only accessible if you are NOT logged in.
          If you are logged in, these redirect to "/"
        */}
        <Route element={<GuestRoute />}>
          {/* Public Routes */}
          <Route element={<AuthLayout />}>
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />
          </Route>
        </Route>

        {/*
          PUBLIC ROUTES
          Accessible by anyone (logged in or not).
          Used for: email verification (user clicks link from email)
        */}
        <Route element={<AuthLayout />}>
          <Route path="/verify-email" element={<VerifyEmailPage />} />
        </Route>

        {/*
          PROTECTED ROUTES
          Only accessible if you ARE logged in.
          If you are not logged in, these redirect to "/login"
        */}
        <Route element={<ProtectedRoute />}>
          <Route element={<AppLayout />}>
            {/* Global Scope */}
            <Route path="/" element={<DashboardPage />} />
            <Route path="/projects" element={<ProjectsPage />} />

            <Route element={<OrgGuard />}>
              <Route
                path="/settings"
                element={<OrgSettingsPage />}
              />
              <Route
                path="/members"
                element={<OrgMembersPage />}
              />
            </Route>

            {/* Project Scope */}
            <Route path="/projects/:projectId" element={<ProjectLayout />}>
              <Route index element={<ProjectOverviewPage />} />
              <Route path="tasks" element={<TasksPage />} />
              <Route path="gantt" element={<GanttPage />} />
              <Route path="resources" element={<ResourcesPage />} />
              <Route path="calendar" element={<CalendarPage />} />
              <Route path="reports" element={<ReportsPage />} />
              <Route path="settings" element={<ProjectSettingsPage />} />
            </Route>
            <Route path="*" element={<NotFoundPage />} />
          </Route>
        </Route>
      </Routes>
    </Suspense>
  );
}

export default App;
