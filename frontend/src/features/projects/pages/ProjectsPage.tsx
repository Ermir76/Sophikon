import { useState } from "react";
import { Loader2, Folder, LayoutGrid, List } from "lucide-react";

import { Button } from "@/shared/ui/button";
import { useOrgStore } from "@/features/organizations/store/org-store";
import { useProjects } from "@/features/projects/hooks/useProjects";
import { QueryError } from "@/shared/components/QueryError";
import { CreateProjectDialog } from "@/features/projects/components/CreateProjectDialog";
import { ProjectsTable } from "@/features/projects/components/ProjectsTable";
import { ProjectsGrid } from "@/features/projects/components/ProjectsGrid";

type ViewMode = "table" | "grid";

export default function ProjectsPage() {
  const activeOrgId = useOrgStore((state) => state.activeOrgId);
  const {
    data: projectsData,
    isLoading: isLoadingProjects,
    isError: isProjectsError,
    refetch: refetchProjects,
  } = useProjects();
  const [createOpen, setCreateOpen] = useState(false);
  const [viewMode, setViewMode] = useState<ViewMode>("table");

  if (!activeOrgId) {
    return <div className="p-4">Please select an organization.</div>;
  }

  const projects = projectsData?.items || [];

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-2xl font-medium">Projects</h3>
          <p className="text-sm text-muted-foreground">
            Manage your organization's projects.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <div className="view-toggle flex items-center gap-1 rounded-lg p-1">
            <Button
              variant="ghost"
              size="sm"
              className={`size-8 p-0 ${viewMode === "table" ? "bg-muted text-foreground" : "text-muted-foreground"}`}
              onClick={() => setViewMode("table")}
            >
              <List className="size-4" />
            </Button>
            <Button
              variant="ghost"
              size="sm"
              className={`size-8 p-0 ${viewMode === "grid" ? "bg-muted text-foreground" : "text-muted-foreground"}`}
              onClick={() => setViewMode("grid")}
            >
              <LayoutGrid className="size-4" />
            </Button>
          </div>
          <CreateProjectDialog open={createOpen} onOpenChange={setCreateOpen} />
        </div>
      </div>

      {isProjectsError ? (
        <QueryError
          message="Failed to load projects."
          onRetry={() => refetchProjects()}
        />
      ) : isLoadingProjects ? (
        <div className="flex justify-center p-8">
          <Loader2 className="size-8 animate-spin text-muted-foreground" />
        </div>
      ) : projects.length === 0 ? (
        <div className="flex flex-col items-center justify-center rounded-md border border-dashed p-8 text-center animate-in fade-in-50">
          <div className="mx-auto flex size-12 items-center justify-center rounded-full bg-accent">
            <Folder className="size-6 text-muted-foreground" />
          </div>
          <h3 className="mt-4 text-lg font-semibold">No projects</h3>
          <p className="mb-4 mt-2 text-sm text-muted-foreground">
            You haven't created any projects yet.
          </p>
          <Button variant="outline" onClick={() => setCreateOpen(true)}>
            Create your first project
          </Button>
        </div>
      ) : viewMode === "table" ? (
        <div key="table" className="animate-in fade-in duration-200">
          <ProjectsTable projects={projects} />
        </div>
      ) : (
        <div key="grid" className="animate-in fade-in duration-200">
          <ProjectsGrid projects={projects} />
        </div>
      )}
    </div>
  );
}
