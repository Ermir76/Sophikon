import type { Project } from "@/features/projects/types";
import { isValid, parseISO, startOfDay } from "date-fns";

export type ProjectBaseStatus = "active" | "completed" | "archived" | "unknown";
export type ProjectVisualState = ProjectBaseStatus | "at-risk";

interface ProjectVisualMeta {
  label: string;
  badgeClassName: string;
  valueClassName: string;
  filterClassName: string;
}

const PROJECT_VISUAL_META: Record<ProjectVisualState, ProjectVisualMeta> = {
  active: {
    label: "In Progress",
    badgeClassName: "border-primary/40 bg-primary/15 text-primary",
    valueClassName: "text-primary",
    filterClassName: "border-primary/40 bg-primary/12 text-primary hover:bg-primary/20",
  },
  completed: {
    label: "Completed",
    badgeClassName: "border-emerald-500/40 bg-emerald-500/15 text-emerald-600 dark:text-emerald-400",
    valueClassName: "text-emerald-600 dark:text-emerald-400",
    filterClassName:
      "border-emerald-500/40 bg-emerald-500/12 text-emerald-600 hover:bg-emerald-500/20 dark:text-emerald-400",
  },
  archived: {
    label: "Archived",
    badgeClassName: "border-muted-foreground/30 bg-muted/40 text-muted-foreground",
    valueClassName: "text-muted-foreground",
    filterClassName: "border-muted-foreground/30 bg-muted/40 text-muted-foreground hover:bg-muted/55",
  },
  unknown: {
    label: "Unknown",
    badgeClassName: "border-muted-foreground/30 bg-muted/30 text-muted-foreground",
    valueClassName: "text-muted-foreground",
    filterClassName: "border-muted-foreground/30 bg-muted/30 text-muted-foreground hover:bg-muted/45",
  },
  "at-risk": {
    label: "At Risk",
    badgeClassName: "border-destructive/50 bg-destructive/15 text-destructive",
    valueClassName: "text-destructive",
    filterClassName: "border-destructive/50 bg-destructive/15 text-destructive hover:bg-destructive/22",
  },
};

export function getProjectBaseStatus(project: Pick<Project, "status">): ProjectBaseStatus {
  const normalized = String(project.status ?? "").toLowerCase().trim();
  if (normalized === "active" || normalized === "in_progress" || normalized === "in progress") {
    return "active";
  }
  if (normalized === "completed" || normalized === "done" || normalized === "closed") {
    return "completed";
  }
  if (normalized === "archived" || normalized === "archive") {
    return "archived";
  }
  return "unknown";
}

function isPastFinishDate(finishDate: string, now: Date): boolean {
  const parsedDate = parseISO(finishDate);
  if (!isValid(parsedDate)) return false;
  return parsedDate < startOfDay(now);
}

export function isProjectAtRisk(
  project: Pick<Project, "status" | "finish_date">,
  now: Date,
): boolean {
  return (
    getProjectBaseStatus(project) === "active" &&
    !!project.finish_date &&
    isPastFinishDate(project.finish_date, now)
  );
}

export function getProjectVisualState(project: Project, now: Date): ProjectVisualState {
  const baseStatus = getProjectBaseStatus(project);
  if (isProjectAtRisk(project, now)) {
    return "at-risk";
  }
  return baseStatus;
}

export function getProjectVisualMeta(state: ProjectVisualState): ProjectVisualMeta {
  return PROJECT_VISUAL_META[state] ?? PROJECT_VISUAL_META.unknown;
}
