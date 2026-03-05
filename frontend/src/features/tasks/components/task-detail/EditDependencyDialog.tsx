import { useState, useEffect } from "react";
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
import { Switch } from "@/shared/ui/switch";
import { useUpdateDependency } from "@/features/tasks/hooks/useDependencies";
import { toast } from "sonner";
import type { Dependency, DependencyUpdate } from "@/features/tasks/types";

interface EditDependencyDialogProps {
    projectId: string;
    dependency: Dependency;
    isOpen: boolean;
    onClose: () => void;
}

export function EditDependencyDialog({
    projectId,
    dependency,
    isOpen,
    onClose,
}: EditDependencyDialogProps) {
    const [type, setType] = useState<"FS" | "FF" | "SS" | "SF">(dependency.type);
    const [lag, setLag] = useState<number>(dependency.lag);
    const [isDisabled, setIsDisabled] = useState<boolean>(dependency.is_disabled);

    const updateDependency = useUpdateDependency(projectId);

    // Sync local state when dependency prop changes
    useEffect(() => {
        setType(dependency.type);
        setLag(dependency.lag);
        setIsDisabled(dependency.is_disabled);
    }, [dependency]);

    const handleSubmit = async () => {
        const data: Partial<DependencyUpdate> = {};

        if (type !== dependency.type) data.type = type;
        if (lag !== dependency.lag) data.lag = lag;
        if (isDisabled !== dependency.is_disabled) data.is_disabled = isDisabled;

        // Nothing changed
        if (Object.keys(data).length === 0) {
            onClose();
            return;
        }

        try {
            await updateDependency.mutateAsync({ dependencyId: dependency.id, data });
            toast.success("Dependency updated");
            onClose();
        } catch (error) {
            toast.error("Failed to update dependency");
        }
    };

    return (
        <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
            <DialogContent className="sm:max-w-[400px]">
                <DialogHeader>
                    <DialogTitle>Edit Dependency</DialogTitle>
                </DialogHeader>

                <div className="grid gap-4 py-4">
                    <div className="space-y-2">
                        <label htmlFor="dep-type" className="text-sm font-medium">
                            Relationship Type
                        </label>
                        <Select
                            value={type}
                            onValueChange={(v) => setType(v as "FS" | "FF" | "SS" | "SF")}
                        >
                            <SelectTrigger id="dep-type">
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

                    <div className="space-y-2">
                        <label htmlFor="dep-lag" className="text-sm font-medium">
                            Lag (minutes)
                        </label>
                        <Input
                            id="dep-lag"
                            type="number"
                            value={lag}
                            onChange={(e) => setLag(Number(e.target.value))}
                        />
                        <p className="text-xs text-muted-foreground">
                            Positive = delay, negative = lead time
                        </p>
                    </div>

                    <div className="flex items-center justify-between rounded-md border px-4 py-3">
                        <div className="space-y-0.5">
                            <label htmlFor="dep-disabled" className="text-sm font-medium">
                                Disabled
                            </label>
                            <p className="text-xs text-muted-foreground">
                                Disabled dependencies are ignored by the scheduler
                            </p>
                        </div>
                        <Switch
                            id="dep-disabled"
                            checked={isDisabled}
                            onCheckedChange={setIsDisabled}
                        />
                    </div>
                </div>

                <DialogFooter>
                    <Button variant="outline" onClick={onClose}>
                        Cancel
                    </Button>
                    <Button
                        onClick={handleSubmit}
                        disabled={updateDependency.isPending}
                    >
                        {updateDependency.isPending && <Loader2 className="mr-2 size-4 animate-spin" />}
                        Save
                    </Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    );
}
