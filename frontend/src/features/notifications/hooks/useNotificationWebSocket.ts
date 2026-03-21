import { useEffect, useRef } from "react";
import { useQueryClient } from "@tanstack/react-query";

import { useAuthStore } from "@/features/auth";
import { notificationKeys } from "@/features/notifications/hooks/useNotifications";
import { useNotificationWebSocketStore } from "@/features/notifications/store/notification-websocket-store";
import type { NotificationWebSocketMessage } from "@/features/notifications/types";
import { API_BASE } from "@/shared/api/api";

const TERMINAL_CLOSE_CODES = new Set([4400, 4401]);
const RECONNECT_DELAYS_MS = [1000, 2000, 5000, 10000];

function buildNotificationWebSocketUrl() {
  if (/^https?:\/\//.test(API_BASE)) {
    const url = new URL(API_BASE);
    url.protocol = url.protocol === "https:" ? "wss:" : "ws:";
    url.pathname = `${url.pathname.replace(/\/$/, "")}/ws/notifications`;
    return url.toString();
  }

  const url = new URL(window.location.origin);
  url.protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  url.pathname = `${API_BASE.replace(/\/$/, "")}/ws/notifications`;
  return url.toString();
}

export function useNotificationWebSocket() {
  const queryClient = useQueryClient();
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const setStatus = useNotificationWebSocketStore((state) => state.setStatus);
  const setReconnectAttempt = useNotificationWebSocketStore((state) => state.setReconnectAttempt);
  const setUnreadCount = useNotificationWebSocketStore((state) => state.setUnreadCount);
  const reset = useNotificationWebSocketStore((state) => state.reset);

  const socketRef = useRef<WebSocket | null>(null);
  const reconnectTimerRef = useRef<number | null>(null);
  const shouldReconnectRef = useRef(true);
  const reconnectAttemptRef = useRef(0);

  useEffect(() => {
    if (!isAuthenticated) {
      shouldReconnectRef.current = false;
      if (reconnectTimerRef.current !== null) {
        window.clearTimeout(reconnectTimerRef.current);
        reconnectTimerRef.current = null;
      }
      if (socketRef.current) {
        socketRef.current.close();
        socketRef.current = null;
      }
      reset();
      return;
    }

    shouldReconnectRef.current = true;
    reconnectAttemptRef.current = 0;
    setReconnectAttempt(0);

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

    function connect(mode: "connecting" | "reconnecting") {
      setStatus(mode);
      const socket = new WebSocket(buildNotificationWebSocketUrl());
      socketRef.current = socket;

      socket.addEventListener("open", () => {
        reconnectAttemptRef.current = 0;
        setReconnectAttempt(0);
        setStatus("connected");
      });

      socket.addEventListener("message", (event) => {
        if (typeof event.data !== "string") {
          return;
        }

        let message: NotificationWebSocketMessage;
        try {
          message = JSON.parse(event.data) as NotificationWebSocketMessage;
        } catch {
          return;
        }

        if (message.type === "error") {
          setStatus("error");
          return;
        }

        if ("unread_count" in message) {
          setUnreadCount(message.unread_count);
        }
        queryClient.invalidateQueries({ queryKey: notificationKeys.all });
      });

      socket.addEventListener("close", (event) => {
        socketRef.current = null;
        if (!shouldReconnectRef.current) {
          setStatus("idle");
          return;
        }

        if (TERMINAL_CLOSE_CODES.has(event.code)) {
          setStatus("error");
          return;
        }

        const attempt = reconnectAttemptRef.current + 1;
        reconnectAttemptRef.current = attempt;
        setReconnectAttempt(attempt);
        setStatus("reconnecting");

        const delay = RECONNECT_DELAYS_MS[Math.min(attempt - 1, RECONNECT_DELAYS_MS.length - 1)];
        reconnectTimerRef.current = window.setTimeout(() => {
          connect("reconnecting");
        }, delay);
      });

      socket.addEventListener("error", () => {
        setStatus("error");
      });
    }

    connect("connecting");

    return () => {
      shouldReconnectRef.current = false;
      cleanupSocket();
      reset();
    };
  }, [
    isAuthenticated,
    queryClient,
    reset,
    setReconnectAttempt,
    setStatus,
    setUnreadCount,
  ]);
}
