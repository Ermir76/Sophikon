import { Suspense, lazy } from "react";
import { Route, Routes } from "react-router"; // Fixed import

import { AppLayout } from "./components/layout/AppLayout";
import { ProjectLayout } from "./components/layout/ProjectLayout";
import { ProtectedRoute } from "./components/ProtectedRoute";
import { GuestRoute } from "./components/GuestRoute";
import { OrgGuard } from "./components/OrgGuard";
import { PageLoader } from "./components/PageLoader";

// Lazy imports
const LoginPage = lazy(() => import("./pages/auth/LoginPage"));
const RegisterPage = lazy(() => import("./pages/auth/RegisterPage"));
const AuthLayout = lazy(() => import("./components/layout/AuthLayout"));
const DashboardPage = lazy(() => import("./pages/DashboardPage"));
const TasksPage = lazy(() => import("./pages/TasksPage"));
const GanttPage = lazy(() => import("./pages/GanttPage"));
const ResourcesPage = lazy(() => import("./pages/ResourcesPage"));
const CalendarPage = lazy(() => import("./pages/CalendarPage"));
const ProjectsPage = lazy(() => import("./pages/ProjectsPage"));
const ReportsPage = lazy(() => import("./pages/ReportsPage"));
const OrgSettingsPage = lazy(() => import("./pages/settings/OrgSettingsPage"));
const OrgMembersPage = lazy(() => import("./pages/settings/OrgMembersPage"));
const ProjectSettingsPage = lazy(() => import("./pages/ProjectSettingsPage"));
const CreateOrganizationPage = lazy(
  () => import("./pages/CreateOrganizationPage"),
);
const ProjectOverviewPage = lazy(() => import("./pages/ProjectOverviewPage"));
const NotFoundPage = lazy(() => import("./pages/NotFoundPage"));

import { useAuthStore } from "./store/auth-store";
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
          PROTECTED ROUTES
          Only accessible if you ARE logged in.
          If you are not logged in, these redirect to "/login"
        */}
        <Route element={<ProtectedRoute />}>
          <Route element={<AppLayout />}>
            {/* Global Scope */}
            <Route path="/" element={<DashboardPage />} />
            <Route path="/projects" element={<ProjectsPage />} />
            <Route
              path="/organizations/new"
              element={<CreateOrganizationPage />}
            />

            <Route element={<OrgGuard />}>
              <Route
                path="/organizations/settings"
                element={<OrgSettingsPage />}
              />
              <Route
                path="/organizations/members"
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
