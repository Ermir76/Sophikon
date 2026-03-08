import { Fragment } from "react";
import { Bell, CheckCheck } from "lucide-react";
import { formatDistanceToNow } from "date-fns";
import { Link, useLocation, useMatch } from "react-router";

import {
  useMarkAllNotificationsRead,
  useMarkNotificationRead,
  useNotifications,
  useNotificationSettings,
  useNotificationWebSocketStore,
  useUpdateNotificationSettings,
} from "@/features/notifications";
import { useProjectWebSocketStore } from "@/features/projects";
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
import { Button } from "@/shared/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuTrigger,
} from "@/shared/ui/dropdown-menu";
import { Separator } from "@/shared/ui/separator";
import { SidebarTrigger } from "@/shared/ui/sidebar";
import { Switch } from "@/shared/ui/switch";

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
  const notificationSocketUnreadCount = useNotificationWebSocketStore(
    (state) => state.unreadCount,
  );
  const notificationsQuery = useNotifications({ page: 1, per_page: 8 });
  const notificationSettingsQuery = useNotificationSettings();
  const markRead = useMarkNotificationRead();
  const markAllRead = useMarkAllNotificationsRead();
  const updateSettings = useUpdateNotificationSettings();
  const visibleUsers = projectSocketState?.users.slice(0, 4) ?? [];
  const extraUsers = Math.max((projectSocketState?.users.length ?? 0) - visibleUsers.length, 0);
  const unreadCount =
    notificationSocketUnreadCount ?? notificationsQuery.data?.unread_count ?? 0;

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
      <div className="ml-auto flex items-center gap-3">
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button
              type="button"
              variant="ghost"
              size="sm"
              className="relative h-9 w-9 p-0"
              aria-label="Notifications"
            >
              <Bell className="size-4" />
              {unreadCount > 0 ? (
                <span className="absolute right-0.5 top-0.5 inline-flex min-w-4 items-center justify-center rounded-full bg-destructive px-1 text-[10px] font-semibold text-white">
                  {unreadCount > 99 ? "99+" : unreadCount}
                </span>
              ) : null}
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-96 space-y-3 p-3">
            <div className="flex items-center justify-between">
              <p className="text-sm font-semibold">Notifications</p>
              <Button
                type="button"
                size="sm"
                variant="ghost"
                className="h-7 px-2 text-xs"
                disabled={markAllRead.isPending || unreadCount === 0}
                onClick={() => {
                  markAllRead.mutate();
                }}
              >
                <CheckCheck className="mr-1 size-3.5" />
                Mark all read
              </Button>
            </div>

            <div className="max-h-72 space-y-2 overflow-auto pr-1">
              {notificationsQuery.isLoading ? (
                <p className="text-xs text-muted-foreground">Loading notifications...</p>
              ) : notificationsQuery.isError ? (
                <p className="text-xs text-muted-foreground">Failed to load notifications.</p>
              ) : notificationsQuery.data?.items.length ? (
                notificationsQuery.data.items.map((notification) => (
                  <div
                    key={notification.id}
                    className="space-y-1 rounded-md border p-2"
                  >
                    <div className="flex items-start justify-between gap-2">
                      <p className="text-xs font-medium">{notification.title}</p>
                      {!notification.is_read ? (
                        <Button
                          type="button"
                          size="sm"
                          variant="ghost"
                          className="h-6 px-2 text-[11px]"
                          disabled={markRead.isPending}
                          onClick={() => {
                            markRead.mutate(notification.id);
                          }}
                        >
                          Read
                        </Button>
                      ) : null}
                    </div>
                    {notification.message ? (
                      <p className="text-xs text-muted-foreground">{notification.message}</p>
                    ) : null}
                    <p className="text-[11px] text-muted-foreground">
                      {formatDistanceToNow(new Date(notification.created_at), { addSuffix: true })}
                    </p>
                  </div>
                ))
              ) : (
                <p className="text-xs text-muted-foreground">No notifications yet.</p>
              )}
            </div>

            <div className="space-y-2 border-t pt-2">
              <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                Notification Settings
              </p>
              {notificationSettingsQuery.isLoading ? (
                <p className="text-xs text-muted-foreground">Loading settings...</p>
              ) : notificationSettingsQuery.isError || !notificationSettingsQuery.data ? (
                <p className="text-xs text-muted-foreground">Settings unavailable.</p>
              ) : (
                <div className="space-y-2">
                  <label className="flex items-center justify-between text-xs">
                    <span>Email task assigned</span>
                    <Switch
                      checked={notificationSettingsQuery.data.email_task_assigned}
                      disabled={updateSettings.isPending}
                      onCheckedChange={(checked) => {
                        updateSettings.mutate({ email_task_assigned: checked });
                      }}
                    />
                  </label>
                  <label className="flex items-center justify-between text-xs">
                    <span>Email mentioned</span>
                    <Switch
                      checked={notificationSettingsQuery.data.email_mentioned}
                      disabled={updateSettings.isPending}
                      onCheckedChange={(checked) => {
                        updateSettings.mutate({ email_mentioned: checked });
                      }}
                    />
                  </label>
                  <label className="flex items-center justify-between text-xs">
                    <span>Email deadline approaching</span>
                    <Switch
                      checked={notificationSettingsQuery.data.email_deadline_approaching}
                      disabled={updateSettings.isPending}
                      onCheckedChange={(checked) => {
                        updateSettings.mutate({ email_deadline_approaching: checked });
                      }}
                    />
                  </label>
                  <label className="flex items-center justify-between text-xs">
                    <span>Push enabled</span>
                    <Switch
                      checked={notificationSettingsQuery.data.push_enabled}
                      disabled={updateSettings.isPending}
                      onCheckedChange={(checked) => {
                        updateSettings.mutate({ push_enabled: checked });
                      }}
                    />
                  </label>
                </div>
              )}
            </div>
          </DropdownMenuContent>
        </DropdownMenu>
        {projectId ? (
          <>
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
          </>
        ) : null}
      </div>
    </header>
  );
}
