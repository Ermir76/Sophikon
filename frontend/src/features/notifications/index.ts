// Public API for the `notifications` feature
export { notificationService } from './api/notification.service';

export {
  notificationKeys,
  useMarkAllNotificationsRead,
  useMarkNotificationRead,
  useNotifications,
  useNotificationSettings,
  useUpdateNotificationSettings,
} from './hooks/useNotifications';
export { useNotificationWebSocket } from './hooks/useNotificationWebSocket';
export { useNotificationWebSocketStore } from './store/notification-websocket-store';

export * from './types';
