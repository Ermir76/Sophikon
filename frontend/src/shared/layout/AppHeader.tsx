import { Fragment, useState } from "react";
import { Bell, CheckCheck } from "lucide-react";
import { formatDistanceToNow } from "date-fns";
import { Link, useLocation, useMatch, useNavigate } from "react-router";
import { toast } from "sonner";

import {
  useMarkAllNotificationsRead,
  useMarkNotificationRead,
  useNotifications,
  notificationKeys,
  useNotificationWebSocketStore,
} from "@/features/notifications";
import type { NotificationItem } from "@/features/notifications";
import { useAcceptProjectInvitation, useProjectWebSocketStore } from "@/features/projects";
import { getErrorMessage } from "@/shared/lib/errors";
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
import { useQueryClient } from "@tanstack/react-query";

const segmentLabels: Record<string, string> = {
  tasks: "Tasks",
  gantt: "Gantt",
  resources: "Resources",
  utilization: "Utilization",
  calendar: "Calendar",
  reports: "Reports",
};

export function AppHeader() {
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const location = useLocation();
  const projectWildcardMatch = useMatch("/projects/:projectId/*");
  const projectRootMatch = useMatch("/projects/:projectId");
  const projectMatch = projectWildcardMatch ?? projectRootMatch;
  const segments = location.pathname.split("/").filter(Boolean);
  const projectId = projectMatch?.params.projectId ?? null;
  const projectSocketState = useProjectWebSocketStore((state) =>
    projectId ? state.projects[projectId] : undefined,
  );
  const notificationSocketUnreadCount = useNotificationWebSocketStore(
    (state) => state.unreadCount,
  );
  const notificationsQuery = useNotifications({ page: 1, per_page: 8 });
  const markRead = useMarkNotificationRead();
  const markAllRead = useMarkAllNotificationsRead();
  const acceptInvitation = useAcceptProjectInvitation();
  const [acceptingNotificationId, setAcceptingNotificationId] = useState<string | null>(null);
  const [acceptErrors, setAcceptErrors] = useState<Record<string, string>>({});
  const [hiddenNotificationIds, setHiddenNotificationIds] = useState<Record<string, true>>({});
  const visibleUsers = projectSocketState?.users.slice(0, 4) ?? [];
  const extraUsers = Math.max((projectSocketState?.users.length ?? 0) - visibleUsers.length, 0);
  const isProjectConnected = projectSocketState?.status === "connected";
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

  const getNotificationTarget = (notification: NotificationItem) => {
    if (
      notification.type === "invitation_received"
      && notification.entity_type === "project_invitation"
      && notification.entity_id
    ) {
      return `/project-invitations/accept?invitation_id=${notification.entity_id}`;
    }

    return null;
  };

  const clearAcceptError = (notificationId: string) => {
    setAcceptErrors((current) => {
      if (!(notificationId in current)) {
        return current;
      }

      const next = { ...current };
      delete next[notificationId];
      return next;
    });
  };

  const hideNotification = (notificationId: string) => {
    setHiddenNotificationIds((current) => {
      if (current[notificationId]) {
        return current;
      }

      return {
        ...current,
        [notificationId]: true,
      };
    });
  };

  const isTerminalInvitationError = (message: string) => {
    const normalized = message.toLowerCase();
    return (
      normalized.includes("already accepted")
      || normalized.includes("expired")
      || normalized.includes("invalid")
      || normalized.includes("revoked")
    );
  };

  const openNotificationTarget = (
    notification: NotificationItem,
    target: string,
    state?: Record<string, unknown>,
  ) => {
    clearAcceptError(notification.id);
    if (!notification.is_read) {
      markRead.mutate(notification.id);
    }
    navigate(target, state ? { state } : undefined);
  };

  const acceptInvitationFromNotification = async (
    notification: NotificationItem,
    target: string,
  ) => {
    if (
      notification.type !== "invitation_received"
      || notification.entity_type !== "project_invitation"
      || !notification.entity_id
    ) {
      return;
    }

    setAcceptingNotificationId(notification.id);
    clearAcceptError(notification.id);

    try {
      const acceptedInvitation = await acceptInvitation.mutateAsync({
        invitation_id: notification.entity_id,
      });
      if (!notification.is_read) {
        markRead.mutate(notification.id);
      }
      hideNotification(notification.id);
      toast.success("Invitation accepted", {
        description: "Opening the project invitation.",
      });
      navigate(target, { state: { acceptedInvitation } });
    } catch (error) {
      const message = getErrorMessage(error);
      if (isTerminalInvitationError(message)) {
        hideNotification(notification.id);
        void queryClient.invalidateQueries({ queryKey: notificationKeys.all });
      }
      setAcceptErrors((current) => ({
        ...current,
        [notification.id]: message,
      }));
      toast.error("Failed to accept invitation", {
        description: message,
      });
    } finally {
      setAcceptingNotificationId(null);
    }
  };

  return (
    <header className="flex h-16 shrink-0 items-center gap-2 px-4 shadow-md shadow-black/40 bg-background backdrop-blur">
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
              size="icon"
              className="relative size-11"
              aria-label="Notifications"
            >
              <Bell className="size-4" />
              {unreadCount > 0 ? (
                <span className="absolute right-1 top-1 inline-flex min-w-4 items-center justify-center rounded-full bg-destructive px-1 text-xs font-semibold text-white" aria-live="polite">
                  {unreadCount > 99 ? "99+" : unreadCount}
                  <span className="sr-only">{`${unreadCount} unread notifications`}</span>
                </span>
              ) : null}
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-80 space-y-3 p-3 sm:w-96">
            <div className="flex items-center justify-between">
              <p className="text-sm font-semibold">Notifications</p>
              <Button
                type="button"
                size="sm"
                variant="ghost"
                className="h-9 px-3 text-xs"
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
              ) : notificationsQuery.data?.items.some(
                (notification) => !hiddenNotificationIds[notification.id],
              ) ? (
                notificationsQuery.data.items
                  .filter((notification) => !hiddenNotificationIds[notification.id])
                  .map((notification) => {
                  const target = getNotificationTarget(notification);
                  const isInviteNotification = target !== null;
                  const isAccepting = acceptingNotificationId === notification.id;
                  const acceptError = acceptErrors[notification.id];

                  return (
                    <div key={notification.id} className="space-y-2 rounded-md border p-2">
                      <div className="flex items-start justify-between gap-2">
                        {target ? (
                          <button
                            type="button"
                            aria-label={notification.title}
                            className="flex-1 space-y-1 text-left"
                            onClick={() => openNotificationTarget(notification, target)}
                          >
                            <p className="text-xs font-medium">{notification.title}</p>
                            {notification.message && !isInviteNotification ? (
                              <p className="text-xs text-muted-foreground">{notification.message}</p>
                            ) : null}
                            <p className="text-xs text-muted-foreground">
                              {formatDistanceToNow(new Date(notification.created_at), { addSuffix: true })}
                            </p>
                          </button>
                        ) : (
                          <div className="flex-1 space-y-1">
                            <p className="text-xs font-medium">{notification.title}</p>
                            {notification.message ? (
                              <p className="text-xs text-muted-foreground">{notification.message}</p>
                            ) : null}
                            <p className="text-xs text-muted-foreground">
                              {formatDistanceToNow(new Date(notification.created_at), { addSuffix: true })}
                            </p>
                          </div>
                        )}
                        {!notification.is_read ? (
                          <Button
                            type="button"
                            size="sm"
                            variant="ghost"
                            className="h-9 px-3 text-xs"
                            disabled={markRead.isPending || isAccepting}
                            aria-label={`Mark ${notification.title} as read`}
                            onClick={() => {
                              markRead.mutate(notification.id);
                            }}
                          >
                            Mark as read
                          </Button>
                        ) : null}
                      </div>
                      {isInviteNotification ? (
                        <div className="flex items-center gap-2">
                          <Button
                            type="button"
                            size="sm"
                            className="h-9 px-3 text-xs"
                            disabled={isAccepting}
                            onClick={() => void acceptInvitationFromNotification(notification, target)}
                          >
                            {isAccepting ? "Accepting..." : "Accept"}
                          </Button>
                          <Button
                            type="button"
                            size="sm"
                            variant="ghost"
                            className="h-9 px-3 text-xs"
                            disabled={isAccepting}
                            onClick={() => openNotificationTarget(notification, target, {
                              review: true,
                              title: notification.title,
                              message: notification.message,
                            })}
                          >
                            Review invitation
                          </Button>
                        </div>
                      ) : null}
                      {acceptError ? (
                        <p className="text-xs text-destructive">{acceptError}</p>
                      ) : null}
                    </div>
                  );
                })
              ) : (
                <p className="text-xs text-muted-foreground">No notifications yet.</p>
              )}
            </div>

            <div className="border-t pt-2">
              <Button asChild type="button" variant="ghost" className="h-9 w-full justify-start px-2 text-xs">
                <Link to="/settings">Manage notification settings</Link>
              </Button>
            </div>
          </DropdownMenuContent>
        </DropdownMenu>
        {projectId ? (
          <>
            <span className={isProjectConnected ? "text-xs text-[var(--auth-feature-analytics)]" : "text-xs text-destructive"}>
              {projectSocketState?.status === "connected"
                ? "Connected"
                : projectSocketState?.status === "reconnecting"
                  ? "Reconnecting..."
                  : projectSocketState?.status === "connecting"
                    ? "Connecting..."
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
