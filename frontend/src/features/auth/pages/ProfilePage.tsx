import { zodResolver } from "@hookform/resolvers/zod";
import { Bot, Loader2, Save, ShieldCheck, Upload, UserRound, X } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { useForm } from "react-hook-form";
import { Link } from "react-router";
import { z } from "zod";
import { toast } from "sonner";

import {
  useAiPreferences,
  useChangePassword,
  useDeleteAvatar,
  useUpdateAiPreferences,
  useUpdateProfile,
  useUploadAvatar,
} from "@/features/auth/hooks/useAuth";
import { useAuthStore } from "@/features/auth/store/auth-store";
import { PageHeader } from "@/shared/components/layout/PageHeader";
import { PageShell } from "@/shared/components/layout/PageShell";
import { QueryError } from "@/shared/components/QueryError";
import { getErrorMessage } from "@/shared/lib/errors";
import { Alert, AlertDescription } from "@/shared/ui/alert";
import { Avatar, AvatarFallback, AvatarImage } from "@/shared/ui/avatar";
import { Button } from "@/shared/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/shared/ui/card";
import { Switch } from "@/shared/ui/switch";
import { Label } from "@/shared/ui/label";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/shared/ui/form";
import { Input } from "@/shared/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/shared/ui/select";
import { Separator } from "@/shared/ui/separator";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/shared/ui/tabs";

const profileSchema = z.object({
  full_name: z.string().min(1, "Full name is required.").max(255, "Name is too long."),
  timezone: z.string().min(1, "Timezone is required.").max(50, "Timezone is too long."),
  locale: z.string().min(1, "Locale is required.").max(10, "Locale is too long."),
});

const changePasswordSchema = z
  .object({
    current_password: z.string().min(1, "Current password is required."),
    new_password: z
      .string()
      .min(8, "Password must be at least 8 characters.")
      .regex(/[A-Z]/, "Password must contain at least one uppercase letter")
      .regex(/[0-9]/, "Password must contain at least one number")
      .regex(
        /[^a-zA-Z0-9]/,
        "Password must contain at least one special character",
      ),
    confirm_password: z.string().min(1, "Please confirm your password."),
  })
  .refine((data) => data.new_password === data.confirm_password, {
    message: "Passwords do not match",
    path: ["confirm_password"],
  });

type ProfileFormValues = z.infer<typeof profileSchema>;
type ChangePasswordFormValues = z.infer<typeof changePasswordSchema>;

const TIMEZONE_OPTIONS = [
  "UTC",
  "Europe/Stockholm",
  "Europe/London",
  "America/New_York",
  "America/Los_Angeles",
  "Asia/Tokyo",
];

const LOCALE_OPTIONS = [
  "en-US",
  "sv-SE",
  "en-GB",
  "de-DE",
  "fr-FR",
];

const MAX_AVATAR_BYTES = 2 * 1024 * 1024;
const ALLOWED_AVATAR_TYPES = ["image/png", "image/jpeg", "image/webp"];

function getInitials(name: string): string {
  return name
    .split(" ")
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase() ?? "")
    .join("");
}

const AI_TOOL_LABELS: Record<string, string> = {
  create_task: "Create task",
  update_task: "Update task",
  bulk_create_tasks: "Bulk create tasks",
  add_dependency: "Add dependency",
  indent_task: "Indent task",
  outdent_task: "Outdent task",
  reorder_task: "Reorder task",
  calculate_schedule: "Calculate schedule",
  navigate: "Navigate view",
  highlight_tasks: "Highlight tasks",
  open_task: "Open task panel",
  filter_view: "Filter view",
};

