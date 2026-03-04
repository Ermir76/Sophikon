// Public API for the `projects` feature
export { default as ProjectsPage } from './pages/ProjectsPage';
export { default as ProjectOverviewPage } from './pages/ProjectOverviewPage';
export { default as ProjectSettingsPage } from './pages/ProjectSettingsPage';

export { ProjectLayout } from './components/ProjectLayout';
export { CreateProjectDialog } from './components/CreateProjectDialog';
export { ProjectsTable } from './components/ProjectsTable';
export { ProjectsGrid } from './components/ProjectsGrid';

export { useProjects, projectKeys, useProject, useUpdateProject } from './hooks/useProjects';

export * from './types';
