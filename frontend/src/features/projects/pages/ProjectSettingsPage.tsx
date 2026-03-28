import { useState, useEffect } from "react";
import { useNavigate, useParams } from "react-router";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { toast } from "sonner";

import { Button } from "@/shared/ui/button";
import { Separator } from "@/shared/ui/separator";
import { Switch } from "@/shared/ui/switch";
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
import { Textarea } from "@/shared/ui/textarea";
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
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/shared/ui/tabs";

import { useProject, useUpdateProject, useDeleteProject } from "@/features/projects/hooks/useProjects";
import { ProjectMembersTab } from "@/features/projects/components/ProjectMembersTab";
import { getErrorMessage } from "@/shared/lib/errors";
import { QueryError } from "@/shared/components/QueryError";
import { ColorPicker } from "@/shared/components/ColorPicker";
import { PageShell } from "@/shared/components/layout/PageShell";
import { PageHeader } from "@/shared/components/layout/PageHeader";
import { PageLoading } from "@/shared/components/state/PageLoading";

const projectSchema = z.object({
  name: z.string().min(2, "Name must be at least 2 characters"),
  description: z.string().optional(),
  color: z.string().nullable().optional(),
  review_threshold: z.coerce.number().int().min(1).max(99),
  agent_enabled: z.boolean(),
});

type ProjectFormValues = z.infer<typeof projectSchema>;

export default function ProjectSettingsPage() {
  const shellClassName = "h-full overflow-y-auto";
  const { projectId } = useParams();
  const navigate = useNavigate();

  const {
    data: project,
    isLoading,
    isError,
    refetch
  } = useProject(projectId);

  const updateProjectMutation = useUpdateProject(projectId);
  const deleteProjectMutation = useDeleteProject(projectId);

  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [activeTab, setActiveTab] = useState("general");

  const form = useForm<ProjectFormValues>({
    resolver: zodResolver(projectSchema),
    defaultValues: {
      name: "",
      description: "",
      review_threshold: 80,
      agent_enabled: true,
    },
  });

  useEffect(() => {
    if (project) {
      form.reset({
        name: project.name,
        description: project.description || "",
        color: project.color ?? null,
        review_threshold:
          typeof project.settings?.status_thresholds?.IN_REVIEW === "number"
            ? project.settings.status_thresholds.IN_REVIEW
            : 80,
        agent_enabled: project.settings?.agent_enabled !== false,
      });
    }
  }, [project, form]);

  const onSubmit = async (data: ProjectFormValues) => {
    if (!projectId) return;
    try {
      await updateProjectMutation.mutateAsync({
        name: data.name,
        description: data.description,
        color: data.color,
        settings: {
          status_thresholds: {
            IN_REVIEW: data.review_threshold,
          },
          agent_enabled: data.agent_enabled,
        },
      });
      toast.success("Project updated", {
        description: "Your project settings have been saved.",
      });
    } catch (error) {
      toast.error("Error", {
        description: getErrorMessage(error),
      });
    }
  };

  const handleDelete = async () => {
    if (!projectId) return;
    try {
      await deleteProjectMutation.mutateAsync();
      toast.success("Project deleted", {
        description: "The project has been permanently deleted.",
      });
      navigate("/projects");
    } catch (error) {
      toast.error("Error", {
        description: getErrorMessage(error),
      });
    }
  };

  if (isLoading) {
    return (
      <PageShell className={shellClassName}>
        <PageLoading message="Loading project details..." />
      </PageShell>
    );
  }

  if (isError) {
    return (
      <PageShell className={shellClassName}>
        <QueryError
          message="Failed to load project settings."
          onRetry={() => refetch()}
        />
      </PageShell>
    );
  }

  return (
    <PageShell className={shellClassName}>
      <PageHeader
        title="Project Settings"
        description={`Manage settings for project: ${project?.name}`}
      />

      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <TabsList variant="line">
          <TabsTrigger value="general">General</TabsTrigger>
          <TabsTrigger value="members">Members</TabsTrigger>
        </TabsList>

        <TabsContent value="general" className="space-y-4">
          <Card className="bg-card/70">
            <CardHeader>
              <CardTitle>General Information</CardTitle>
              <CardDescription>
                Update your project's name and description.
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
                          <Input placeholder="Project Name" {...field} />
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
                            placeholder="Project description..."
                            className="resize-none"
                            {...field}
                          />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  <FormField
                    control={form.control}
                    name="color"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Gantt Color</FormLabel>
                        <FormControl>
                          <ColorPicker
                            value={field.value ?? null}
                            onChange={field.onChange}
                          />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  <FormField
                    control={form.control}
                    name="review_threshold"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Review Threshold (%)</FormLabel>
                        <FormControl>
                          <Input type="number" min={1} max={99} {...field} />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  <FormField
                    control={form.control}
                    name="agent_enabled"
                    render={({ field }) => (
                      <FormItem className="flex items-center justify-between rounded-md border p-3">
                        <div className="space-y-0.5">
                          <FormLabel>AI Agent</FormLabel>
                          <p className="text-xs text-muted-foreground">
                            Enable AI chat and proactive agent actions for this project.
                          </p>
                        </div>
                        <FormControl>
                          <Switch
                            checked={field.value}
                            onCheckedChange={field.onChange}
                          />
                        </FormControl>
                      </FormItem>
                    )}
                  />

                  <div className="flex justify-end">
                    <Button
                      type="submit"
                      size="sm"
                      className="h-8 px-3 text-xs"
                      disabled={updateProjectMutation.isPending}
                    >
                      {updateProjectMutation.isPending ? "Saving..." : "Save Changes"}
                    </Button>
                  </div>
                </form>
              </Form>
            </CardContent>
          </Card>
          <div className="pt-1">
            <h3 className="text-sm font-semibold uppercase tracking-wide text-destructive">Danger Zone</h3>
            <p className="mt-1 text-sm text-muted-foreground">
              Irreversible actions for your project.
            </p>
          </div>
          <Separator />

          <Card className="border-destructive/50 bg-card/70">
            <CardHeader>
              <CardTitle className="text-destructive">Delete Project</CardTitle>
              <CardDescription>
                Permanently delete this project and all its tasks. This action cannot be undone.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Button
                variant="destructive"
                size="sm"
                className="h-8 px-3 text-xs"
                onClick={() => setShowDeleteConfirm(true)}
              >
                Delete Project
              </Button>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="members">
          {projectId ? (
            <ProjectMembersTab projectId={projectId} />
          ) : (
            <QueryError
              message="Missing project ID."
              onRetry={() => refetch()}
            />
          )}
        </TabsContent>
      </Tabs>

      <AlertDialog open={showDeleteConfirm} onOpenChange={setShowDeleteConfirm}>
        <AlertDialogContent variant="destructive">
          <AlertDialogHeader>
            <AlertDialogTitle>Are you absolutely sure?</AlertDialogTitle>
            <AlertDialogDescription>
              This action cannot be undone. This will permanently delete the project
              <span className="font-semibold text-foreground"> {project?.name} </span>
              and remove all associated data.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              variant="destructive"
              onClick={handleDelete}
              disabled={deleteProjectMutation.isPending}
            >
              {deleteProjectMutation.isPending ? "Deleting..." : "Delete Project"}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </PageShell>
  );
}
