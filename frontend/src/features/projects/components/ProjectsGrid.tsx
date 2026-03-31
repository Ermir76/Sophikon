import { Link } from "react-router";
import { format, isValid, parseISO } from "date-fns";
import { MoreHorizontal } from "lucide-react";

import { Button } from "@/shared/ui/button";
import { Badge } from "@/shared/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/shared/ui/card";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/shared/ui/dropdown-menu";
import { getProjectVisualMeta, getProjectVisualState } from "@/features/projects/lib/project-status";

import type { Project } from "@/features/projects/types";

interface ProjectsGridProps {
  projects: Project[];
}

export function ProjectsGrid({ projects }: ProjectsGridProps) {
  const now = new Date();
  const formatDate = (value?: string | null) => {
    if (!value) return "-";
    const parsed = parseISO(value);
    return isValid(parsed) ? format(parsed, "MMM d, yyyy") : "-";
  };

  return (
    <div className="projects-grid grid gap-3 md:grid-cols-2 lg:grid-cols-3">
      {projects.map((project) => {
        const visualState = getProjectVisualState(project, now);
        const visualMeta = getProjectVisualMeta(visualState);

        return (
          <Card key={project.id} className="gap-3 bg-card/70 py-4 transition-colors hover:bg-card">
            <CardHeader className="flex flex-row items-start justify-between space-y-0 pb-2">
              <CardTitle className="text-base font-medium">
                <Link
                  to={`/projects/${project.id}`}
                  className="hover:underline"
                >
                  {project.name}
                </Link>
              </CardTitle>
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="ghost" className="size-7 p-0">
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
              <div className="mb-3">
                <Badge variant="outline" className={visualMeta.badgeClassName}>
                  {visualMeta.label}
                </Badge>
              </div>
              <div className="text-sm text-muted-foreground line-clamp-2 min-h-[40px]">
                {project.description || "No description provided."}
              </div>
              <div className="mt-4 flex items-center justify-between text-xs text-muted-foreground">
                <span>
                  Due {formatDate(project.finish_date)}
                </span>
                <span>Updated {formatDate(project.updated_at)}</span>
              </div>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}
