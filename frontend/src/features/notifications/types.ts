export type NotificationType =
  | "task_assigned"
  | "task_updated"
  | "mentioned"
  | "comment_added"
  | "deadline_approaching"
  | "invitation_received";

export interface NotificationActor {
  id: string;
  full_name?: string | null;
  avatar_url?: string | null;
}

export interface NotificationItem {
  id: string;
  type: NotificationType;
  title: string;
  message?: string | null;
  entity_type?: string | null;
  entity_id?: string | null;
  actor?: NotificationActor | null;
  is_read: boolean;
  read_at?: string | null;
  created_at: string;
}

export interface NotificationListResponse {
  items: NotificationItem[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
  unread_count: number;
}

export interface NotificationSettings {
  email_task_assigned: boolean;
  email_mentioned: boolean;
  email_deadline_approaching: boolean;
  push_enabled: boolean;
}

export interface NotificationSettingsUpdate {
  email_task_assigned?: boolean;
  email_mentioned?: boolean;
  email_deadline_approaching?: boolean;
  push_enabled?: boolean;
}

export interface NotificationReadAllResponse {
  updated_count: number;
  unread_count: number;
}

export type NotificationConnectionStatus =
  | "idle"
  | "connecting"
  | "connected"
  | "reconnecting"
  | "error";

export interface NotificationSnapshotMessage {
  type: "notification_snapshot";
  unread_count: number;
}

export interface NotificationCreatedMessage {
  type: "notification_created";
  notification: NotificationItem;
  unread_count: number;
}

export interface NotificationUpdatedMessage {
  type: "notification_updated";
  notification_id: string;
  is_read: boolean;
  read_at?: string | null;
  unread_count: number;
}

export interface NotificationsReadAllMessage {
  type: "notifications_read_all";
  unread_count: number;
}

export interface NotificationWebSocketErrorMessage {
  type: "error";
  code: string;
  message: string;
}

export type NotificationWebSocketMessage =
  | NotificationSnapshotMessage
  | NotificationCreatedMessage
  | NotificationUpdatedMessage
  | NotificationsReadAllMessage
  | NotificationWebSocketErrorMessage;
