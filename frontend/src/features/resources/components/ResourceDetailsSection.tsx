import { Input } from "@/shared/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/shared/ui/select";
import type { ResourceUpdate, ResourceType, Resource } from "@/features/resources/types";
import type { UseMutationResult } from "@tanstack/react-query";
import { toast } from "sonner";

interface ResourceDetailsSectionProps {
    localData: Partial<ResourceUpdate>;
    setLocalData: (data: Partial<ResourceUpdate>) => void;
    handleBlur: (field: keyof ResourceUpdate) => void;
    updateResource: UseMutationResult<Resource, Error, { resourceId: string; data: ResourceUpdate }>;
    resourceId: string;
    calendarOptions: Array<{ id: string; name: string }>;
}

export function ResourceDetailsSection({
    localData,
    setLocalData,
    handleBlur,
    updateResource,
    resourceId,
    calendarOptions,
}: ResourceDetailsSectionProps) {
    return (
        <div className="space-y-4">
            <h3 className="text-sm font-semibold uppercase tracking-wide text-muted-foreground">Details</h3>

            <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1.5">
                    <label className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">Type</label>
                    <Select
                        value={localData.type ?? "WORK"}
                        onValueChange={async (v) => {
                            // NOTE: Auto-save pattern: discrete selects commit immediately to avoid user confusion
                            setLocalData({ ...localData, type: v as ResourceType });
                            try {
                                await updateResource.mutateAsync({ resourceId, data: { type: v as ResourceType } });
                            } catch (error) {
                                toast.error("Failed to update type");
                            }
                        }}
                    >
                        <SelectTrigger><SelectValue /></SelectTrigger>
                        <SelectContent>
                            <SelectItem value="WORK">Work</SelectItem>
                            <SelectItem value="MATERIAL">Material</SelectItem>
                            <SelectItem value="COST">Cost</SelectItem>
                        </SelectContent>
                    </Select>
                </div>

                <div className="space-y-1.5">
                    <label className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">Calendar</label>
                    <Select
                        value={localData.calendar_id ?? "none"}
                        onValueChange={async (value) => {
                            const nextCalendarId = value === "none" ? null : value;
                            setLocalData({ ...localData, calendar_id: nextCalendarId });
                            try {
                                await updateResource.mutateAsync({
                                    resourceId,
                                    data: { calendar_id: nextCalendarId },
                                });
                            } catch (error) {
                                toast.error("Failed to update calendar");
                            }
                        }}
                    >
                        <SelectTrigger><SelectValue placeholder="Project default" /></SelectTrigger>
                        <SelectContent>
                            <SelectItem value="none">Project default</SelectItem>
                            {calendarOptions.map((calendar) => (
                                <SelectItem key={calendar.id} value={calendar.id}>
                                    {calendar.name}
                                </SelectItem>
                            ))}
                        </SelectContent>
                    </Select>
                </div>

                <div className="space-y-1.5">
                    <label className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">Initials</label>
                    <Input
                        value={localData.initials ?? ""}
                        onChange={(e) => setLocalData({ ...localData, initials: e.target.value })}
                        // NOTE: Auto-save pattern: text inputs commit on blur to prevent spamming the backend
                        onBlur={() => handleBlur("initials")}
                        maxLength={10}
                        placeholder={
                            localData.type === "WORK" ? "e.g. JS" :
                                localData.type === "MATERIAL" ? "e.g. CON" :
                                    "e.g. TRV"
                        }
                    />
                </div>
            </div>

            {/* Email - only for WORK */}
            {localData.type === "WORK" && (
                <div className="grid grid-cols-2 gap-3">
                    <div className="space-y-1.5">
                        <label className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">Email</label>
                        <Input
                            value={localData.email ?? ""}
                            onChange={(e) => setLocalData({ ...localData, email: e.target.value })}
                            onBlur={() => handleBlur("email")}
                            type="email"
                            placeholder="john@example.com"
                        />
                    </div>

                    <div className="space-y-1.5">
                        <label className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">Group</label>
                        <Input
                            value={localData.group_name ?? ""}
                            onChange={(e) => setLocalData({ ...localData, group_name: e.target.value })}
                            onBlur={() => handleBlur("group_name")}
                            placeholder="e.g. Engineering"
                        />
                    </div>
                </div>
            )}

            {/* Group - for MATERIAL and COST (no email row) */}
            {localData.type !== "WORK" && (
                <div className="space-y-1.5">
                    <label className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">Group</label>
                    <Input
                        value={localData.group_name ?? ""}
                        onChange={(e) => setLocalData({ ...localData, group_name: e.target.value })}
                        onBlur={() => handleBlur("group_name")}
                        placeholder="e.g. Raw Materials"
                    />
                </div>
            )}

            <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1.5">
                    <label className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">Code</label>
                    <Input
                        value={localData.code ?? ""}
                        onChange={(e) => setLocalData({ ...localData, code: e.target.value })}
                        onBlur={() => handleBlur("code")}
                        maxLength={50}
                        placeholder={
                            localData.type === "WORK" ? "e.g. ENG-001" :
                                localData.type === "MATERIAL" ? "e.g. MAT-001" :
                                    "e.g. CST-001"
                        }
                    />
                </div>

                {/* Max Units - only for WORK */}
                {localData.type === "WORK" && (
                    <div className="space-y-1.5">
                        <label className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">Max Units</label>
                        <Input
                            type="number"
                            value={localData.max_units ?? ""}
                            onChange={(e) => setLocalData({ ...localData, max_units: Number(e.target.value) })}
                            onBlur={() => handleBlur("max_units")}
                            min={0}
                            step={0.1}
                        />
                    </div>
                )}
            </div>

            {/* Material Label - only for MATERIAL */}
            {localData.type === "MATERIAL" && (
                <div className="space-y-1.5">
                    <label className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">Material Label</label>
                    <Input
                        value={localData.material_label ?? ""}
                        onChange={(e) => setLocalData({ ...localData, material_label: e.target.value })}
                        onBlur={() => handleBlur("material_label")}
                        placeholder="e.g. cubic meters"
                    />
                </div>
            )}
        </div>
    );
}
