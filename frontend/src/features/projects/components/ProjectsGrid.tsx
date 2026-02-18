import { Link } from "react-router";
import { format } from "date-fns";
import { MoreHorizontal } from "lucide-react";

import { Button } from "@/shared/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/shared/ui/card";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/shared/ui/dropdown-menu";

import type { Project } from "@/features/projects/types";

interface ProjectsGridProps {
  projects: Project[];
}

export function ProjectsGrid({ projects }: ProjectsGridProps) {
  return (
    <div className="projects-grid grid gap-4 md:grid-cols-2 lg:grid-cols-3">
      {projects.map((project) => (
        <Card key={project.id} className="transition-colors hover:bg-muted/50">
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
  );
}
