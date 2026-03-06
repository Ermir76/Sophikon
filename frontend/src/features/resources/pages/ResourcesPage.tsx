import { useState } from "react";
import { useParams, Navigate } from "react-router";
import { Users, Plus, Trash2 } from "lucide-react";
import type { RowSelectionState } from "@tanstack/react-table";
import { Button } from "@/shared/ui/button";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/shared/ui/alert-dialog";
import { QueryError } from "@/shared/components/QueryError";
import { useResources, useDeleteResource, useBulkDeleteResources } from "@/features/resources/hooks/useResources";
import { useOverAllocations } from "@/features/resources/hooks/useUtilization";
import { format, addDays } from "date-fns";
import { ResourceTable } from "@/features/resources/components/ResourceTable";
import { ResourceDetailPanel } from "@/features/resources/components/ResourceDetailPanel";
import { CreateResourceDialog } from "@/features/resources/components/CreateResourceDialog";
import { toast } from "sonner";
import type { Resource } from "@/features/resources/types";

import { PageShell } from "@/shared/components/layout/PageShell";
import { PageHeader } from "@/shared/components/layout/PageHeader";
import { PageLoading } from "@/shared/components/state/PageLoading";
import { PageEmpty } from "@/shared/components/state/PageEmpty";

const EMPTY_RESOURCES: Resource[] = [];

