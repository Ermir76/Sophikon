import { useState, useEffect } from "react";
import { useNavigate, useParams } from "react-router";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { toast } from "sonner";

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

import { useProject, useUpdateProject, useDeleteProject } from "@/features/projects/hooks/useProjects";
import { getErrorMessage } from "@/shared/lib/errors";
import { QueryError } from "@/shared/components/QueryError";

const projectSchema = z.object({
  name: z.string().min(2, "Name must be at least 2 characters"),
  description: z.string().optional(),
});

type ProjectFormValues = z.infer<typeof projectSchema>;

export default function ProjectSettingsPage() {
  const { projectId } = useParams();
  const navigate = useNavigate();

  const {
    data: project,
    isLoading,
    isError,
    refetch
  } = useProject(projectId || "");

  const updateProjectMutation = useUpdateProject(projectId || "");
  const deleteProjectMutation = useDeleteProject(projectId || "");

  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

  const form = useForm<ProjectFormValues>({
    resolver: zodResolver(projectSchema),
    defaultValues: {
      name: "",
      description: "",
    },
  });

  useEffect(() => {
    if (project) {
      form.reset({
        name: project.name,
        description: project.description || "",
      });
    }
  }, [project, form]);

  const onSubmit = async (data: ProjectFormValues) => {
    if (!projectId) return;
    try {
      await updateProjectMutation.mutateAsync(data);
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
    return <div className="p-4">Loading project details...</div>;
  }

  if (isError) {
    return (
      <QueryError
        message="Failed to load project settings."
        onRetry={() => refetch()}
      />
    );
  }

  return (
    <div className="space-y-8 p-6">
      <div className="space-y-6">
        <div>
          <h3 className="text-2xl font-medium">Project Settings</h3>
          <p className="text-sm text-muted-foreground">
            Manage settings for project: {project?.name}
          </p>
        </div>
        <Separator />

        <Card>
          <CardHeader>
            <CardTitle>General Information</CardTitle>
            <CardDescription>
              Update your project's name and description.
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

                <div className="flex justify-end">
                  <Button type="submit" disabled={updateProjectMutation.isPending}>
                    {updateProjectMutation.isPending ? "Saving..." : "Save Changes"}
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
            Irreversible actions for your project.
          </p>
        </div>
        <Separator className="gradient-divider-destructive" />

        <Card className="gradient-border-destructive bg-destructive/5">
          <CardHeader>
            <CardTitle className="text-destructive">Delete Project</CardTitle>
            <CardDescription>
              Permanently delete this project and all its tasks. This action cannot be undone.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Button
              variant="destructive"
              onClick={() => setShowDeleteConfirm(true)}
            >
              Delete Project
            </Button>
          </CardContent>
        </Card>
      </div>

      <AlertDialog open={showDeleteConfirm} onOpenChange={setShowDeleteConfirm}>
        <AlertDialogContent>
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
              onClick={handleDelete}
              className="bg-destructive hover:bg-destructive/90"
              disabled={deleteProjectMutation.isPending}
            >
              {deleteProjectMutation.isPending ? "Deleting..." : "Delete Project"}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
