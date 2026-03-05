import { useState } from "react";
import { Loader2 } from "lucide-react";
import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
    DialogDescription,
    DialogFooter,
} from "@/shared/ui/dialog";
import { Button } from "@/shared/ui/button";
import { Input } from "@/shared/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/shared/ui/select";
import { useBulkUpdateTasks } from "@/features/tasks/hooks/useTasks";
import { toast } from "sonner";
import type { TaskUpdate } from "@/features/tasks/types";

interface BulkEditDialogProps {
    projectId: string;
    selectedTaskIds: string[];
    isOpen: boolean;
    onClose: () => void;
    onSuccess?: () => void;
}

export function BulkEditDialog({
    projectId,
    selectedTaskIds,
    isOpen,
    onClose,
    onSuccess,
}: BulkEditDialogProps) {
    const [percentComplete, setPercentComplete] = useState<string>("");
    const [priority, setPriority] = useState<string>("");

    const bulkUpdate = useBulkUpdateTasks(projectId);

    const handleSubmit = async () => {
        // Build update payload - only include fields that were changed
        const data: TaskUpdate = {};

        if (percentComplete !== "") {
            const val = parseFloat(percentComplete);
            if (isNaN(val) || val < 0 || val > 100) {
                toast.error("% Complete must be between 0 and 100");
                return;
            }
            data.percent_complete = val;
        }

        if (priority !== "") {
            data.priority = parseInt(priority, 10);
        }

        if (Object.keys(data).length === 0) {
            toast.error("No changes specified");
            return;
        }

        try {
            const result = await bulkUpdate.mutateAsync({
                tasks: selectedTaskIds.map((id) => ({ id, data })),
            });
            toast.success(`${result.succeeded} task(s) updated`);
            resetForm();
            onClose();
            onSuccess?.();
        } catch (error) {
            toast.error("Failed to update tasks");
        }
    };

    const resetForm = () => {
        setPercentComplete("");
        setPriority("");
    };

    const handleOpenChange = (open: boolean) => {
        if (!open) {
            resetForm();
            onClose();
        }
    };

    return (
        <Dialog open={isOpen} onOpenChange={handleOpenChange}>
            <DialogContent className="sm:max-w-md">
                <DialogHeader>
                    <DialogTitle>Bulk Edit {selectedTaskIds.length} Task{selectedTaskIds.length !== 1 ? "s" : ""}</DialogTitle>
                    <DialogDescription>
                        Only changed fields will be applied. Leave fields empty to skip them.
                    </DialogDescription>
                </DialogHeader>

                <div className="space-y-4 py-4">
                    <div className="space-y-2">
                        <label className="text-sm font-medium">% Complete</label>
                        <Input
                            type="number"
                            value={percentComplete}
                            onChange={(e) => setPercentComplete(e.target.value)}
                            min={0}
                            max={100}
                            step={5}
                            placeholder="Leave empty to skip"
                        />
                    </div>

                    <div className="space-y-2">
                        <label className="text-sm font-medium">Priority</label>
                        <Select value={priority} onValueChange={setPriority}>
                            <SelectTrigger>
                                <SelectValue placeholder="Leave empty to skip" />
                            </SelectTrigger>
                            <SelectContent>
                                <SelectItem value="100">Do Not Level (100)</SelectItem>
                                <SelectItem value="1000">Highest (1000)</SelectItem>
                                <SelectItem value="800">Very High (800)</SelectItem>
                                <SelectItem value="600">High (600)</SelectItem>
                                <SelectItem value="500">Medium (500)</SelectItem>
                                <SelectItem value="400">Low (400)</SelectItem>
                                <SelectItem value="200">Very Low (200)</SelectItem>
                                <SelectItem value="0">Lowest (0)</SelectItem>
                            </SelectContent>
                        </Select>
                    </div>
                </div>

                <DialogFooter>
                    <Button variant="outline" onClick={() => handleOpenChange(false)}>
                        Cancel
                    </Button>
                    <Button
                        onClick={handleSubmit}
                        disabled={bulkUpdate.isPending}
                    >
                        {bulkUpdate.isPending ? (
                            <>
                                <Loader2 className="size-4 animate-spin" />
                                Updating...
                            </>
                        ) : (
                            "Apply Changes"
                        )}
                    </Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    );
}
