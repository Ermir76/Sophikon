import { useEffect, useState, useCallback } from "react";
import { Link } from "react-router";
import { format } from "date-fns";
import {
  Plus,
  MoreHorizontal,
  Loader2,
  Folder,
  Calendar as CalendarIcon,
} from "lucide-react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";

import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Calendar } from "@/components/ui/calendar";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";

import { toast } from "sonner";
import { useOrgStore } from "@/store/org-store";
import { projectService } from "@/services/project";
import type { Project } from "@/types/project";

const projectSchema = z.object({
  name: z.string().min(1, "Name is required"),
  description: z.string().optional(),
  start_date: z.date(),
});

type ProjectFormValues = z.infer<typeof projectSchema>;

export default function ProjectsPage() {
  const activeOrganization = useOrgStore((state) => state.activeOrganization);
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(false);
  const [createOpen, setCreateOpen] = useState(false);

  const form = useForm<ProjectFormValues>({
    resolver: zodResolver(projectSchema),
    defaultValues: {
      name: "",
      description: "",
    },
  });

  const fetchProjects = useCallback(async () => {
    if (!activeOrganization) return;
    setLoading(true);
    try {
      const response = await projectService.list(activeOrganization.id);
      setProjects(response.items);
    } catch (error) {
      toast.error("Error", {
        description: "Failed to fetch projects.",
      });
    } finally {
      setLoading(false);
    }
  }, [activeOrganization]);

  useEffect(() => {
    fetchProjects();
  }, [fetchProjects]);

  const onCreate = async (data: ProjectFormValues) => {
    if (!activeOrganization) return;
    try {
      await projectService.create(activeOrganization.id, {
        name: data.name,
        description: data.description,
        start_date: format(data.start_date, "yyyy-MM-dd"),
      });

      toast.success("Project created", {
        description: `Project "${data.name}" has been created.`,
      });
      setCreateOpen(false);
      form.reset();
      await fetchProjects(); // Await fetchProjects
    } catch (error) {
      toast.error("Error", {
        description: "Failed to create project.",
      });
    }
  };

  if (!activeOrganization) {
    return <div className="p-4">Please select an organization.</div>;
  }

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-2xl font-medium">Projects</h3>
          <p className="text-sm text-muted-foreground">
            Manage your organization's projects.
          </p>
        </div>
        <Dialog open={createOpen} onOpenChange={setCreateOpen}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="mr-2 size-4" />
              New Project
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Create Project</DialogTitle>
              <DialogDescription>
                Add a new project to {activeOrganization.name}.
              </DialogDescription>
            </DialogHeader>
            <Form {...form}>
              <form
                onSubmit={form.handleSubmit(onCreate)}
                className="space-y-4"
              >
                <FormField
                  control={form.control}
                  name="name"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Name</FormLabel>
                      <FormControl>
                        <Input placeholder="Mobile App Redesign" {...field} />
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
                          placeholder="Project goals and scope..."
                          {...field}
                        />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <FormField
                  control={form.control}
                  name="start_date"
                  render={({ field }) => (
                    <FormItem className="flex flex-col">
                      <FormLabel>Start Date</FormLabel>
                      <Popover>
                        <PopoverTrigger asChild>
                          <FormControl>
                            <Button
                              variant={"outline"}
                              className={cn(
                                "w-full pl-3 text-left font-normal",
                                !field.value && "text-muted-foreground",
                              )}
                            >
                              {field.value ? (
                                format(field.value, "PPP")
                              ) : (
                                <span>Pick a date</span>
                              )}
                              <CalendarIcon className="ml-auto size-4 opacity-50" />
                            </Button>
                          </FormControl>
                        </PopoverTrigger>
                        <PopoverContent className="w-auto p-0" align="start">
                          <Calendar
                            mode="single"
                            selected={field.value}
                            onSelect={field.onChange}
                            disabled={(date) => date < new Date("1900-01-01")}
                            initialFocus
                          />
                        </PopoverContent>
                      </Popover>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <DialogFooter>
                  <Button type="submit">Create Project</Button>
                </DialogFooter>
              </form>
            </Form>
          </DialogContent>
        </Dialog>
      </div>

      {loading ? (
        <div className="flex justify-center p-8">
          <Loader2 className="size-8 animate-spin text-muted-foreground" />
        </div>
      ) : projects.length === 0 ? (
        <div className="flex flex-col items-center justify-center rounded-md border border-dashed p-8 text-center animate-in fade-in-50">
          <div className="mx-auto flex size-12 items-center justify-center rounded-full bg-accent">
            <Folder className="size-6 text-muted-foreground" />
          </div>
          <h3 className="mt-4 text-lg font-semibold">No projects</h3>
          <p className="mb-4 mt-2 text-sm text-muted-foreground">
            You haven't created any projects yet.
          </p>
          <Button variant="outline" onClick={() => setCreateOpen(true)}>
            Create your first project
          </Button>
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {projects.map((project) => (
            <Card
              key={project.id}
              className="hover:bg-muted/50 transition-colors"
            >
              <CardHeader className="flex flex-row items-start justify-between space-y-0 pb-2">
                <CardTitle className="text-base font-medium">
                  <Link
                    to={`/projects/${project.id}/tasks`}
                    className="hover:underline"
                  >
                    {project.name}
                  </Link>
                </CardTitle>
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button variant="ghost" className="size-8 p-0">
                      <span className="sr-only">Open menu</span>
                      <MoreHorizontal className="size-4" />
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end">
                    <DropdownMenuItem asChild>
                      <Link to={`/projects/${project.id}/settings`}>
                        Settings
                      </Link>
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              </CardHeader>
              <CardContent>
                <div className="text-sm text-muted-foreground line-clamp-2 min-h-[40px]">
                  {project.description || "No description provided."}
                </div>
                <div className="mt-4 text-xs text-muted-foreground">
                  Updated {format(new Date(project.updated_at), "MMM d, yyyy")}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
