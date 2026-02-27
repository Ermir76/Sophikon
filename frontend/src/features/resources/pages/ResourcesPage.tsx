import { useState } from "react";
import { useParams, Navigate } from "react-router";
import { Loader2, Users, Plus, Trash2 } from "lucide-react";
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
import { ResourceTable } from "@/features/resources/components/ResourceTable";
import { ResourceDetailPanel } from "@/features/resources/components/ResourceDetailPanel";
import { CreateResourceDialog } from "@/features/resources/components/CreateResourceDialog";
import { toast } from "sonner";
import type { Resource } from "@/features/resources/types";

const EMPTY_RESOURCES: Resource[] = [];

export default function ResourcesPage() {
  const { projectId } = useParams<{ projectId: string }>();

  const [rowSelection, setRowSelection] = useState<RowSelectionState>({});
  const [selectedResourceId, setSelectedResourceId] = useState<string | null>(null);
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [showBulkDeleteConfirm, setShowBulkDeleteConfirm] = useState(false);

  const { data, isLoading, isError, refetch } = useResources(projectId);
  const deleteResource = useDeleteResource(projectId);
  const bulkDeleteResources = useBulkDeleteResources(projectId);

  const resources = data?.items ?? EMPTY_RESOURCES;

  const selectedIds = Object.keys(rowSelection).filter((id) => rowSelection[id]);
  const selectionCount = selectedIds.length;

  const handleDeleteResource = (resourceId: string) => {
    deleteResource.mutate(resourceId, {
      onSuccess: () => {
        toast.success("Resource deleted");
        if (selectedResourceId === resourceId) {
          setSelectedResourceId(null);
        }
        setRowSelection((prev) => {
          const next = { ...prev };
          delete next[resourceId];
          return next;
        });
      },
      onError: () => toast.error("Failed to delete resource"),
    });
  };

  const handleBulkDelete = () => {
    bulkDeleteResources.mutate(selectedIds, {
      onSuccess: (result) => {
        toast.success(`${result.succeeded} resource(s) deleted`);
        setRowSelection({});
        setShowBulkDeleteConfirm(false);
      },
      onError: () => {
        toast.error("Failed to delete resources");
        setShowBulkDeleteConfirm(false);
      },
    });
  };

  if (!projectId) {
    return <Navigate to="/projects" replace />;
  }

  if (isError) {
    return (
      <div className="p-6">
        <QueryError
          message="Failed to load project resources."
          onRetry={() => refetch()}
        />
      </div>
    );
  }

  return (
    <div className="space-y-6 p-6">
      {/* Header section */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-2xl font-medium">Resources</h3>
          <p className="text-sm text-muted-foreground">
            Allocate team members and manage resource utilization.
          </p>
        </div>
        <Button onClick={() => setIsCreateOpen(true)} size="sm" className="gap-1.5">
          <Plus className="size-4" />
          Add Resource
        </Button>
      </div>

      {isLoading ? (
        <div className="flex justify-center p-8">
          <Loader2 className="size-8 animate-spin text-muted-foreground" />
        </div>
      ) : resources.length === 0 ? (
        <div className="flex flex-col items-center justify-center rounded-md border border-dashed p-8 text-center animate-in fade-in-50">
          <div className="mx-auto flex size-12 items-center justify-center rounded-full bg-accent">
            <Users className="size-6 text-muted-foreground" />
          </div>
          <h3 className="mt-4 text-lg font-semibold">No resources</h3>
          <p className="mb-4 mt-2 text-sm text-muted-foreground">
            You haven't added any resources to this project yet.
          </p>
          <Button variant="outline" onClick={() => setIsCreateOpen(true)}>
            Add resource
          </Button>
        </div>
      ) : (
        <div className="animate-in fade-in duration-200">
          <ResourceTable
            data={resources}
            rowSelection={rowSelection}
            setRowSelection={setRowSelection}
            onViewDetails={(id) => setSelectedResourceId(id)}
            onDelete={handleDeleteResource}
            isDeletePending={deleteResource.isPending}
          />
        </div>
      )}

      {/* Floating bulk-action toolbar */}
      {selectionCount > 0 && (
        <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-50 animate-in slide-in-from-bottom-4 fade-in duration-200">
          <div className="flex items-center gap-3 rounded-xl border border-primary/30 bg-primary/10 backdrop-blur-xl px-5 py-3 shadow-2xl">
            <span className="text-sm font-semibold text-primary">
              {selectionCount} selected
            </span>
            <div className="h-5 w-px bg-primary/20" />
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
              {bulkDeleteResources.isPending ? "Deleting…" : "Delete"}
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
    </div>
  );
}
