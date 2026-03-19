// Public API for the `tasks` feature
export { default as TasksPage } from './pages/TasksPage';
export { TaskDetailPanel } from './components/task-detail/TaskDetailPanel';

export { useTasks, useUpdateTask } from './hooks/useTasks';
export { useDependencies } from './hooks/useDependencies';
export { useAssignments } from './hooks/useAssignments';
export { useComments } from './hooks/useComments';
export { useCollapsedTasks } from './hooks/useCollapsedTasks';

export { TaskDependencyList } from './components/task-detail/TaskDependencyList';
export { TaskAssignmentList } from './components/task-detail/TaskAssignmentList';
export { AddDependencyDialog } from './components/task-detail/AddDependencyDialog';
export { EditDependencyDialog } from './components/task-detail/EditDependencyDialog';
export { AddAssignmentDialog } from './components/task-detail/AddAssignmentDialog';

export * from './types';
