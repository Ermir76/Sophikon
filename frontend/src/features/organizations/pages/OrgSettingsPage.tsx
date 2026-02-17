import { useState, useEffect } from "react";
import { useNavigate } from "react-router";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useMutation, useQueryClient } from "@tanstack/react-query";

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
} from "@/features/organizations/hooks/useOrganizations";
import { QueryError } from "@/shared/components/QueryError";
import { getErrorMessage } from "@/shared/lib/errors";
import { organizationService } from "@/features/organizations/api/organization.service";
import { orgKeys } from "@/features/organizations/hooks/useOrganizations";
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

export default function OrgSettingsPage() {
  const navigate = useNavigate(); // Add hook
  const activeOrgId = useOrgStore((state) => state.activeOrgId);
  const clearOrg = useOrgStore((state) => state.clear); // Add clear action
  const {
    data: activeOrganization,
    isLoading,
    isError,
    refetch,
  } = useOrganization(activeOrgId || "");
  const queryClient = useQueryClient();
  const updateOrgMutation = useUpdateOrganization(activeOrgId || "");

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
  const deleteOrgMutation = useMutation({
    mutationFn: () => organizationService.delete(activeOrgId || ""),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: orgKeys.list });
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

  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

  if (isLoading) {
    return <div className="p-4">Loading organization details...</div>;
  }

  if (isError) {
    return (
      <QueryError
        message="Failed to load organization settings."
        onRetry={() => refetch()}
      />
    );
  }

  return (
    <div className="space-y-8 p-6">
      <div className="space-y-6">
        <div>
          <h3 className="text-2xl font-medium">Organization Settings</h3>
          <p className="text-sm text-muted-foreground">
            Manage your organization details.
          </p>
        </div>
        <Separator />
        <Card>
          <CardHeader>
            <CardTitle>General Information</CardTitle>
            <CardDescription>
              Update your organization's name and identifier.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Form {...form}>
              <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
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
                  <Button type="submit" disabled={updateOrgMutation.isPending}>
                    {updateOrgMutation.isPending ? "Saving..." : "Save Changes"}
                  </Button>
                </div>
              </form>
            </Form>
          </CardContent>
        </Card>
      </div>

      <div className="space-y-6">
        <div>
          <h3 className="text-lg font-medium text-destructive">Danger Zone</h3>
          <p className="text-sm text-muted-foreground">
            Irreversible actions for your organization.
          </p>
        </div>
        <Separator className="bg-destructive/20" />
        <Card className="border-destructive/20 bg-destructive/5">
          <CardHeader>
            <CardTitle className="text-destructive">Delete Organization</CardTitle>
            <CardDescription>
              Permanently delete this organization and all its data. This action cannot be undone.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Button
              variant="destructive"
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
        <AlertDialogContent>
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
              onClick={() => deleteOrgMutation.mutate()}
              className="bg-destructive hover:bg-destructive/90"
              disabled={deleteOrgMutation.isPending}
            >
              {deleteOrgMutation.isPending ? "Deleting..." : "Delete Organization"}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
