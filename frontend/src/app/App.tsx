import { Suspense, lazy } from "react";
import { Route, Routes } from "react-router";

import { AppLayout } from "@/shared/layout/AppLayout";
import { ProjectLayout } from "@/features/projects";
import { ProtectedRoute } from "@/app/routing/ProtectedRoute";
import { GuestRoute } from "@/app/routing/GuestRoute";
import { OrgGuard } from "@/app/routing/OrgGuard";
import { PageLoader } from "@/shared/components/PageLoader";

// Lazy imports
const LoginPage = lazy(() => import("@/features/auth").then(m => ({ default: m.LoginPage })));
const RegisterPage = lazy(() => import("@/features/auth").then(m => ({ default: m.RegisterPage })));
const ForgotPasswordPage = lazy(
  () => import("@/features/auth").then(m => ({ default: m.ForgotPasswordPage }))
);
const ResetPasswordPage = lazy(
  () => import("@/features/auth").then(m => ({ default: m.ResetPasswordPage }))
);
const ProfilePage = lazy(() => import("@/features/auth").then(m => ({ default: m.ProfilePage })));
const AuthLayout = lazy(() => import("@/shared/layout/AuthLayout"));
const DashboardPage = lazy(
  () => import("@/features/dashboard").then(m => ({ default: m.DashboardPage }))
);
const TasksPage = lazy(() => import("@/features/tasks").then(m => ({ default: m.TasksPage })));
const GanttPage = lazy(() => import("@/features/gantt").then(m => ({ default: m.GanttPage })));
const KanbanPage = lazy(() => import("@/features/kanban").then(m => ({ default: m.KanbanPage })));
const ResourcesPage = lazy(
  () => import("@/features/resources").then(m => ({ default: m.ResourcesPage }))
);
const UtilizationPage = lazy(
  () => import("@/features/resources").then(m => ({ default: m.UtilizationPage }))
);
const CalendarPage = lazy(
  () => import("@/features/calendar").then(m => ({ default: m.CalendarPage }))
);
const ProjectsPage = lazy(
  () => import("@/features/projects").then(m => ({ default: m.ProjectsPage }))
);
const ReportsPage = lazy(
  () => import("@/features/reports").then(m => ({ default: m.ReportsPage }))
);
const OrgSettingsPage = lazy(
  () => import("@/features/organizations").then(m => ({ default: m.OrgSettingsPage }))
);
const OrgMembersPage = lazy(
  () => import("@/features/organizations").then(m => ({ default: m.OrgMembersPage }))
);
const ProjectSettingsPage = lazy(
  () => import("@/features/projects").then(m => ({ default: m.ProjectSettingsPage }))
);
const ProjectInvitationAcceptPage = lazy(
  () => import("@/features/projects").then(m => ({ default: m.ProjectInvitationAcceptPage }))
);
const ProjectOverviewPage = lazy(
  () => import("@/features/projects").then(m => ({ default: m.ProjectOverviewPage }))
);
const NotFoundPage = lazy(() => import("@/app/NotFoundPage"));
const VerifyEmailPage = lazy(
  () => import("@/features/auth").then(m => ({ default: m.VerifyEmailPage }))
);

import { useAuthStore } from "@/features/auth";
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
          <Route path="/forgot-password" element={<ForgotPasswordPage />} />
          <Route path="/reset-password" element={<ResetPasswordPage />} />
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
            <Route path="/project-invitations/accept" element={<ProjectInvitationAcceptPage />} />
            <Route path="/profile" element={<ProfilePage />} />

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
              <Route path="kanban" element={<KanbanPage />} />
              <Route path="resources" element={<ResourcesPage />} />
              <Route path="utilization" element={<UtilizationPage />} />
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
