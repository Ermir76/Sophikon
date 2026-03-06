import { useState, useEffect } from "react";
import { useNavigate } from "react-router";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";

import { Button } from "@/shared/ui/button";
import { Separator } from "@/shared/ui/separator";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/shared/ui/card";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/shared/ui/form";
import { Input } from "@/shared/ui/input";
import { toast } from "sonner";
import { useOrgStore } from "@/features/organizations/store/org-store";
import {
  useOrganization,
  useUpdateOrganization,
  useDeleteOrganization,
} from "@/features/organizations/hooks/useOrganizations";
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

const orgSchema = z.object({
  name: z.string().min(2, "Name must be at least 2 characters"),
  slug: z
    .string()
    .min(2, "Slug must be at least 2 characters")
    .regex(
      /^[a-z0-9]+(?:-[a-z0-9]+)*$/,
      "Slug must contain only lowercase letters, numbers, and hyphens.",
    ),
});

type OrgFormValues = z.infer<typeof orgSchema>;

import { PageShell } from "@/shared/components/layout/PageShell";
import { PageHeader } from "@/shared/components/layout/PageHeader";
import { PageLoading } from "@/shared/components/state/PageLoading";

export default function OrgSettingsPage() {
  const shellClassName = "h-full overflow-y-auto";
  const navigate = useNavigate(); // Add hook
  const activeOrgId = useOrgStore((state) => state.activeOrgId);
  const clearOrg = useOrgStore((state) => state.clear); // Add clear action
  const {
    data: activeOrganization,
    isLoading,
    isError,
    refetch,
  } = useOrganization(activeOrgId);
  const updateOrgMutation = useUpdateOrganization(activeOrgId);

  const form = useForm<OrgFormValues>({
    resolver: zodResolver(orgSchema),
    defaultValues: {
      name: "",
      slug: "",
    },
  });

  useEffect(() => {
    if (activeOrganization) {
      form.reset({
        name: activeOrganization.name,
        slug: activeOrganization.slug,
      });
    }
  }, [activeOrganization, form]);

  const onSubmit = async (data: OrgFormValues) => {
    if (!activeOrgId) return;
    try {
      await updateOrgMutation.mutateAsync(data);
      toast.success("Organization updated", {
        description: "Your organization settings have been saved.",
      });
    } catch (error) {
      toast.error("Error", {
        description: getErrorMessage(error),
      });
    }
  };

  // Add Delete Mutation
  const deleteOrgMutation = useDeleteOrganization();

  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

  if (isLoading) {
    return (
      <PageShell className={shellClassName}>
        <PageLoading message="Loading organization details..." />
      </PageShell>
    );
  }

  if (isError) {
    return (
      <PageShell className={shellClassName}>
        <QueryError
          message="Failed to load organization settings."
          onRetry={() => refetch()}
        />
      </PageShell>
    );
  }

  return (
    <PageShell className={shellClassName}>
      <PageHeader
        title="Organization Settings"
        description="Manage your organization details."
      />

      <div className="space-y-4">
        <Card className="bg-card/70">
          <CardHeader>
            <CardTitle>General Information</CardTitle>
            <CardDescription>
              Update your organization's name and identifier.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Form {...form}>
              <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-3.5">
                <FormField
                  control={form.control}
                  name="name"
                  render={({ field }) => (
                    <FormItem>
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
                    <FormItem>
                      <FormLabel>Slug</FormLabel>
                      <FormControl>
                        <Input placeholder="acme-corp" {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <div className="flex justify-end">
                  <Button type="submit" size="sm" className="h-8 px-3 text-xs" disabled={updateOrgMutation.isPending}>
                    {updateOrgMutation.isPending ? "Saving..." : "Save Changes"}
                  </Button>
                </div>
              </form>
            </Form>
          </CardContent>
        </Card>
        <div className="pt-1">
          <h3 className="text-sm font-semibold uppercase tracking-wide text-destructive">Danger Zone</h3>
          <p className="mt-1 text-sm text-muted-foreground">
            Irreversible actions for your organization.
          </p>
        </div>
        <Separator />
        <Card className="border-destructive/50 bg-card/70">
          <CardHeader>
            <CardTitle className="text-destructive">Delete Organization</CardTitle>
            <CardDescription>
              Permanently delete this organization and all its data. This action cannot be undone.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Button
              variant="destructive"
              size="sm"
              className="h-8 px-3 text-xs"
              onClick={() => setShowDeleteConfirm(true)}
              disabled={activeOrganization?.is_personal} // Personal orgs often can't be deleted
            >
              Delete Organization
            </Button>
            {activeOrganization?.is_personal && (
              <p className="mt-2 text-xs text-muted-foreground">
                Personal organizations cannot be deleted.
              </p>
            )}
          </CardContent>
        </Card>
      </div>

      <AlertDialog open={showDeleteConfirm} onOpenChange={setShowDeleteConfirm}>
        <AlertDialogContent variant="destructive">
          <AlertDialogHeader>
            <AlertDialogTitle>Are you absolutely sure?</AlertDialogTitle>
            <AlertDialogDescription>
              This action cannot be undone. This will permanently delete the organization
              <span className="font-semibold text-foreground"> {activeOrganization?.name} </span>
              and remove all associated data.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              variant="destructive"
              onClick={() => {
                if (!activeOrgId) return;
                deleteOrgMutation.mutate(activeOrgId, {
                  onSuccess: () => {
                    clearOrg();
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
    </PageShell>
  );
}
