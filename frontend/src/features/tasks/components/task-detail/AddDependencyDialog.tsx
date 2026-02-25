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
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/shared/ui/select";
import { useTasks } from "@/features/tasks/hooks/useTasks";
import { useCreateDependency } from "@/features/tasks/hooks/useDependencies";
import { toast } from "sonner";

interface AddDependencyDialogProps {
    projectId: string;
    successorTaskId: string;
    isOpen: boolean;
    onClose: () => void;
}

export function AddDependencyDialog({
    projectId,
    successorTaskId,
    isOpen,
    onClose
}: AddDependencyDialogProps) {
    const [predecessorId, setPredecessorId] = useState<string>("");
    const [dependencyType, setDependencyType] = useState<"FS" | "FF" | "SS" | "SF">("FS");

    const { data: tasksData, isLoading: isLoadingTasks } = useTasks(projectId);
    const createDependency = useCreateDependency(projectId);

    // Filter out the current task itself to prevent self-dependency
    const availablePredecessors = tasksData?.items?.filter(t => t.id !== successorTaskId) || [];

    const handleSubmit = () => {
        if (!predecessorId) {
            toast.error("Please select a predecessor task");
            return;
        }

        createDependency.mutate(
            {
                predecessor_id: predecessorId,
                successor_id: successorTaskId,
                type: dependencyType,
            },
            {
                onSuccess: () => {
                    toast.success("Dependency added");
                    setPredecessorId("");
                    setDependencyType("FS");
                    onClose();
                },
                onError: () => {
                    toast.error("Failed to add dependency");
                },
            }
        );
    };

    return (
        <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
            <DialogContent className="sm:max-w-[425px]">
                <DialogHeader>
                    <DialogTitle>Add Dependency</DialogTitle>
                </DialogHeader>

                <div className="grid gap-4 py-4">
                    <div className="space-y-2">
                        <label htmlFor="predecessor" className="text-sm font-medium">
                            Predecessor Task
                        </label>
                        <Select
                            value={predecessorId}
                            onValueChange={setPredecessorId}
                            disabled={isLoadingTasks}
                        >
                            <SelectTrigger id="predecessor">
                                <SelectValue placeholder="Select a task..." />
                            </SelectTrigger>
                            <SelectContent>
                                {isLoadingTasks ? (
                                    <div className="flex justify-center p-2"><Loader2 className="size-4 animate-spin" /></div>
                                ) : availablePredecessors.length === 0 ? (
                                    <div className="p-2 text-sm text-muted-foreground text-center">No other tasks available</div>
                                ) : (
                                    availablePredecessors.map((task) => (
                                        <SelectItem key={task.id} value={task.id}>
                                            <span className="font-mono text-muted-foreground mr-2">{task.wbs_code}</span>
                                            {task.name}
                                        </SelectItem>
                                    ))
                                )}
                            </SelectContent>
                        </Select>
                    </div>

                    <div className="space-y-2">
                        <label htmlFor="type" className="text-sm font-medium">
                            Relationship Type
                        </label>
                        <Select
                            value={dependencyType}
                            onValueChange={(v) => setDependencyType(v as "FS" | "FF" | "SS" | "SF")}
                        >
                            <SelectTrigger id="type">
                                <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                                <SelectItem value="FS">Finish-to-Start (FS)</SelectItem>
                                <SelectItem value="SS">Start-to-Start (SS)</SelectItem>
                                <SelectItem value="FF">Finish-to-Finish (FF)</SelectItem>
                                <SelectItem value="SF">Start-to-Finish (SF)</SelectItem>
                            </SelectContent>
                        </Select>
                    </div>
                </div>

                <DialogFooter>
                    <Button variant="outline" onClick={onClose}>
                        Cancel
                    </Button>
                    <Button
                        onClick={handleSubmit}
                        disabled={!predecessorId || createDependency.isPending}
                    >
                        {createDependency.isPending && <Loader2 className="mr-2 size-4 animate-spin" />}
                        Add
                    </Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    );
}
