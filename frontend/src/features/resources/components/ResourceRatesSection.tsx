import { Input } from "@/shared/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/shared/ui/select";
import type { ResourceUpdate, CostAccrual, Resource } from "@/features/resources/types";
import type { UseMutationResult } from "@tanstack/react-query";
import { toast } from "sonner";

interface ResourceRatesSectionProps {
    localData: Partial<ResourceUpdate>;
    setLocalData: (data: Partial<ResourceUpdate>) => void;
    handleBlur: (field: keyof ResourceUpdate) => void;
    updateResource: UseMutationResult<Resource, Error, { resourceId: string; data: ResourceUpdate }>;
    resourceId: string;
}

export function ResourceRatesSection({ localData, setLocalData, handleBlur, updateResource, resourceId }: ResourceRatesSectionProps) {
    return (
        <div className="space-y-6">
            <h3 className="text-lg font-semibold tracking-tight">
                {localData.type === "COST" ? "Cost" : "Rates"}
            </h3>

            {localData.type !== "COST" && (
                <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                        <label className="text-sm font-medium text-muted-foreground">
                            Standard Rate ({localData.type === "MATERIAL" ? "$/unit" : "$/h"})
                        </label>
                        <Input
                            type="number"
                            value={localData.standard_rate ?? ""}
                            onChange={(e) => setLocalData({ ...localData, standard_rate: Number(e.target.value) })}
                            onBlur={() => handleBlur("standard_rate")}
                            min={0}
                            step={0.01}
                        />
                    </div>

                    {/* Overtime Rate - only for WORK */}
                    {localData.type === "WORK" && (
                        <div className="space-y-2">
                            <label className="text-sm font-medium text-muted-foreground">Overtime Rate ($/h)</label>
                            <Input
                                type="number"
                                value={localData.overtime_rate ?? ""}
                                onChange={(e) => setLocalData({ ...localData, overtime_rate: Number(e.target.value) })}
                                onBlur={() => handleBlur("overtime_rate")}
                                min={0}
                                step={0.01}
                            />
                        </div>
                    )}
                </div>
            )}

            <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                    <label className="text-sm font-medium text-muted-foreground">
                        {localData.type === "COST" ? "Cost Amount ($)" : "Cost per Use ($)"}
                    </label>
                    <Input
                        type="number"
                        value={localData.cost_per_use ?? ""}
                        onChange={(e) => setLocalData({ ...localData, cost_per_use: Number(e.target.value) })}
                        onBlur={() => handleBlur("cost_per_use")}
                        min={0}
                        step={0.01}
                    />
                </div>

                <div className="space-y-2">
                    <label className="text-sm font-medium text-muted-foreground">Accrue At</label>
                    <Select
                        value={localData.accrue_at ?? "PRORATED"}
                        onValueChange={async (v) => {
                            // NOTE: Auto-save pattern: discrete selects commit immediately
                            setLocalData({ ...localData, accrue_at: v as CostAccrual });
                            try {
                                await updateResource.mutateAsync({ resourceId, data: { accrue_at: v as CostAccrual } });
                            } catch (error) {
                                toast.error("Failed to update accrue at");
                            }
                        }}
                    >
                        <SelectTrigger><SelectValue /></SelectTrigger>
                        <SelectContent>
                            <SelectItem value="START">Start</SelectItem>
                            <SelectItem value="END">End</SelectItem>
                            <SelectItem value="PRORATED">Prorated</SelectItem>
                        </SelectContent>
                    </Select>
                </div>
            </div>
        </div>
    );
}
