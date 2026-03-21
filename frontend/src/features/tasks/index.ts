// Public API for the `tasks` feature
export { default as TasksPage } from './pages/TasksPage';
export { TaskDetailPanel } from './components/task-detail/TaskDetailPanel';

export { taskKeys, useTasks, useCreateTask, useUpdateTask, useDeleteTask } from './hooks/useTasks';
export { dependencyKeys, useDependencies, useCreateDependency, useDeleteDependency } from './hooks/useDependencies';
export { assignmentKeys, useAssignments } from './hooks/useAssignments';
export { commentKeys, useComments } from './hooks/useComments';
export { useCollapsedTasks } from './hooks/useCollapsedTasks';

export { TaskDependencyList } from './components/task-detail/TaskDependencyList';
export { TaskAssignmentList } from './components/task-detail/TaskAssignmentList';
export { AddDependencyDialog } from './components/task-detail/AddDependencyDialog';
export { EditDependencyDialog } from './components/task-detail/EditDependencyDialog';
export { AddAssignmentDialog } from './components/task-detail/AddAssignmentDialog';

export * from './types';