export default function ResourcesPage() {
  const shellClassName = "h-full overflow-y-auto";
  const { projectId } = useParams<{ projectId: string }>();

  const [rowSelection, setRowSelection] = useState<RowSelectionState>({});
  const [selectedResourceId, setSelectedResourceId] = useState<string | null>(null);
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [showBulkDeleteConfirm, setShowBulkDeleteConfirm] = useState(false);

  const { data, isLoading, isError, refetch } = useResources(projectId);
  const deleteResource = useDeleteResource(projectId);
  const bulkDeleteResources = useBulkDeleteResources(projectId);

  // Get over-allocations for the next 30 days to show warnings
  const today = new Date();
  const startDate = format(today, "yyyy-MM-dd");
  const endDate = format(addDays(today, 30), "yyyy-MM-dd");
  const { data: overAllocations } = useOverAllocations(projectId, startDate, endDate);

  const overAllocatedIds = new Set(
    overAllocations?.items.map(item => item.resource_id) ?? []
  );

  const resources = data?.items ?? EMPTY_RESOURCES;
  const activeCount = resources.filter((resource) => resource.is_active).length;
  const inactiveCount = resources.filter((resource) => !resource.is_active).length;

  const selectedIds = Object.keys(rowSelection).filter((id) => rowSelection[id]);
  const selectionCount = selectedIds.length;

  const handleDeleteResource = async (resourceId: string) => {
    try {
      await deleteResource.mutateAsync(resourceId);
      toast.success("Resource deleted");
      if (selectedResourceId === resourceId) {
        setSelectedResourceId(null);
      }
      setRowSelection((prev) => {
        const next = { ...prev };
        delete next[resourceId];
        return next;
      });
    } catch {
      toast.error("Failed to delete resource");
    }
  };

  const handleBulkDelete = async () => {
    try {
      const result = await bulkDeleteResources.mutateAsync(selectedIds);
      toast.success(`${result.succeeded} resource(s) deleted`);
      setRowSelection({});
      setShowBulkDeleteConfirm(false);
    } catch {
      toast.error("Failed to delete resources");
      setShowBulkDeleteConfirm(false);
    }
  };

  if (!projectId) {
    return <Navigate to="/projects" replace />;
  }

  if (isError) {
    return (
      <PageShell className={shellClassName}>
        <QueryError
          message="Failed to load project resources."
          onRetry={() => refetch()}
        />
      </PageShell>
    );
  }

  return (
    <PageShell className={shellClassName}>
      {/* Header section */}
      <PageHeader
        title="Resources"
        description="Manage capacity, allocations, and workload health."
        action={
          <Button onClick={() => setIsCreateOpen(true)} size="sm" className="h-8 gap-1.5 px-3 text-xs">
            <Plus className="size-4" />
            Add Resource
          </Button>
        }
      />

      {!isLoading && resources.length > 0 ? (
        <div className="grid gap-2 sm:grid-cols-2 xl:grid-cols-4">
          <div className="rounded-md border bg-card/70 px-3 py-2">
            <p className="text-[10px] uppercase tracking-wide text-muted-foreground">Total</p>
            <p className="mt-1 text-lg font-semibold tabular-nums">{resources.length}</p>
          </div>
          <div className="rounded-md border bg-card/70 px-3 py-2">
            <p className="text-[10px] uppercase tracking-wide text-muted-foreground">Active</p>
            <p className="mt-1 text-lg font-semibold tabular-nums text-primary">{activeCount}</p>
          </div>
          <div className="rounded-md border bg-card/70 px-3 py-2">
            <p className="text-[10px] uppercase tracking-wide text-muted-foreground">Overallocated</p>
            <p className="mt-1 text-lg font-semibold tabular-nums text-destructive">{overAllocatedIds.size}</p>
          </div>
          <div className="rounded-md border bg-card/70 px-3 py-2">
            <p className="text-[10px] uppercase tracking-wide text-muted-foreground">Inactive</p>
            <p className="mt-1 text-lg font-semibold tabular-nums text-muted-foreground">{inactiveCount}</p>
          </div>
        </div>
      ) : null}

      {isLoading ? (
        <PageLoading />
      ) : resources.length === 0 ? (
        <PageEmpty
          icon={Users}
          title="No resources"
          description="You haven't added any resources to this project yet."
          action={
            <Button variant="outline" onClick={() => setIsCreateOpen(true)}>
              Add resource
            </Button>
          }
        />
      ) : (
        <div className="animate-in fade-in duration-200">
          <ResourceTable
            data={resources}
            rowSelection={rowSelection}
            setRowSelection={setRowSelection}
            onViewDetails={(id) => setSelectedResourceId(id)}
            onDelete={handleDeleteResource}
            isDeletePending={deleteResource.isPending}
            overAllocatedResourceIds={overAllocatedIds}
          />
        </div>
      )}

      {/* Floating bulk-action toolbar */}
      {selectionCount > 0 && (
        <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-50 animate-in slide-in-from-bottom-4 fade-in duration-200">
          <div className="flex items-center gap-3 rounded-xl border bg-card px-5 py-3 shadow-sm">
            <span className="text-sm font-semibold text-primary">
              {selectionCount} selected
            </span>
            <div className="h-5 w-px bg-border" />
            <Button
              variant="destructive"
              size="sm"
              className="h-8 text-xs font-medium gap-1.5"
              disabled={bulkDeleteResources.isPending}
              onClick={() => setShowBulkDeleteConfirm(true)}
            >
              <Trash2 className="size-3.5" />
              Delete
            </Button>
          </div>
        </div>
      )}

      {/* Bulk delete confirmation */}
      <AlertDialog open={showBulkDeleteConfirm} onOpenChange={setShowBulkDeleteConfirm}>
        <AlertDialogContent variant="destructive">
          <AlertDialogHeader>
            <AlertDialogTitle>Delete {selectionCount} resource{selectionCount !== 1 ? "s" : ""}?</AlertDialogTitle>
            <AlertDialogDescription>
              This will permanently delete the selected resource{selectionCount !== 1 ? "s" : ""}. This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              variant="destructive"
              disabled={bulkDeleteResources.isPending}
              onClick={handleBulkDelete}
            >
              {bulkDeleteResources.isPending ? "Deleting..." : "Delete"}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Detail Panel */}
      <ResourceDetailPanel
        projectId={projectId}
        resourceId={selectedResourceId}
        isOpen={!!selectedResourceId}
        onClose={() => setSelectedResourceId(null)}
        onDelete={handleDeleteResource}
        isDeletePending={deleteResource.isPending}
      />

      {/* Create Dialog */}
      <CreateResourceDialog
        projectId={projectId}
        isOpen={isCreateOpen}
        onClose={() => setIsCreateOpen(false)}
      />
    </PageShell>
  );
}
