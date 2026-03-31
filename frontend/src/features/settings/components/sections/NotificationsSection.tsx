import { toast } from "sonner";

import {
  useNotificationSettings,
  useUpdateNotificationSettings,
} from "@/features/notifications";
import type { NotificationSettings } from "@/features/notifications";
import { getErrorMessage } from "@/shared/lib/errors";
import { QueryError } from "@/shared/components/QueryError";
import { Label } from "@/shared/ui/label";
import { Switch } from "@/shared/ui/switch";

const NOTIFICATION_FIELDS: Array<{
  key: keyof NotificationSettings;
  label: string;
  description: string;
}> = [
  {
    key: "email_task_assigned",
    label: "Task assignments",
    description: "Send an email when a task is assigned to you.",
  },
  {
    key: "email_mentioned",
    label: "Mentions",
    description: "Send an email when someone mentions you.",
  },
  {
    key: "email_deadline_approaching",
    label: "Deadline approaching",
    description: "Send an email before upcoming deadlines.",
  },
  {
    key: "push_enabled",
    label: "In-app push notifications",
    description: "Show realtime notifications in the app.",
  },
];

export function NotificationsSection() {
  const notificationSettingsQuery = useNotificationSettings();
  const updateNotificationSettingsMutation = useUpdateNotificationSettings();

  const handleToggle = (field: keyof NotificationSettings, checked: boolean) => {
    updateNotificationSettingsMutation.mutate(
      { [field]: checked },
      {
        onSuccess: () => {
          toast.success("Notification settings saved");
        },
        onError: (error) => {
          toast.error(getErrorMessage(error));
        },
      },
    );
  };

  return (
    <section className="space-y-5">
      <div className="space-y-1">
        <h2 className="text-xl font-semibold text-foreground">Notifications</h2>
        <p className="text-sm text-muted-foreground">
          Choose which notifications you receive by email and in the app.
        </p>
      </div>
      {notificationSettingsQuery.isLoading ? (
        <p className="text-sm text-muted-foreground">Loading notification settings...</p>
      ) : notificationSettingsQuery.isError ? (
        <QueryError
          message={getErrorMessage(notificationSettingsQuery.error)}
          onRetry={() => notificationSettingsQuery.refetch()}
        />
      ) : (
        <div className="space-y-4">
          {NOTIFICATION_FIELDS.map((field) => (
            <div key={field.key} className="flex items-center justify-between gap-3 rounded-md border p-3">
              <div>
                <Label htmlFor={`notification-${field.key}`} className="text-sm font-medium">
                  {field.label}
                </Label>
                <p className="text-xs text-muted-foreground">{field.description}</p>
              </div>
              <Switch
                id={`notification-${field.key}`}
                checked={notificationSettingsQuery.data?.[field.key] ?? false}
                onCheckedChange={(checked) => handleToggle(field.key, checked)}
                disabled={updateNotificationSettingsMutation.isPending}
              />
            </div>
          ))}
        </div>
      )}
    </section>
  );
}
