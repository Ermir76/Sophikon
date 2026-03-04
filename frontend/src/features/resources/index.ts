// Public API for the `resources` feature
export { default as ResourcesPage } from './pages/ResourcesPage';
export { default as UtilizationPage } from './pages/UtilizationPage';

export { useResources } from './hooks/useResources';
export { useProjectUtilization, useResourceUtilization, useOverAllocations } from './hooks/useUtilization';

export { ResourceTable } from './components/ResourceTable';
export { ResourceDetailPanel } from './components/ResourceDetailPanel';
export { CreateResourceDialog } from './components/CreateResourceDialog';
export { OverAllocationBadge } from './components/OverAllocationBadge';

export * from './types';
