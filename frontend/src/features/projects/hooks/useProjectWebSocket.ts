import { useEffect, useRef } from "react";
import { useNavigate } from "react-router";
import { useQueryClient } from "@tanstack/react-query";

import { useAuthStore } from "@/features/auth/store/auth-store";
import { projectActivityKeys } from "@/features/projects/hooks/useProjectActivity";
import { projectDashboardKeys } from "@/features/projects/hooks/useProjectDashboard";
import { projectMemberKeys } from "@/features/projects/hooks/useProjectMembers";
import { projectKeys } from "@/features/projects/hooks/useProjects";
import { useProjectWebSocketStore } from "@/features/projects/store/websocket-store";
import type {
  ProjectRealtimeChannel,
  ProjectRealtimeEventMessage,
  ProjectWebSocketMessage,
} from "@/features/projects/types";
import { resourceKeys } from "@/features/resources/hooks/useResources";
import { API_BASE } from "@/shared/api/api";
import { assignmentKeys } from "@/features/tasks/hooks/useAssignments";
import { commentKeys } from "@/features/tasks/hooks/useComments";
import { dependencyKeys } from "@/features/tasks/hooks/useDependencies";
import { taskKeys } from "@/features/tasks/hooks/useTasks";
import type { CommentEntityType } from "@/features/tasks/types";

const DEFAULT_CHANNELS: ProjectRealtimeChannel[] = [
  "tasks",
  "resources",
  "members",
  "activity",
  "project",
  "comments",
];
const TERMINAL_CLOSE_CODES = new Set([4401, 4403, 4404]);
const RECONNECT_DELAYS_MS = [1000, 2000, 5000, 10000];
const COMMENT_ENTITY_TYPES: ReadonlySet<CommentEntityType> = new Set([
  "project",
  "task",
  "resource",
  "assignment",
  "dependency",
  "project_member",
]);

function buildProjectWebSocketUrl(projectId: string) {
  if (/^https?:\/\//.test(API_BASE)) {
    const url = new URL(API_BASE);
    url.protocol = url.protocol === "https:" ? "wss:" : "ws:";
    url.pathname = `${url.pathname.replace(/\/$/, "")}/ws/projects/${projectId}`;
    return url.toString();
  }

  const url = new URL(window.location.origin);
  url.protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  url.pathname = `${API_BASE.replace(/\/$/, "")}/ws/projects/${projectId}`;
  return url.toString();
}

function invalidateProjectEventQueries(
  queryClient: ReturnType<typeof useQueryClient>,
  projectId: string,
  message: ProjectRealtimeEventMessage,
) {
  queryClient.invalidateQueries({
    queryKey: projectActivityKeys.all,
  });
  queryClient.invalidateQueries({
    queryKey: projectDashboardKeys.detail(projectId),
  });

  if (message.type === "activity_logged") {
    return;
  }

  if (message.entity_type === "project") {
    queryClient.invalidateQueries({ queryKey: projectKeys.all });
  }

  if (
    message.entity_type === "task"
    || message.entity_type === "assignment"
    || message.entity_type === "dependency"
  ) {
    queryClient.invalidateQueries({ queryKey: taskKeys.list(projectId) });
    queryClient.invalidateQueries({ queryKey: dependencyKeys.list(projectId) });
  }

  if (
    message.entity_type === "task"
    && message.entity_id
  ) {
    queryClient.invalidateQueries({
      queryKey: taskKeys.detail(projectId, message.entity_id),
    });
  }

  if (
    message.entity_type === "resource"
    || message.entity_type === "assignment"
  ) {
    queryClient.invalidateQueries({ queryKey: resourceKeys.list(projectId) });
  }

  if (message.entity_type === "resource" && message.entity_id) {
    queryClient.invalidateQueries({
      queryKey: resourceKeys.detail(projectId, message.entity_id),
    });
  }

  if (message.entity_type === "assignment") {
    const taskId = typeof message.metadata?.task_id === "string"
      ? message.metadata.task_id
      : null;
    if (taskId) {
      queryClient.invalidateQueries({
        queryKey: assignmentKeys.list(projectId, taskId),
      });
    }
  }

  if (message.entity_type === "project_member") {
    queryClient.invalidateQueries({ queryKey: projectMemberKeys.members(projectId) });
    queryClient.invalidateQueries({
      queryKey: projectMemberKeys.invitations(projectId),
    });
  }

  if (message.entity_type === "comment") {
    const commentEntityTypeRaw = typeof message.metadata?.comment_entity_type === "string"
      ? message.metadata.comment_entity_type
      : null;
    const commentEntityType = (
      commentEntityTypeRaw
      && COMMENT_ENTITY_TYPES.has(commentEntityTypeRaw as CommentEntityType)
    )
      ? commentEntityTypeRaw as CommentEntityType
      : null;
    const commentEntityId = typeof message.metadata?.comment_entity_id === "string"
      ? message.metadata.comment_entity_id
      : null;
    if (commentEntityType && commentEntityId) {
      queryClient.invalidateQueries({
        queryKey: commentKeys.byEntity(commentEntityType, commentEntityId),
      });
      if (commentEntityType === "task") {
        queryClient.invalidateQueries({ queryKey: taskKeys.list(projectId) });
        queryClient.invalidateQueries({
          queryKey: taskKeys.detail(projectId, commentEntityId),
        });
      }
    }
  }
}

