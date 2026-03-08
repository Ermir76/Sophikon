import { Fragment } from "react";
import { Link, useLocation, useMatch } from "react-router";

import { useProjectWebSocketStore } from "@/features/projects/store/websocket-store";
import {
  Avatar,
  AvatarFallback,
  AvatarGroup,
  AvatarGroupCount,
  AvatarImage,
} from "@/shared/ui/avatar";
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from "@/shared/ui/breadcrumb";
import { Separator } from "@/shared/ui/separator";
import { SidebarTrigger } from "@/shared/ui/sidebar";

const segmentLabels: Record<string, string> = {
  tasks: "Tasks",
  gantt: "Gantt",
  resources: "Resources",
  utilization: "Utilization",
  calendar: "Calendar",
  reports: "Reports",
};

export function AppHeader() {
  const location = useLocation();
  const projectMatch = useMatch("/projects/:projectId/*") ?? useMatch("/projects/:projectId");
  const segments = location.pathname.split("/").filter(Boolean);
  const projectId = projectMatch?.params.projectId ?? null;
  const projectSocketState = useProjectWebSocketStore((state) =>
    projectId ? state.projects[projectId] : undefined,
  );
  const visibleUsers = projectSocketState?.users.slice(0, 4) ?? [];
  const extraUsers = Math.max((projectSocketState?.users.length ?? 0) - visibleUsers.length, 0);

  const isUUID = (str: string) =>
    /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(str);

  const getLabel = (segment: string, index: number, allSegments: string[]) => {
    if (segmentLabels[segment]) {
      return segmentLabels[segment];
    }
    if (isUUID(segment)) {
      const prev = allSegments[index - 1];
      if (prev === "projects") return "Project";
      return "Details";
    }
    return segment.charAt(0).toUpperCase() + segment.slice(1);
  };

  const getInitials = (name?: string | null) =>
    (name ?? "U")
      .split(/\s+/)
      .filter(Boolean)
      .slice(0, 2)
      .map((part) => part[0]?.toUpperCase() ?? "")
      .join("");

  return (
    <header className="flex h-16 shrink-0 items-center gap-2 border-b px-4">
      <SidebarTrigger className="-ml-1" />
      <Separator orientation="vertical" className="mr-2 h-4" />
      <Breadcrumb>
        <BreadcrumbList>
          {/* If there are segments, the first item is always Dashboard (link to /) */}
          {segments.length > 0 ? (
            <Fragment>
              <BreadcrumbItem className="hidden md:block">
                <BreadcrumbLink asChild>
                  <Link to="/">Dashboard</Link>
                </BreadcrumbLink>
              </BreadcrumbItem>
              <BreadcrumbSeparator className="hidden md:block" />
            </Fragment>
          ) : (
            // If we are at root /, just show "Dashboard" as current page
            <BreadcrumbItem>
              <BreadcrumbPage>Dashboard</BreadcrumbPage>
            </BreadcrumbItem>
          )}

          {segments.map((segment, index) => {
            const isLast = index === segments.length - 1;
            const path = `/${segments.slice(0, index + 1).join("/")}`;
            const label = getLabel(segment, index, segments);

            return (
              <Fragment key={path}>
                <BreadcrumbItem>
                  {isLast ? (
                    <BreadcrumbPage>{label}</BreadcrumbPage>
                  ) : (
                    <BreadcrumbLink asChild>
                      <Link to={path}>{label}</Link>
                    </BreadcrumbLink>
                  )}
                </BreadcrumbItem>
                {!isLast && <BreadcrumbSeparator className="hidden md:block" />}
              </Fragment>
            );
          })}
        </BreadcrumbList>
      </Breadcrumb>
      {projectId ? (
        <div className="ml-auto flex items-center gap-3">
          <span className="text-xs text-muted-foreground">
            {projectSocketState?.status === "connected"
              ? "Live"
              : projectSocketState?.status === "reconnecting"
                ? "Reconnecting"
                : projectSocketState?.status === "connecting"
                  ? "Connecting"
                  : "Offline"}
          </span>
          <AvatarGroup>
            {visibleUsers.map((user) => (
              <Avatar key={user.id} size="sm" title={user.full_name ?? "Connected user"}>
                {user.avatar_url ? (
                  <AvatarImage src={user.avatar_url} alt={user.full_name ?? "Connected user"} />
                ) : null}
                <AvatarFallback>{getInitials(user.full_name)}</AvatarFallback>
              </Avatar>
            ))}
            {extraUsers > 0 ? <AvatarGroupCount>+{extraUsers}</AvatarGroupCount> : null}
          </AvatarGroup>
        </div>
      ) : null}
    </header>
  );
}
