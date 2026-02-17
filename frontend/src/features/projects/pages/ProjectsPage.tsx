import { useState } from "react";
import { Link } from "react-router";
import { format } from "date-fns";
import { MoreHorizontal, Loader2, Folder } from "lucide-react";

import { Button } from "@/shared/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/shared/ui/card";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/shared/ui/dropdown-menu";

import { useOrgStore } from "@/features/organizations/store/org-store";
import { useProjects } from "@/features/projects/hooks/useProjects";
import { QueryError } from "@/shared/components/QueryError";
import { CreateProjectDialog } from "@/features/projects/components/CreateProjectDialog";

export default function ProjectsPage() {
  const activeOrgId = useOrgStore((state) => state.activeOrgId);
  const {
    data: projectsData,
    isLoading: isLoadingProjects,
    isError: isProjectsError,
    refetch: refetchProjects,
  } = useProjects();
  const [createOpen, setCreateOpen] = useState(false);

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
        <CreateProjectDialog open={createOpen} onOpenChange={setCreateOpen} />
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
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {projects.map((project) => (
            <Card
              key={project.id}
              className="hover:bg-muted/50 transition-colors"
            >
              <CardHeader className="flex flex-row items-start justify-between space-y-0 pb-2">
                <CardTitle className="text-base font-medium">
                  <Link
                    to={`/projects/${project.id}/tasks`}
                    className="hover:underline"
                  >
                    {project.name}
                  </Link>
                </CardTitle>
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button variant="ghost" className="size-8 p-0">
                      <span className="sr-only">Open menu</span>
                      <MoreHorizontal className="size-4" />
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end">
                    <DropdownMenuItem asChild>
                      <Link to={`/projects/${project.id}/settings`}>
                        Settings
                      </Link>
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              </CardHeader>
              <CardContent>
                <div className="text-sm text-muted-foreground line-clamp-2 min-h-[40px]">
                  {project.description || "No description provided."}
                </div>
                <div className="mt-4 text-xs text-muted-foreground">
                  Updated {format(new Date(project.updated_at), "MMM d, yyyy")}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
