import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { toast } from "sonner";
import { useNavigate } from "react-router";

import { useOrgStore, useOrganization, useOrganizations, useUpdateOrganization, useDeleteOrganization } from "@/features/organizations";
import { QueryError } from "@/shared/components/QueryError";
import { getErrorMessage } from "@/shared/lib/errors";
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
import { Textarea } from "@/shared/ui/textarea";

const orgSchema = z.object({
  name: z.string().min(2, "Name must be at least 2 characters"),
  slug: z
    .string()
    .min(2, "Slug must be at least 2 characters")
    .regex(
      /^[a-z0-9]+(?:-[a-z0-9]+)*$/,
      "Slug must contain only lowercase letters, numbers, and hyphens.",
    ),
  description: z.string().max(500, "Description must be 500 characters or less.").optional(),
});

type OrgFormValues = z.infer<typeof orgSchema>;

export function GeneralSection() {
  const navigate = useNavigate();
  const activeOrgId = useOrgStore((state) => state.activeOrgId);
  const setActiveOrg = useOrgStore((state) => state.setActiveOrg);
  const clearOrg = useOrgStore((state) => state.clear);

  const { data: activeOrganization, isLoading, isError, refetch } = useOrganization(activeOrgId);
  const { data: organizationsData } = useOrganizations();
  const updateOrgMutation = useUpdateOrganization(activeOrgId);
  const deleteOrgMutation = useDeleteOrganization();
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

  const form = useForm<OrgFormValues>({
    resolver: zodResolver(orgSchema),
    defaultValues: {
      name: "",
      slug: "",
      description: "",
    },
  });

  useEffect(() => {
    if (!activeOrganization) {
      return;
    }

    const currentDescription =
      typeof activeOrganization.settings?.description === "string"
        ? activeOrganization.settings.description
        : "";

    form.reset({
      name: activeOrganization.name,
      slug: activeOrganization.slug,
      description: currentDescription,
    });
  }, [activeOrganization, form]);

  if (!activeOrgId) {
    return (
      <section className="space-y-1">
        <h2 className="text-xl font-semibold text-foreground">General</h2>
        <p className="text-sm text-muted-foreground">Select an organization to manage organization settings.</p>
      </section>
    );
  }

  if (isLoading) {
    return (
      <section className="space-y-1">
        <h2 className="text-xl font-semibold text-foreground">General</h2>
        <p className="text-sm text-muted-foreground">Loading organization details...</p>
      </section>
    );
  }

  if (isError) {
    return (
      <section className="space-y-5">
        <div className="space-y-1">
          <h2 className="text-xl font-semibold text-foreground">General</h2>
          <p className="text-sm text-muted-foreground">Organization details could not be loaded.</p>
        </div>
        <QueryError message="Failed to load organization settings." onRetry={() => refetch()} />
      </section>
    );
  }

  const fallbackOrganization = organizationsData?.items.find(
    (organization) => organization.id !== activeOrgId && organization.is_personal,
  );

  return (
    <>
      <section className="space-y-5">
        <div className="space-y-1">
          <h2 className="text-xl font-semibold text-foreground">General</h2>
          <p className="text-sm text-muted-foreground">Update organization details for your active workspace.</p>
        </div>
        <Form {...form}>
          <form
            onSubmit={form.handleSubmit(async (data) => {
              if (!activeOrgId || !activeOrganization) {
                return;
              }

              const currentDescription =
                typeof activeOrganization.settings?.description === "string"
                  ? activeOrganization.settings.description
                  : "";

              const patch: {
                name?: string;
                slug?: string;
                settings?: Record<string, unknown>;
              } = {};

              if (data.name.trim() !== activeOrganization.name) {
                patch.name = data.name.trim();
              }
              if (data.slug.trim() !== activeOrganization.slug) {
                patch.slug = data.slug.trim();
              }
              if ((data.description ?? "").trim() !== currentDescription) {
                patch.settings = {
                  ...(activeOrganization.settings ?? {}),
                  description: (data.description ?? "").trim(),
                };
              }

              if (Object.keys(patch).length === 0) {
                return;
              }

              try {
                await updateOrgMutation.mutateAsync(patch);
                toast.success("Organization updated", {
                  description: "Your organization settings have been saved.",
                });
              } catch (error) {
                toast.error("Error", {
                  description: getErrorMessage(error),
                });
              }
            })}
            className="space-y-4"
          >
            <FormField
              control={form.control}
              name="name"
              render={({ field }) => (
                <FormItem className="w-full max-w-[28rem]">
                  <FormLabel>Name</FormLabel>
                  <FormControl>
                    <Input placeholder="Acme Corp" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="slug"
              render={({ field }) => (
                <FormItem className="w-full max-w-[28rem]">
                  <FormLabel>Slug</FormLabel>
                  <FormControl>
                    <Input placeholder="acme-corp" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="description"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Description</FormLabel>
                  <FormControl>
                    <Textarea
                      placeholder="Describe your organization"
                      className="min-h-24"
                      value={field.value ?? ""}
                      onChange={field.onChange}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <div className="flex justify-end gap-3">
              <Button
                type="button"
                variant="destructive"
                className="h-10 min-w-36 justify-center"
                onClick={() => setShowDeleteConfirm(true)}
                disabled={activeOrganization?.is_personal}
              >
                Delete Organization
              </Button>
              <Button type="submit" className="h-10 min-w-36 justify-center" disabled={updateOrgMutation.isPending}>
                {updateOrgMutation.isPending ? "Saving..." : "Save Changes"}
              </Button>
            </div>
            {activeOrganization?.is_personal ? (
              <p className="text-xs text-muted-foreground">Personal organizations cannot be deleted.</p>
            ) : null}
          </form>
        </Form>
      </section>

      <AlertDialog open={showDeleteConfirm} onOpenChange={setShowDeleteConfirm}>
        <AlertDialogContent variant="destructive">
          <AlertDialogHeader>
            <AlertDialogTitle>Delete organization?</AlertDialogTitle>
            <AlertDialogDescription>
              This action cannot be undone and permanently deletes {activeOrganization?.name}.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              variant="destructive"
              onClick={() => {
                if (!activeOrgId) {
                  return;
                }
                deleteOrgMutation.mutate(activeOrgId, {
                  onSuccess: () => {
                    if (fallbackOrganization) {
                      setActiveOrg(fallbackOrganization.id);
                    } else {
                      clearOrg();
                    }
                    toast.success("Organization deleted", {
                      description: "The organization has been permanently deleted.",
                    });
                    navigate("/");
                  },
                  onError: (error) => {
                    toast.error("Error", {
                      description: getErrorMessage(error),
                    });
                  },
                });
              }}
              disabled={deleteOrgMutation.isPending}
            >
              {deleteOrgMutation.isPending ? "Deleting..." : "Delete Organization"}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
}
