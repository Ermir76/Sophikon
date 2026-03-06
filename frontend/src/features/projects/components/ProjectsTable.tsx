import { useMemo, useState } from "react";
import { Link } from "react-router";
import { format, isValid, parseISO } from "date-fns";
import { GripVertical, MoreHorizontal, PanelRight, Settings2, SquarePen, Trash2 } from "lucide-react";
import {
  DndContext,
  KeyboardSensor,
  PointerSensor,
  closestCenter,
  useSensor,
  useSensors,
} from "@dnd-kit/core";
import type { DragEndEvent } from "@dnd-kit/core";
import {
  SortableContext,
  arrayMove,
  sortableKeyboardCoordinates,
  useSortable,
  verticalListSortingStrategy,
} from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import { restrictToVerticalAxis } from "@dnd-kit/modifiers";
import { toast } from "sonner";

import { Button } from "@/shared/ui/button";
import { Badge } from "@/shared/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/shared/ui/table";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/shared/ui/dropdown-menu";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/shared/ui/dialog";
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
import { Input } from "@/shared/ui/input";
import { Textarea } from "@/shared/ui/textarea";
import { ColorPicker } from "@/shared/components/ColorPicker";
import { getProjectVisualMeta, getProjectVisualState } from "@/features/projects/lib/project-status";
import { useDeleteProject, useUpdateProject } from "@/features/projects/hooks/useProjects";
import { getErrorMessage } from "@/shared/lib/errors";

import type { Project } from "@/features/projects/types";

interface ProjectsTableProps {
  projects: Project[];
}

interface SortableProjectRowProps {
  project: Project;
  now: Date;
  formatDate: (value?: string | null) => string;
}