export function useProjectWebSocket(projectId: string | null | undefined) {
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const currentUserId = useAuthStore((state) => state.user?.id ?? null);
  const setStatus = useProjectWebSocketStore((state) => state.setStatus);
  const setUsers = useProjectWebSocketStore((state) => state.setUsers);
  const setSubscribedChannels = useProjectWebSocketStore(
    (state) => state.setSubscribedChannels,
  );
  const setReconnectAttempt = useProjectWebSocketStore(
    (state) => state.setReconnectAttempt,
  );
  const clearProject = useProjectWebSocketStore((state) => state.clearProject);

  const socketRef = useRef<WebSocket | null>(null);
  const reconnectTimerRef = useRef<number | null>(null);
  const shouldReconnectRef = useRef(true);
  const reconnectAttemptRef = useRef(0);

  useEffect(() => {
    if (!projectId) {
      return;
    }
    const activeProjectId = projectId;

    shouldReconnectRef.current = true;
    reconnectAttemptRef.current = 0;
    setSubscribedChannels(activeProjectId, DEFAULT_CHANNELS);

    function cleanupSocket() {
      if (reconnectTimerRef.current !== null) {
        window.clearTimeout(reconnectTimerRef.current);
        reconnectTimerRef.current = null;
      }
      if (socketRef.current) {
        socketRef.current.close();
        socketRef.current = null;
      }
    }

    function handleProjectExit() {
      shouldReconnectRef.current = false;
      cleanupSocket();
      clearProject(activeProjectId);
      navigate("/projects", { replace: true });
    }

    function connect(mode: "connecting" | "reconnecting") {
      setStatus(activeProjectId, mode);

      const socket = new WebSocket(buildProjectWebSocketUrl(activeProjectId));
      socketRef.current = socket;

      socket.addEventListener("open", () => {
        reconnectAttemptRef.current = 0;
        setReconnectAttempt(activeProjectId, 0);
        setStatus(activeProjectId, "connected");
        socket.send(
          JSON.stringify({
            type: "subscribe",
            channels: DEFAULT_CHANNELS,
          }),
        );
      });

      socket.addEventListener("message", (event) => {
        if (typeof event.data !== "string") {
          console.warn("Received non-string websocket payload", event.data);
          return;
        }

        let message: ProjectWebSocketMessage;
        try {
          message = JSON.parse(event.data) as ProjectWebSocketMessage;
        } catch (error) {
          console.warn("Received malformed websocket payload", error);
          return;
        }

        if (message.type === "presence_snapshot" || message.type === "presence_update") {
          setUsers(activeProjectId, message.users);
          return;
        }

        if (message.type === "error") {
          setStatus(activeProjectId, "error");
          return;
        }

        invalidateProjectEventQueries(queryClient, activeProjectId, message);

        if (message.type === "project_deleted") {
          handleProjectExit();
          return;
        }

        if (
          message.type === "project_member_deleted"
          && currentUserId
          && typeof message.metadata?.user_id === "string"
          && message.metadata.user_id === currentUserId
        ) {
          handleProjectExit();
        }
      });

      socket.addEventListener("close", (event) => {
        socketRef.current = null;
        setUsers(activeProjectId, []);

        if (!shouldReconnectRef.current) {
          setStatus(activeProjectId, "idle");
          return;
        }

        if (TERMINAL_CLOSE_CODES.has(event.code)) {
          setStatus(activeProjectId, "error");
          return;
        }

        const attempt = reconnectAttemptRef.current + 1;
        reconnectAttemptRef.current = attempt;
        setReconnectAttempt(activeProjectId, attempt);
        setStatus(activeProjectId, "reconnecting");

        const delay = RECONNECT_DELAYS_MS[Math.min(attempt - 1, RECONNECT_DELAYS_MS.length - 1)];
        reconnectTimerRef.current = window.setTimeout(() => {
          connect("reconnecting");
        }, delay);
      });

      socket.addEventListener("error", () => {
        setStatus(activeProjectId, "error");
      });
    }

    connect("connecting");

    return () => {
      shouldReconnectRef.current = false;
      cleanupSocket();
      clearProject(activeProjectId);
    };
  }, [
    clearProject,
    currentUserId,
    navigate,
    projectId,
    queryClient,
    setReconnectAttempt,
    setStatus,
    setSubscribedChannels,
    setUsers,
  ]);
}
