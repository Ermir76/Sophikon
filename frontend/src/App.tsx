import { Route, Routes } from "react-router";

import { AppLayout } from "./components/layout/AppLayout";
import { ProjectLayout } from "./components/layout/ProjectLayout";
import { ProtectedRoute } from "./components/ProtectedRoute";
import { GuestRoute } from "./components/GuestRoute";

import LoginPage from "./pages/auth/LoginPage";
import RegisterPage from "./pages/auth/RegisterPage";
import DashboardPage from "./pages/DashboardPage";
import TasksPage from "./pages/TasksPage";
import GanttPage from "./pages/GanttPage";
import ResourcesPage from "./pages/ResourcesPage";
import CalendarPage from "./pages/CalendarPage";
import ProjectsPage from "./pages/ProjectsPage";
import ReportsPage from "./pages/ReportsPage";
import OrgSettingsPage from "./pages/settings/OrgSettingsPage";
import OrgMembersPage from "./pages/settings/OrgMembersPage";
import ProjectSettingsPage from "./pages/ProjectSettingsPage";

function App() {
  return (
    <Routes>
      {/* 
        GUEST ROUTES 
        Only accessible if you are NOT logged in.
        If you are logged in, these redirect to "/" 
      */}
      <Route element={<GuestRoute />}>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
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
            element={<div className="p-4">Create Organization (TODO)</div>}
          />

          <Route path="/organizations/settings" element={<OrgSettingsPage />} />
          <Route path="/organizations/members" element={<OrgMembersPage />} />

          {/* Project Scope */}
          <Route path="/projects/:projectId" element={<ProjectLayout />}>
            <Route
              index
              element={<div className="p-4">Project Overview (TODO)</div>}
            />
            <Route path="tasks" element={<TasksPage />} />
            <Route path="gantt" element={<GanttPage />} />
            <Route path="resources" element={<ResourcesPage />} />
            <Route path="calendar" element={<CalendarPage />} />
            <Route path="reports" element={<ReportsPage />} />
            <Route path="settings" element={<ProjectSettingsPage />} />
          </Route>
        </Route>
      </Route>
    </Routes>
  );
}

export default App;