function ProjectRowActions({ project }: { project: Project }) {
  const updateProjectMutation = useUpdateProject(project.id);
  const deleteProjectMutation = useDeleteProject(project.id);
  const [editorOpen, setEditorOpen] = useState(false);
  const [deleteOpen, setDeleteOpen] = useState(false);
  const [draftName, setDraftName] = useState(project.name);
  const [draftDescription, setDraftDescription] = useState(project.description || "");
  const [draftColor, setDraftColor] = useState<string | null>(project.color ?? null);

  const openEditor = () => {
    setDraftName(project.name);
    setDraftDescription(project.description || "");
    setDraftColor(project.color ?? null);
    setEditorOpen(true);
  };

  const saveProject = async () => {
    try {
      await updateProjectMutation.mutateAsync({
        name: draftName.trim() || project.name,
        description: draftDescription,
        color: draftColor,
      });
      toast.success("Project updated");
      setEditorOpen(false);
    } catch (error) {
      toast.error("Failed to update project", {
        description: getErrorMessage(error),
      });
    }
  };

  const deleteProject = async () => {
    try {
      await deleteProjectMutation.mutateAsync();
      toast.success("Project deleted");
      setDeleteOpen(false);
    } catch (error) {
      toast.error("Failed to delete project", {
        description: getErrorMessage(error),
      });
    }
  };

  return (
    <div onClick={(event) => event.stopPropagation()}>
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button variant="ghost" size="icon" className="size-8">
            <span className="sr-only">Open menu</span>
            <MoreHorizontal className="size-4" />
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end">
          <DropdownMenuItem onSelect={openEditor}>
            <SquarePen className="size-4" />
            Edit Project
          </DropdownMenuItem>
          <DropdownMenuItem asChild>
            <Link to={`/projects/${project.id}/tasks`}>
              <PanelRight className="size-4" />
              Open Tasks
            </Link>
          </DropdownMenuItem>
          <DropdownMenuItem asChild>
            <Link to={`/projects/${project.id}/settings`}>
              <Settings2 className="size-4" />
              Advanced Settings
            </Link>
          </DropdownMenuItem>
          <DropdownMenuSeparator />
          <DropdownMenuItem
            className="text-destructive focus:text-destructive focus:bg-destructive/10"
            onSelect={() => setDeleteOpen(true)}
          >
            <Trash2 className="size-4" />
            Delete
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>

      <Dialog open={editorOpen} onOpenChange={setEditorOpen}>
        <DialogContent className="sm:max-w-xl">
          <DialogHeader>
            <DialogTitle>Edit Project</DialogTitle>
            <DialogDescription>Quick project updates without leaving the table.</DialogDescription>
          </DialogHeader>
          <div className="space-y-3">
            <div className="space-y-1.5">
              <label htmlFor={`project-name-${project.id}`} className="text-sm font-medium">
                Name
              </label>
              <Input
                id={`project-name-${project.id}`}
                value={draftName}
                onChange={(event) => setDraftName(event.target.value)}
                placeholder="Project name"
              />
            </div>
            <div className="space-y-1.5">
              <label htmlFor={`project-description-${project.id}`} className="text-sm font-medium">
                Description
              </label>
              <Textarea
                id={`project-description-${project.id}`}
                value={draftDescription}
                onChange={(event) => setDraftDescription(event.target.value)}
                placeholder="Project description..."
                className="min-h-28 resize-none"
              />
            </div>
            <div className="space-y-1.5">
              <p className="text-sm font-medium">Gantt Color</p>
              <ColorPicker value={draftColor} onChange={setDraftColor} />
            </div>
          </div>
          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => setEditorOpen(false)}>
              Cancel
            </Button>
            <Button type="button" onClick={saveProject} disabled={updateProjectMutation.isPending}>
              {updateProjectMutation.isPending ? "Saving..." : "Save"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <AlertDialog open={deleteOpen} onOpenChange={setDeleteOpen}>
        <AlertDialogContent variant="destructive">
          <AlertDialogHeader>
            <AlertDialogTitle>Delete project?</AlertDialogTitle>
            <AlertDialogDescription>
              This will permanently delete "{project.name}" and all related tasks.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              variant="destructive"
              onClick={deleteProject}
              disabled={deleteProjectMutation.isPending}
            >
              {deleteProjectMutation.isPending ? "Deleting..." : "Delete"}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}

function ProjectDescriptionCell({ project }: { project: Project }) {
  const updateProjectMutation = useUpdateProject(project.id);
  const [editorOpen, setEditorOpen] = useState(false);
  const [draftDescription, setDraftDescription] = useState(project.description || "");

  const openEditor = () => {
    setDraftDescription(project.description || "");
    setEditorOpen(true);
  };

  const saveDescription = async () => {
    try {
      await updateProjectMutation.mutateAsync({
        description: draftDescription,
      });
      toast.success("Description updated");
      setEditorOpen(false);
    } catch (error) {
      toast.error("Failed to update description", {
        description: getErrorMessage(error),
      });
    }
  };

  return (
    <>
      <button
        type="button"
        className="w-full text-left text-xs text-muted-foreground hover:text-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
        onClick={openEditor}
      >
        <span className="block truncate">{project.description || "No description provided."}</span>
      </button>
      <Dialog open={editorOpen} onOpenChange={setEditorOpen}>
        <DialogContent className="sm:max-w-xl">
          <DialogHeader>
            <DialogTitle>Edit Description</DialogTitle>
            <DialogDescription>{project.name}</DialogDescription>
          </DialogHeader>
          <Textarea
            value={draftDescription}
            onChange={(event) => setDraftDescription(event.target.value)}
            placeholder="Project description..."
            className="min-h-28 resize-none"
          />
          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => setEditorOpen(false)}>
              Cancel
            </Button>
            <Button type="button" onClick={saveDescription} disabled={updateProjectMutation.isPending}>
              {updateProjectMutation.isPending ? "Saving..." : "Save"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}

function SortableProjectRow({
  project,
  now,
  formatDate,
}: SortableProjectRowProps) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: project.id });

  const visualState = getProjectVisualState(project, now);
  const visualMeta = getProjectVisualMeta(visualState);
  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.8 : 1,
  };

  return (
    <TableRow
      ref={setNodeRef}
      style={style}
      className={isDragging ? "relative z-10 h-11 bg-muted shadow-sm" : "h-11"}
    >
      <TableCell
        className="w-10 cursor-grab text-center active:cursor-grabbing"
        aria-label={`Reorder ${project.name}`}
        {...attributes}
        {...listeners}
      >
        <div className="flex items-center justify-center text-muted-foreground">
          <GripVertical className="size-4" />
        </div>
      </TableCell>
      <TableCell className="min-w-0">
        <Link
          to={`/projects/${project.id}/tasks`}
          className="block truncate font-medium hover:underline"
        >
          {project.name}
        </Link>
      </TableCell>
      <TableCell className="max-w-0 pr-8 text-xs text-muted-foreground">
        <ProjectDescriptionCell project={project} />
      </TableCell>
      <TableCell className="pl-3">
        <Badge variant="outline" className={visualMeta.badgeClassName}>
          {visualMeta.label}
        </Badge>
      </TableCell>
      <TableCell className="text-sm whitespace-nowrap text-muted-foreground tabular-nums">
        {formatDate(project.finish_date)}
      </TableCell>
      <TableCell className="text-sm whitespace-nowrap text-muted-foreground tabular-nums">
        {formatDate(project.updated_at)}
      </TableCell>
      <TableCell className="sticky right-0 z-10 w-12 bg-background">
        <ProjectRowActions project={project} />
      </TableCell>
    </TableRow>
  );
}

