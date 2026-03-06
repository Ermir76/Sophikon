import { Switch } from "@/shared/ui/switch";
import type { ResourceUpdate, Resource } from "@/features/resources/types";
import type { UseMutationResult } from "@tanstack/react-query";
import { toast } from "sonner";

interface ResourceStatusSectionProps {
    localData: Partial<ResourceUpdate>;
    setLocalData: (data: Partial<ResourceUpdate>) => void;
    updateResource: UseMutationResult<Resource, Error, { resourceId: string; data: ResourceUpdate }>;
    resourceId: string;
}

export function ResourceStatusSection({ localData, setLocalData, updateResource, resourceId }: ResourceStatusSectionProps) {
    return (
        <div className="space-y-3">
            <h3 className="text-sm font-semibold uppercase tracking-wide text-muted-foreground">Status</h3>

            <div className="flex items-center justify-between rounded-md border px-3 py-2.5">
                <div className="space-y-0.5">
                    <label className="text-sm font-medium">Active</label>
                    <p className="text-xs text-muted-foreground">Inactive resources cannot be assigned to new tasks</p>
                </div>
                <Switch
                    checked={localData.is_active ?? true}
                    onCheckedChange={async (checked) => {
                        // NOTE: Auto-save pattern: switches commit immediately
                        setLocalData({ ...localData, is_active: checked });
                        try {
                            await updateResource.mutateAsync({ resourceId, data: { is_active: checked } });
                        } catch (error) {
                            toast.error("Failed to update active status");
                        }
                    }}
                />
            </div>

            {/* Generic toggle - only for WORK */}
            {localData.type === "WORK" && (
                <div className="flex items-center justify-between rounded-md border px-3 py-2.5">
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
