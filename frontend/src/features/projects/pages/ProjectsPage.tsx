import { useState } from "react";
import { Folder, LayoutGrid, List, Plus } from "lucide-react";

import { Button } from "@/shared/ui/button";
import { Badge } from "@/shared/ui/badge";
import { ToggleGroup, ToggleGroupItem } from "@/shared/ui/toggle-group";
import { useOrgStore } from "@/features/organizations";
import { useProjects } from "@/features/projects/hooks/useProjects";
import { QueryError } from "@/shared/components/QueryError";
import { CreateProjectDialog } from "@/features/projects/components/CreateProjectDialog";
import { ProjectsTable } from "@/features/projects/components/ProjectsTable";
import { ProjectsGrid } from "@/features/projects/components/ProjectsGrid";
import { getProjectBaseStatus, getProjectVisualMeta, isProjectAtRisk } from "@/features/projects/lib/project-status";
import { PageShell } from "@/shared/components/layout/PageShell";
import { PageHeader } from "@/shared/components/layout/PageHeader";
import { PageLoading } from "@/shared/components/state/PageLoading";
import { PageEmpty } from "@/shared/components/state/PageEmpty";
import { cn } from "@/shared/lib/utils";

type ViewMode = "table" | "grid";
type FilterMode = "all" | "active" | "completed" | "archived" | "at-risk";

export default function ProjectsPage() {
  const shellClassName = "h-full overflow-y-auto";
  const activeOrgId = useOrgStore((state) => state.activeOrgId);
  const {
    data: projectsData,
    isLoading: isLoadingProjects,
    isError: isProjectsError,
    refetch: refetchProjects,
  } = useProjects();
  const [createOpen, setCreateOpen] = useState(false);
  const [viewMode, setViewMode] = useState<ViewMode>("table");
  const [filterMode, setFilterMode] = useState<FilterMode>("all");

  if (!activeOrgId) {
    return (
      <PageShell className={shellClassName}>
        <PageEmpty
          title="Organization required"
          description="Please select an organization."
        />
      </PageShell>
    );
  }

  const projects = projectsData?.items || [];
  const today = new Date();
  const activeCount = projects.filter((project) => getProjectBaseStatus(project) === "active").length;
  const completedCount = projects.filter((project) => getProjectBaseStatus(project) === "completed").length;
  const archivedCount = projects.filter((project) => getProjectBaseStatus(project) === "archived").length;
  const atRiskCount = projects.filter((project) => isProjectAtRisk(project, today)).length;

  const filteredProjects = projects.filter((project) => {
    const baseStatus = getProjectBaseStatus(project);
    if (filterMode === "all") return true;
    if (filterMode === "at-risk") {
      return isProjectAtRisk(project, today);
    }
    return baseStatus === filterMode;
  });

  return (
    <PageShell className={shellClassName}>
      <PageHeader
        title="Projects"
        description="Scan portfolio status, focus risk, and jump into execution."
        action={
          <div className="flex items-center gap-2">
            <ToggleGroup
              type="single"
              value={viewMode}
              onValueChange={(value) => {
                if (value === "table" || value === "grid") setViewMode(value);
              }}
              variant="outline"
              size="sm"
              className="rounded-md border bg-card/70 p-0.5"
            >
              <ToggleGroupItem value="table" aria-label="Table view" className="size-7 p-0">
                <List className="size-4" />
              </ToggleGroupItem>
              <ToggleGroupItem value="grid" aria-label="Grid view" className="size-7 p-0">
                <LayoutGrid className="size-4" />
              </ToggleGroupItem>
            </ToggleGroup>
            <Button
              variant="default"
              size="sm"
              className="h-8 px-3 text-xs font-medium"
              onClick={() => setCreateOpen(true)}
            >
              <Plus className="mr-1.5 size-3.5" />
              New Project
            </Button>
            <CreateProjectDialog open={createOpen} onOpenChange={setCreateOpen} />
          </div>
        }
      />

      <div className="grid gap-2 sm:grid-cols-2 xl:grid-cols-4">
        <div className="rounded-md border bg-card/70 px-3 py-2">
          <p className="text-[10px] uppercase tracking-wide text-muted-foreground">Total</p>
          <p className="mt-1 text-lg font-semibold tabular-nums">{projects.length}</p>
        </div>
        <div className="rounded-md border bg-card/70 px-3 py-2">
          <p className="text-[10px] uppercase tracking-wide text-muted-foreground">Active</p>
          <p className={cn("mt-1 text-lg font-semibold tabular-nums", getProjectVisualMeta("active").valueClassName)}>
            {activeCount}
          </p>
        </div>
        <div className="rounded-md border bg-card/70 px-3 py-2">
          <p className="text-[10px] uppercase tracking-wide text-muted-foreground">At Risk</p>
          <p className={cn("mt-1 text-lg font-semibold tabular-nums", getProjectVisualMeta("at-risk").valueClassName)}>
            {atRiskCount}
          </p>
        </div>
        <div className="rounded-md border bg-card/70 px-3 py-2">
          <p className="text-[10px] uppercase tracking-wide text-muted-foreground">Completed</p>
          <p className={cn("mt-1 text-lg font-semibold tabular-nums", getProjectVisualMeta("completed").valueClassName)}>
            {completedCount}
          </p>
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-2">
        <Button
          size="sm"
          variant={filterMode === "all" ? "secondary" : "outline"}
          className={cn("h-7 text-xs", filterMode === "all" && "border-border bg-muted text-foreground")}
          onClick={() => setFilterMode("all")}
        >
          All
        </Button>
        <Button
          size="sm"
          variant="outline"
          className={cn(
            "h-7 text-xs",
            filterMode === "active" && getProjectVisualMeta("active").filterClassName,
          )}
          onClick={() => setFilterMode("active")}
        >
          Active
        </Button>
        <Button
          size="sm"
          variant="outline"
          className={cn(
            "h-7 text-xs",
            filterMode === "completed" && getProjectVisualMeta("completed").filterClassName,
          )}
          onClick={() => setFilterMode("completed")}
        >
          Completed
        </Button>
        <Button
          size="sm"
          variant="outline"
          className={cn(
            "h-7 text-xs",
            filterMode === "archived" && getProjectVisualMeta("archived").filterClassName,
          )}
          onClick={() => setFilterMode("archived")}
        >
          Archived
        </Button>
        <Button
          size="sm"
          variant="outline"
          className={cn(
            "h-7 text-xs",
            filterMode === "at-risk" && getProjectVisualMeta("at-risk").filterClassName,
          )}
          onClick={() => setFilterMode("at-risk")}
        >
          At Risk
        </Button>
        <Badge variant="outline" className="ml-auto h-7 px-2.5 text-[11px] text-muted-foreground">
          Archived: {archivedCount}
        </Badge>
      </div>

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
      ) : filteredProjects.length === 0 ? (
        <PageEmpty
          title="No projects in this filter"
          description="Try another status filter to view projects."
        />
      ) : viewMode === "table" ? (
        <div key="table" className="animate-in fade-in duration-200">
          <ProjectsTable projects={filteredProjects} />
        </div>
      ) : (
        <div key="grid" className="animate-in fade-in duration-200">
          <ProjectsGrid projects={filteredProjects} />
        </div>
      )}
    </PageShell>
  );
}