export function ProjectsTable({ projects }: ProjectsTableProps) {
  const now = new Date();
  const [orderIds, setOrderIds] = useState<string[]>(() => projects.map((project) => project.id));

  const orderedProjects = useMemo(() => {
    const projectMap = new Map(projects.map((project) => [project.id, project]));
    const known = orderIds
      .map((id) => projectMap.get(id))
      .filter((project): project is Project => Boolean(project));
    const knownIds = new Set(known.map((project) => project.id));
    const rest = projects.filter((project) => !knownIds.has(project.id));
    return [...known, ...rest];
  }, [orderIds, projects]);

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 5 } }),
    useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates }),
  );

  const formatDate = (value?: string | null) => {
    if (!value) return "-";
    const parsed = parseISO(value);
    return isValid(parsed) ? format(parsed, "MMM d, yyyy") : "-";
  };

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;
    if (!over || active.id === over.id) return;

    const oldIndex = orderedProjects.findIndex((project) => project.id === active.id);
    const newIndex = orderedProjects.findIndex((project) => project.id === over.id);
    if (oldIndex < 0 || newIndex < 0) return;

    const reordered = arrayMove(orderedProjects, oldIndex, newIndex);
    const reorderedIds = reordered.map((project) => project.id);
    const visibleIds = new Set(orderedProjects.map((project) => project.id));

    setOrderIds((current) => [
      ...reorderedIds,
      ...current.filter((id) => !visibleIds.has(id)),
    ]);
  };

  return (
    <DndContext
      sensors={sensors}
      collisionDetection={closestCenter}
      modifiers={[restrictToVerticalAxis]}
      onDragEnd={handleDragEnd}
    >
      <div className="overflow-hidden rounded-lg border bg-card/70">
        <Table>
          <TableHeader className="sticky top-0 z-20 bg-card/95 backdrop-blur supports-[backdrop-filter]:bg-card/85">
            <TableRow>
              <TableHead className="w-10" />
              <TableHead className="w-[32%]">Project</TableHead>
              <TableHead className="w-[26%] pr-8">Description</TableHead>
              <TableHead className="w-[12%] pl-3">Status</TableHead>
              <TableHead className="w-[14%]">Due</TableHead>
              <TableHead className="w-[14%]">Updated</TableHead>
              <TableHead className="sticky right-0 z-10 w-12 bg-card/95 backdrop-blur supports-[backdrop-filter]:bg-card/85" />
            </TableRow>
          </TableHeader>
          <TableBody>
            <SortableContext
              items={orderedProjects.map((project) => project.id)}
              strategy={verticalListSortingStrategy}
            >
              {orderedProjects.map((project) => (
                <SortableProjectRow
                  key={project.id}
                  project={project}
                  now={now}
                  formatDate={formatDate}
                />
              ))}
            </SortableContext>
          </TableBody>
        </Table>
      </div>
    </DndContext>
  );
}
