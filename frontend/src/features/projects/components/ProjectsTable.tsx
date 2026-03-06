import { Link } from "react-router";
import { format, isValid, parseISO } from "date-fns";
import { MoreHorizontal } from "lucide-react";

import { Button } from "@/shared/ui/button";
import { Badge } from "@/shared/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/shared/ui/table";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/shared/ui/dropdown-menu";
import { getProjectVisualMeta, getProjectVisualState } from "@/features/projects/lib/project-status";

import type { Project } from "@/features/projects/types";

interface ProjectsTableProps {
  projects: Project[];
}

export function ProjectsTable({ projects }: ProjectsTableProps) {
  const now = new Date();
  const formatDate = (value?: string | null) => {
    if (!value) return "-";
    const parsed = parseISO(value);
    return isValid(parsed) ? format(parsed, "MMM d, yyyy") : "-";
  };

  return (
    <div className="rounded-lg border bg-card/70">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead className="sticky top-0 z-20 w-[42%] bg-card/95 backdrop-blur supports-[backdrop-filter]:bg-card/85">Project</TableHead>
            <TableHead className="sticky top-0 z-20 w-[16%] bg-card/95 backdrop-blur supports-[backdrop-filter]:bg-card/85">Status</TableHead>
            <TableHead className="sticky top-0 z-20 w-[16%] bg-card/95 backdrop-blur supports-[backdrop-filter]:bg-card/85">Due</TableHead>
            <TableHead className="sticky top-0 z-20 w-[16%] bg-card/95 backdrop-blur supports-[backdrop-filter]:bg-card/85">Updated</TableHead>
            <TableHead className="sticky top-0 z-20 w-[50px] bg-card/95 backdrop-blur supports-[backdrop-filter]:bg-card/85" />
          </TableRow>
        </TableHeader>
        <TableBody>
          {projects.map((project) => {
            const visualState = getProjectVisualState(project, now);
            const visualMeta = getProjectVisualMeta(visualState);

            return (
              <TableRow key={project.id} className="h-11">
                <TableCell className="min-w-0">
                  <Link
                    to={`/projects/${project.id}/tasks`}
                    className="font-medium hover:underline"
                  >
                    {project.name}
                  </Link>
                  <p className="mt-1 truncate text-xs text-muted-foreground">
                    {project.description || "No description provided."}
                  </p>
                </TableCell>
                <TableCell>
                  <Badge variant="outline" className={visualMeta.badgeClassName}>
                    {visualMeta.label}
                  </Badge>
                </TableCell>
                <TableCell className="text-muted-foreground text-sm whitespace-nowrap tabular-nums">
                  {formatDate(project.finish_date)}
                </TableCell>
                <TableCell className="text-muted-foreground text-sm whitespace-nowrap tabular-nums">
                  {formatDate(project.updated_at)}
                </TableCell>
                <TableCell>
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
                </TableCell>
              </TableRow>
            );
          })}
        </TableBody>
      </Table>
    </div>
  );
}
