import { Switch } from "@/shared/ui/switch";
import type { ResourceUpdate } from "@/features/resources/types";
import type { UseMutationResult } from "@tanstack/react-query";
import { toast } from "sonner";

interface ResourceStatusSectionProps {
    localData: Partial<ResourceUpdate>;
    setLocalData: (data: Partial<ResourceUpdate>) => void;
    updateResource: UseMutationResult<any, any, { resourceId: string; data: ResourceUpdate }, any>;
    resourceId: string;
}

export function ResourceStatusSection({ localData, setLocalData, updateResource, resourceId }: ResourceStatusSectionProps) {
    return (
        <div className="space-y-4">
            <h3 className="text-lg font-semibold tracking-tight">Status</h3>

            <div className="flex items-center justify-between rounded-md border border-border/50 px-4 py-3">
                <div className="space-y-0.5">
                    <label className="text-sm font-medium">Active</label>
                    <p className="text-xs text-muted-foreground">Inactive resources cannot be assigned to new tasks</p>
                </div>
                <Switch
                    checked={localData.is_active ?? true}
                    onCheckedChange={async (checked) => {
                        setLocalData({ ...localData, is_active: checked });
                        try {
                            await updateResource.mutateAsync({ resourceId, data: { is_active: checked } });
                        } catch (error) {
                            toast.error("Failed to update active status");
                        }
                    }}
                />
            </div>

            {/* Generic toggle — only for WORK */}
            {localData.type === "WORK" && (
                <div className="flex items-center justify-between rounded-md border border-border/50 px-4 py-3">
                    <div className="space-y-0.5">
                        <label className="text-sm font-medium">Generic</label>
                        <p className="text-xs text-muted-foreground">Generic resources represent a role rather than a specific person</p>
                    </div>
                    <Switch
                        checked={localData.is_generic ?? false}
                        onCheckedChange={async (checked) => {
                            setLocalData({ ...localData, is_generic: checked });
                            try {
                                await updateResource.mutateAsync({ resourceId, data: { is_generic: checked } });
                            } catch (error) {
                                toast.error("Failed to update generic status");
                            }
                        }}
                    />
                </div>
            )}
        </div>
    );
}
