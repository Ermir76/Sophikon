import { useState } from "react";
import { Loader2 } from "lucide-react";
import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
    DialogFooter,
} from "@/shared/ui/dialog";
import { Button } from "@/shared/ui/button";
import { Input } from "@/shared/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/shared/ui/select";
import { useResources } from "@/features/resources/hooks/useResources";
import { useCreateAssignment } from "@/features/tasks/hooks/useAssignments";
import { useTask } from "@/features/tasks/hooks/useTasks";
import { toast } from "sonner";

interface AddAssignmentDialogProps {
    projectId: string;
    taskId: string;
    isOpen: boolean;
    onClose: () => void;
}

export function AddAssignmentDialog({
    projectId,
    taskId,
    isOpen,
    onClose,
}: AddAssignmentDialogProps) {
    const [resourceId, setResourceId] = useState<string>("");
    const [units, setUnits] = useState<string>("1.0");

    const { data: resourcesData, isLoading: isLoadingResources } = useResources(projectId);
    const { data: task } = useTask(projectId, taskId);
    const createAssignment = useCreateAssignment(projectId, taskId);

    const availableResources = resourcesData?.items?.filter((r) => r.is_active) ?? [];

    const handleSubmit = () => {
        if (!resourceId) {
            toast.error("Please select a resource");
            return;
        }

        if (!task) {
            toast.error("Task data not available");
            return;
        }

        createAssignment.mutate(
            {
                resource_id: resourceId,
                units: parseFloat(units) || 1.0,
                start_date: task.start_date,
                finish_date: task.finish_date,
            },
            {
                onSuccess: () => {
                    toast.success("Assignment created");
                    setResourceId("");
                    setUnits("1.0");
                    onClose();
                },
                onError: () => toast.error("Failed to create assignment"),
            }
        );
    };

    const handleOpenChange = (open: boolean) => {
        if (!open) {
            setResourceId("");
            setUnits("1.0");
            onClose();
        }
    };

    return (
        <Dialog open={isOpen} onOpenChange={handleOpenChange}>
            <DialogContent className="sm:max-w-md">
                <DialogHeader>
                    <DialogTitle>Add Assignment</DialogTitle>
                </DialogHeader>

                <div className="space-y-4 py-4">
                    <div className="space-y-2">
                        <label className="text-sm font-medium">Resource</label>
                        {isLoadingResources ? (
                            <div className="flex justify-center py-4">
                                <Loader2 className="size-5 animate-spin text-muted-foreground" />
                            </div>
                        ) : (
                            <Select value={resourceId} onValueChange={setResourceId}>
                                <SelectTrigger>
                                    <SelectValue placeholder="Select a resource…" />
                                </SelectTrigger>
                                <SelectContent>
                                    {availableResources.length === 0 ? (
                                        <div className="px-2 py-3 text-sm text-muted-foreground text-center">
                                            No active resources. Create one first.
                                        </div>
                                    ) : (
                                        availableResources.map((resource) => (
                                            <SelectItem key={resource.id} value={resource.id}>
                                                <div className="flex items-center gap-2">
                                                    {resource.initials && (
                                                        <span className="inline-flex items-center justify-center size-5 rounded-full bg-primary/10 text-[8px] font-bold text-primary shrink-0">
                                                            {resource.initials}
                                                        </span>
                                                    )}
                                                    <span>{resource.name}</span>
                                                    <span className="text-muted-foreground text-xs">({resource.type})</span>
                                                </div>
                                            </SelectItem>
                                        ))
                                    )}
                                </SelectContent>
                            </Select>
                        )}
                    </div>

                    <div className="space-y-2">
                        <label className="text-sm font-medium">Units</label>
                        <Input
                            type="number"
                            value={units}
                            onChange={(e) => setUnits(e.target.value)}
                            min={0}
                            step={0.1}
                            placeholder="1.0 = 100%"
                        />
                        <p className="text-xs text-muted-foreground">1.0 = 100% allocation</p>
                    </div>
                </div>

                <DialogFooter>
                    <Button variant="outline" onClick={onClose}>
                        Cancel
                    </Button>
                    <Button
                        onClick={handleSubmit}
                        disabled={createAssignment.isPending || !resourceId}
                    >
                        {createAssignment.isPending ? (
                            <>
                                <Loader2 className="size-4 animate-spin" />
                                Adding…
                            </>
                        ) : (
                            "Add Assignment"
                        )}
                    </Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    );
}
