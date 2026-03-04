import { useState } from "react";
import { Folder, LayoutGrid, List, Plus } from "lucide-react";

import { Button } from "@/shared/ui/button";
import { useOrgStore } from "@/features/organizations";
import { useProjects } from "@/features/projects/hooks/useProjects";
import { QueryError } from "@/shared/components/QueryError";
import { CreateProjectDialog } from "@/features/projects/components/CreateProjectDialog";
import { ProjectsTable } from "@/features/projects/components/ProjectsTable";
import { ProjectsGrid } from "@/features/projects/components/ProjectsGrid";
import { PageShell } from "@/shared/components/layout/PageShell";
import { PageHeader } from "@/shared/components/layout/PageHeader";
import { PageLoading } from "@/shared/components/state/PageLoading";
import { PageEmpty } from "@/shared/components/state/PageEmpty";

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
    return (
      <PageShell>
        <PageEmpty
          title="Organization required"
          description="Please select an organization."
        />
      </PageShell>
    );
  }

  const projects = projectsData?.items || [];

  return (
    <PageShell>
      <PageHeader
        title="Projects"
        description="Manage your organization's projects."
        action={
          <>
            <div className="flex items-center gap-1 rounded-lg p-1">
              <Button
                variant="ghost"
                size="sm"
                className={`ui-subtle-outline size-8 p-0 ${viewMode === "table" ? "bg-muted text-foreground" : "text-muted-foreground"}`}
                onClick={() => setViewMode("table")}
              >
                <List className="size-4" />
              </Button>
              <Button
                variant="ghost"
                size="sm"
                className={`ui-subtle-outline size-8 p-0 ${viewMode === "grid" ? "bg-muted text-foreground" : "text-muted-foreground"}`}
                onClick={() => setViewMode("grid")}
              >
                <LayoutGrid className="size-4" />
              </Button>
            </div>
            <Button
              variant="ghost"
              size="sm"
              className="ui-subtle-outline h-8 px-3 text-primary-foreground"
              onClick={() => setCreateOpen(true)}
            >
              <Plus className="mr-2 size-4" />
              New Project
            </Button>
            <CreateProjectDialog open={createOpen} onOpenChange={setCreateOpen} />
          </>
        }
      />

      {isProjectsError ? (
        <QueryError
          message="Failed to load projects."
          onRetry={() => refetchProjects()}
        />
      ) : isLoadingProjects ? (
        <PageLoading />
      ) : projects.length === 0 ? (
        <PageEmpty
          icon={Folder}
          title="No projects"
          description="You haven't created any projects yet."
          action={
            <Button variant="outline" onClick={() => setCreateOpen(true)}>
              Create your first project
            </Button>
          }
        />
      ) : viewMode === "table" ? (
        <div key="table" className="animate-in fade-in duration-200">
          <ProjectsTable projects={projects} />
        </div>
      ) : (
        <div key="grid" className="animate-in fade-in duration-200">
          <ProjectsGrid projects={projects} />
        </div>
      )}
    </PageShell>
  );
}
