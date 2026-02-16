import { useEffect } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";

import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { toast } from "sonner";
import { useOrgStore } from "@/store/org-store";
import {
  useOrganization,
  useUpdateOrganization,
} from "@/hooks/useOrganizations";
import { QueryError } from "@/components/QueryError";
import { getErrorMessage } from "@/lib/errors";

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
  const activeOrgId = useOrgStore((state) => state.activeOrgId);
  const {
    data: activeOrganization,
    isLoading,
    isError,
    refetch,
  } = useOrganization(activeOrgId || "");
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
    <div className="space-y-6 p-6">
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
  );
}
