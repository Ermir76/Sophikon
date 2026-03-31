import { zodResolver } from "@hookform/resolvers/zod";
import { Loader2, Save, Upload, X } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import { z } from "zod";

import {
  useDeleteAvatar,
  useUpdateProfile,
  useUploadAvatar,
  useAuthStore,
} from "@/features/auth";
import { getErrorMessage } from "@/shared/lib/errors";
import { Alert, AlertDescription } from "@/shared/ui/alert";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/shared/ui/alert-dialog";
import { Avatar, AvatarFallback, AvatarImage } from "@/shared/ui/avatar";
import { Button } from "@/shared/ui/button";
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

const profileSchema = z.object({
  full_name: z.string().min(1, "Full name is required.").max(255, "Name is too long."),
  timezone: z.string().min(1, "Timezone is required.").max(50, "Timezone is too long."),
  locale: z.string().min(1, "Locale is required.").max(10, "Locale is too long."),
});

type ProfileFormValues = z.infer<typeof profileSchema>;

const TIMEZONE_OPTIONS = [
  "UTC",
  "Europe/Stockholm",
  "Europe/London",
  "America/New_York",
  "America/Los_Angeles",
  "Asia/Tokyo",
];

const LOCALE_OPTIONS = ["en-US", "sv-SE", "en-GB", "de-DE", "fr-FR"];

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

export function ProfileSection() {
  const user = useAuthStore((state) => state.user);
  const updateProfileMutation = useUpdateProfile();
  const uploadAvatarMutation = useUploadAvatar();
  const deleteAvatarMutation = useDeleteAvatar();
  const avatarInputRef = useRef<HTMLInputElement | null>(null);
  const [avatarUploadError, setAvatarUploadError] = useState<string | null>(null);
  const [showRemoveAvatarDialog, setShowRemoveAvatarDialog] = useState(false);

  const profileForm = useForm<ProfileFormValues>({
    resolver: zodResolver(profileSchema),
    defaultValues: {
      full_name: user?.full_name ?? "",
      timezone: user?.timezone ?? "UTC",
      locale: user?.locale ?? "en-US",
    },
  });

  useEffect(() => {
    profileForm.reset({
      full_name: user?.full_name ?? "",
      timezone: user?.timezone ?? "UTC",
      locale: user?.locale ?? "en-US",
    });
  }, [profileForm, user]);

  if (!user) {
    return null;
  }

  return (
    <>
      <section className="space-y-6">
        <div className="space-y-1">
          <h2 className="text-xl font-semibold text-foreground">Profile</h2>
          <p className="text-sm text-muted-foreground">
            Update your profile photo, name, and localization settings.
          </p>
        </div>
        {avatarUploadError ? (
          <Alert variant="destructive">
            <AlertDescription>{avatarUploadError}</AlertDescription>
          </Alert>
        ) : null}

        {deleteAvatarMutation.isError ? (
          <Alert variant="destructive">
            <AlertDescription>{getErrorMessage(deleteAvatarMutation.error)}</AlertDescription>
          </Alert>
        ) : null}

        <div className="grid w-full max-w-[28rem] grid-cols-1 gap-3 sm:grid-cols-[auto_minmax(0,1fr)] sm:items-center">
          <Avatar className="h-14 w-14 rounded-full sm:self-center">
            {user.avatar_url ? <AvatarImage src={user.avatar_url} alt={user.full_name} /> : null}
            <AvatarFallback className="rounded-full">{getInitials(user.full_name)}</AvatarFallback>
          </Avatar>
          <input
            ref={avatarInputRef}
            type="file"
            className="hidden"
            accept="image/png,image/jpeg,image/webp"
            onChange={(event) => {
              const selected = event.target.files?.[0];
              event.target.value = "";
              if (!selected) {
                return;
              }
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
                  toast.success("Profile photo updated");
                },
                onError: (error) => {
                  const message = getErrorMessage(error);
                  setAvatarUploadError(message);
                  toast.error(message);
                },
              });
            }}
          />
          <div className="grid w-full grid-cols-1 gap-3 sm:grid-cols-2">
            <Button
              type="button"
              variant="outline"
              className="w-full justify-center"
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
                  Upload photo
                </>
              )}
            </Button>
            <Button
              type="button"
              variant="outline"
              className="w-full justify-center"
              onClick={() => setShowRemoveAvatarDialog(true)}
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
                  Remove photo
                </>
              )}
            </Button>
          </div>
        </div>

        {updateProfileMutation.isError ? (
          <Alert variant="destructive">
            <AlertDescription>{getErrorMessage(updateProfileMutation.error)}</AlertDescription>
          </Alert>
        ) : null}

        <Form {...profileForm}>
          <form
            className="w-full max-w-[42rem] space-y-6"
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
                <FormItem className="w-full max-w-[28rem]">
                  <FormLabel>Full Name</FormLabel>
                  <FormControl>
                    <Input placeholder="Your full name" autoComplete="name" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <div className="grid w-full max-w-[28rem] gap-4 md:grid-cols-2">
              <FormField
                control={profileForm.control}
                name="timezone"
                render={({ field }) => (
                  <FormItem className="w-full">
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
                  <FormItem className="w-full">
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

            <div className="flex w-full justify-end">
              <Button
                type="submit"
                className="h-10 min-w-36 justify-center"
                disabled={updateProfileMutation.isPending || !profileForm.formState.isDirty}
              >
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
      </section>

      <AlertDialog open={showRemoveAvatarDialog} onOpenChange={setShowRemoveAvatarDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Remove profile photo?</AlertDialogTitle>
            <AlertDialogDescription>
              You can upload a new profile photo at any time.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => {
                setAvatarUploadError(null);
                deleteAvatarMutation.mutate(undefined, {
                  onSuccess: () => {
                    toast.success("Profile photo removed");
                  },
                });
              }}
              disabled={deleteAvatarMutation.isPending}
            >
              {deleteAvatarMutation.isPending ? "Removing..." : "Remove photo"}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
}