export default function ProfilePage() {
  const user = useAuthStore((state) => state.user);
  const updateProfileMutation = useUpdateProfile();
  const changePasswordMutation = useChangePassword();
  const uploadAvatarMutation = useUploadAvatar();
  const deleteAvatarMutation = useDeleteAvatar();
  const aiPreferencesQuery = useAiPreferences();
  const updateAiPreferencesMutation = useUpdateAiPreferences();
  const avatarInputRef = useRef<HTMLInputElement | null>(null);
  const [avatarUploadError, setAvatarUploadError] = useState<string | null>(null);
  const [aiAutoApproveDraft, setAiAutoApproveDraft] = useState<Record<string, boolean>>({});
  const [pendingAiToolName, setPendingAiToolName] = useState<string | null>(null);

  const aiAutoApprove = {
    ...(aiPreferencesQuery.data?.auto_approve ?? {}),
    ...aiAutoApproveDraft,
  };

  const handleAiToggle = (toolName: string, value: boolean) => {
    if (pendingAiToolName) {
      return;
    }

    const previousValue =
      aiAutoApproveDraft[toolName] ?? aiPreferencesQuery.data?.auto_approve?.[toolName] ?? true;

    setPendingAiToolName(toolName);
    setAiAutoApproveDraft((current) => ({ ...current, [toolName]: value }));
    updateAiPreferencesMutation.mutate(
      { auto_approve: { [toolName]: value } },
      {
        onSuccess: (updatedPreferences) => {
          setAiAutoApproveDraft(updatedPreferences.auto_approve);
          setPendingAiToolName(null);
          toast.success("Preferences saved");
        },
        onError: (error) => {
          setAiAutoApproveDraft((current) => ({ ...current, [toolName]: previousValue }));
          setPendingAiToolName(null);
          toast.error(getErrorMessage(error));
        },
      },
    );
  };

  const profileForm = useForm<ProfileFormValues>({
    resolver: zodResolver(profileSchema),
    defaultValues: {
      full_name: user?.full_name ?? "",
      timezone: user?.timezone ?? "UTC",
      locale: user?.locale ?? "en-US",
    },
  });

  const securityForm = useForm<ChangePasswordFormValues>({
    resolver: zodResolver(changePasswordSchema),
    defaultValues: {
      current_password: "",
      new_password: "",
      confirm_password: "",
    },
  });

  useEffect(() => {
    profileForm.reset({
      full_name: user?.full_name ?? "",
      timezone: user?.timezone ?? "UTC",
      locale: user?.locale ?? "en-US",
    });
  }, [profileForm, user]);

  useEffect(() => {
    setAiAutoApproveDraft(aiPreferencesQuery.data?.auto_approve ?? {});
  }, [aiPreferencesQuery.data?.auto_approve]);

  const handleAvatarUploadError = (error: unknown) => {
    const rawMessage: unknown = getErrorMessage(error);
    const message =
      typeof rawMessage === "string" && rawMessage.trim().length > 0
        ? rawMessage
        : "Avatar upload failed. Please try a different image.";
    setAvatarUploadError(message);
    toast.error(message);
  };

  if (!user) {
    return null;
  }

  return (
    <PageShell className="h-full overflow-y-auto">
      <PageHeader
        title="Profile"
        description="Manage your account profile and security settings."
      />

      <Tabs defaultValue="profile" className="space-y-4">
        <TabsList variant="line">
          <TabsTrigger value="profile">
            <UserRound className="mr-2 h-4 w-4" />
            Profile
          </TabsTrigger>
          <TabsTrigger value="security">
            <ShieldCheck className="mr-2 h-4 w-4" />
            Security
          </TabsTrigger>
          <TabsTrigger value="ai">
            <Bot className="mr-2 h-4 w-4" />
            AI Settings
          </TabsTrigger>
        </TabsList>

        <TabsContent value="profile" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Avatar</CardTitle>
              <CardDescription>
                Upload a profile photo. PNG, JPEG, or WEBP up to 2MB.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {avatarUploadError ? (
                <Alert variant="destructive">
                  <AlertDescription>{avatarUploadError}</AlertDescription>
                </Alert>
              ) : null}

              {deleteAvatarMutation.isError ? (
                <Alert variant="destructive">
                  <AlertDescription>
                    {getErrorMessage(deleteAvatarMutation.error)}
                  </AlertDescription>
                </Alert>
              ) : null}

              <div className="flex items-center gap-4">
                <Avatar className="h-14 w-14 rounded-lg">
                  {user.avatar_url ? <AvatarImage src={user.avatar_url} alt={user.full_name} /> : null}
                  <AvatarFallback className="rounded-lg">{getInitials(user.full_name)}</AvatarFallback>
                </Avatar>
                <div className="flex flex-wrap gap-2">
                  <input
                    ref={avatarInputRef}
                    type="file"
                    className="hidden"
                    accept="image/png,image/jpeg,image/webp"
                    onChange={(event) => {
                      const selected = event.target.files?.[0];
                      event.target.value = "";
                      if (!selected) return;
                      if (!ALLOWED_AVATAR_TYPES.includes(selected.type)) {
                        setAvatarUploadError("Only PNG, JPEG, and WEBP files are supported.");
                        return;
                      }
                      if (selected.size > MAX_AVATAR_BYTES) {
                        setAvatarUploadError("Avatar file must be 2MB or smaller.");
                        return;
                      }
                      setAvatarUploadError(null);
                      uploadAvatarMutation.mutate(selected, {
                        onSuccess: () => {
                          setAvatarUploadError(null);
                        },
                        onError: handleAvatarUploadError,
                      });
                    }}
                  />
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => avatarInputRef.current?.click()}
                    disabled={uploadAvatarMutation.isPending}
                  >
                    {uploadAvatarMutation.isPending ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        Uploading...
                      </>
                    ) : (
                      <>
                        <Upload className="mr-2 h-4 w-4" />
                        Upload Avatar
                      </>
                    )}
                  </Button>
                  <Button
                    type="button"
                    variant="ghost"
                    onClick={() => {
                      setAvatarUploadError(null);
                      deleteAvatarMutation.mutate();
                    }}
                    disabled={!user.avatar_url || deleteAvatarMutation.isPending}
                  >
                    {deleteAvatarMutation.isPending ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        Removing...
                      </>
                    ) : (
                      <>
                        <X className="mr-2 h-4 w-4" />
                        Remove
                      </>
                    )}
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Profile Details</CardTitle>
              <CardDescription>
                Update your name and localization settings.
              </CardDescription>
            </CardHeader>
            <CardContent>
              {updateProfileMutation.isError ? (
                <Alert variant="destructive" className="mb-5">
                  <AlertDescription>{getErrorMessage(updateProfileMutation.error)}</AlertDescription>
                </Alert>
              ) : null}

              <Form {...profileForm}>
                <form
                  className="space-y-6"
                  onSubmit={profileForm.handleSubmit((data) => {
                    const patch: {
                      full_name?: string;
                      timezone?: string;
                      locale?: string;
                    } = {};

                    if (data.full_name.trim() !== (user.full_name ?? "")) {
                      patch.full_name = data.full_name.trim();
                    }
                    if (data.timezone.trim() !== (user.timezone ?? "UTC")) {
                      patch.timezone = data.timezone.trim();
                    }
                    if (data.locale.trim() !== (user.locale ?? "en-US")) {
                      patch.locale = data.locale.trim();
                    }

                    if (Object.keys(patch).length === 0) {
                      return;
                    }
                    updateProfileMutation.mutate(patch, {
                      onSuccess: () => {
                        toast.success("Profile updated successfully");
                      },
                    });
                  })}
                >
                  <FormField
                    control={profileForm.control}
                    name="full_name"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Full Name</FormLabel>
                        <FormControl>
                          <Input placeholder="Your full name" autoComplete="name" {...field} />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  <div className="grid gap-4 md:grid-cols-2">
                    <FormField
                      control={profileForm.control}
                      name="timezone"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Timezone</FormLabel>
                          <Select value={field.value} onValueChange={field.onChange}>
                            <FormControl>
                              <SelectTrigger className="w-full">
                                <SelectValue placeholder="Select timezone" />
                              </SelectTrigger>
                            </FormControl>
                            <SelectContent>
                              {TIMEZONE_OPTIONS.map((option) => (
                                <SelectItem key={option} value={option}>
                                  {option}
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                          <FormMessage />
                        </FormItem>
                      )}
                    />

                    <FormField
                      control={profileForm.control}
                      name="locale"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Locale</FormLabel>
                          <Select value={field.value} onValueChange={field.onChange}>
                            <FormControl>
                              <SelectTrigger className="w-full">
                                <SelectValue placeholder="Select locale" />
                              </SelectTrigger>
                            </FormControl>
                            <SelectContent>
                              {LOCALE_OPTIONS.map((option) => (
                                <SelectItem key={option} value={option}>
                                  {option}
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                  </div>

                  <div className="flex justify-end">
                    <Button type="submit" disabled={updateProfileMutation.isPending}>
                      {updateProfileMutation.isPending ? (
                        <>
                          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                          Saving...
                        </>
                      ) : (
                        <>
                          <Save className="mr-2 h-4 w-4" />
                          Save Changes
                        </>
                      )}
                    </Button>
                  </div>
                </form>
              </Form>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="security" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Change Password</CardTitle>
              <CardDescription>
                Update your password while you are signed in.
              </CardDescription>
            </CardHeader>
            <CardContent>
              {changePasswordMutation.isError ? (
                <Alert variant="destructive" className="mb-5">
                  <AlertDescription>{getErrorMessage(changePasswordMutation.error)}</AlertDescription>
                </Alert>
              ) : null}

              <Form {...securityForm}>
                <form
                  className="space-y-6"
                  onSubmit={securityForm.handleSubmit((data) => {
                    changePasswordMutation.mutate(
                      {
                        current_password: data.current_password,
                        new_password: data.new_password,
                      },
                      {
                        onSuccess: () => {
                          securityForm.reset({
                            current_password: "",
                            new_password: "",
                            confirm_password: "",
                          });
                          toast.success("Password changed successfully");
                        },
                      },
                    );
                  })}
                >
                  <FormField
                    control={securityForm.control}
                    name="current_password"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Current Password</FormLabel>
                        <FormControl>
                          <Input type="password" autoComplete="current-password" {...field} />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  <div className="grid gap-4 md:grid-cols-2">
                    <FormField
                      control={securityForm.control}
                      name="new_password"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>New Password</FormLabel>
                          <FormControl>
                            <Input type="password" autoComplete="new-password" {...field} />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />

                    <FormField
                      control={securityForm.control}
                      name="confirm_password"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Confirm New Password</FormLabel>
                          <FormControl>
                            <Input type="password" autoComplete="new-password" {...field} />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                  </div>

                  <div className="flex justify-end">
                    <Button type="submit" disabled={changePasswordMutation.isPending}>
                      {changePasswordMutation.isPending ? (
                        <>
                          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                          Updating...
                        </>
                      ) : (
                        "Change Password"
                      )}
                    </Button>
                  </div>
                </form>
              </Form>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Account Recovery</CardTitle>
              <CardDescription>
                If you cannot remember your current password, use the reset flow.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <Separator />
              <p className="text-sm text-muted-foreground">
                Recovery sends a reset link to your email and is intended for locked-out scenarios.
              </p>
              <Button asChild variant="outline">
                <Link to="/forgot-password">Go to password reset</Link>
              </Button>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="ai" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>AI Tool Permissions</CardTitle>
              <CardDescription>
                Control which actions the AI can take autonomously. Disabled tools always require your approval.
                Delete actions always require approval regardless of these settings.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {aiPreferencesQuery.isLoading ? (
                <p className="text-sm text-muted-foreground">Loading preferences...</p>
              ) : aiPreferencesQuery.isError ? (
                <QueryError
                  message={getErrorMessage(aiPreferencesQuery.error)}
                  onRetry={() => aiPreferencesQuery.refetch()}
                />
              ) : (
                <div className="space-y-4">
                  {Object.entries(AI_TOOL_LABELS).map(([toolName, label]) => (
                    <div key={toolName} className="flex items-center justify-between">
                      <Label htmlFor={`ai-tool-${toolName}`} className="text-sm font-normal">
                        {label}
                      </Label>
                      <Switch
                        id={`ai-tool-${toolName}`}
                        checked={aiAutoApprove[toolName] ?? true}
                        onCheckedChange={(checked) => handleAiToggle(toolName, checked)}
                        aria-busy={pendingAiToolName === toolName}
                      />
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </PageShell>
  );
}
