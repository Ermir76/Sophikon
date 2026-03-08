// Public API for the `projects` feature
export { default as ProjectsPage } from './pages/ProjectsPage';
export { default as ProjectOverviewPage } from './pages/ProjectOverviewPage';
export { default as ProjectSettingsPage } from './pages/ProjectSettingsPage';
export { default as ProjectInvitationAcceptPage } from './pages/ProjectInvitationAcceptPage';

export { ProjectLayout } from './components/ProjectLayout';
export { CreateProjectDialog } from './components/CreateProjectDialog';
export { ProjectsTable } from './components/ProjectsTable';
export { ProjectsGrid } from './components/ProjectsGrid';

export { useProjects, projectKeys, useProject, useUpdateProject } from './hooks/useProjects';
export { useProjectDashboard } from './hooks/useProjectDashboard';
export {
  useAcceptProjectInvitation,
  useInviteProjectMember,
  useProjectInvitations,
  useProjectMembers,
  useRemoveProjectMember,
  useResendProjectInvitation,
  useRevokeProjectInvitation,
  useUpdateProjectMemberRole,
  projectMemberKeys,
} from './hooks/useProjectMembers';

export * from './types';
