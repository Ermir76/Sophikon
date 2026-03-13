import { useState, useEffect } from "react";
import { format, parseISO } from "date-fns";
import { Loader2, Trash2 } from "lucide-react";
import {
    Sheet,
    SheetContent,
    SheetHeader,
    SheetTitle,
    SheetDescription,
} from "@/shared/ui/sheet";
import { Input } from "@/shared/ui/input";
import { Button } from "@/shared/ui/button";
import { Badge } from "@/shared/ui/badge";
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
import { useResource, useUpdateResource } from "@/features/resources/hooks/useResources";
import { toast } from "sonner";
import { ResourceDetailsSection } from "./ResourceDetailsSection";
import { ResourceRatesSection } from "./ResourceRatesSection";
import { ResourceStatusSection } from "./ResourceStatusSection";
import { useCalendars } from "@/features/calendar";
import type { ResourceUpdate } from "@/features/resources/types";

interface ResourceDetailPanelProps {
    projectId: string;
    resourceId: string | null;
    isOpen: boolean;
    onClose: () => void;
    onDelete?: (resourceId: string) => void;
    isDeletePending?: boolean;
}

const NULLABLE_FIELDS: (keyof ResourceUpdate)[] = ["initials", "email", "group_name", "code", "material_label"];

export function ResourceDetailPanel({ projectId, resourceId, isOpen, onClose, onDelete, isDeletePending }: ResourceDetailPanelProps) {
    const { data: resource, isLoading } = useResource(projectId, resourceId ?? undefined);
    const updateResource = useUpdateResource(projectId);
    const calendarsQuery = useCalendars(projectId);
    const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
    const [localData, setLocalData] = useState<Partial<ResourceUpdate>>({});

    // Sync from server when resource loads
    useEffect(() => {
        if (resource) {
            setLocalData({
                name: resource.name,
                type: resource.type,
                initials: resource.initials || "",
                email: resource.email || "",
                max_units: resource.max_units,
                calendar_id: resource.calendar_id ?? null,
                group_name: resource.group_name || "",
                code: resource.code || "",
                material_label: resource.material_label || "",
                is_generic: resource.is_generic,
                is_active: resource.is_active,
                standard_rate: resource.standard_rate,
                overtime_rate: resource.overtime_rate,
                cost_per_use: resource.cost_per_use,
                accrue_at: resource.accrue_at,
            });
        }
    }, [resource]);

    const handleBlur = async (field: keyof ResourceUpdate) => {
        if (!resource || !resourceId) return;

        const currentValue = localData[field];
        let originalValue = resource[field as keyof typeof resource] as ResourceUpdate[typeof field];

        if (NULLABLE_FIELDS.includes(field) && !originalValue) originalValue = "";

        if (currentValue !== originalValue) {
            const valueToSend = (NULLABLE_FIELDS.includes(field) && currentValue === "") ? null : currentValue;

            try {
                await updateResource.mutateAsync({ resourceId, data: { [field]: valueToSend } });
            } catch (error) {
                toast.error(`Failed to update ${field}`);
                setLocalData((prev) => ({ ...prev, [field]: originalValue }));
            }
        }
    };

    const sectionProps = {
        localData,
        setLocalData,
        handleBlur,
        updateResource,
        resourceId: resourceId ?? "",
        calendarOptions: (calendarsQuery.data ?? []).map((calendar) => ({
            id: calendar.id,
            name: calendar.name,
        })),
    };

    return (<>
        <Sheet open={isOpen} onOpenChange={(open) => !open && onClose()}>
            <SheetContent className="w-full overflow-y-auto p-0 sm:max-w-md md:max-w-xl">
                {isLoading || !resource ? (
                    <div className="flex justify-center items-center h-full">
                        <Loader2 className="size-8 animate-spin text-muted-foreground" />
                    </div>
                ) : (
                    <div className="flex h-full flex-col bg-background">
                        {/* Header */}
                        <div className="sticky top-0 z-10 border-b bg-background/95 px-4 py-4 backdrop-blur supports-[backdrop-filter]:bg-background/85 sm:px-5">
                            <SheetHeader className="space-y-3">
                                <SheetTitle className="flex items-start justify-between gap-4 pr-8">
                                    <div className="flex flex-1 flex-col gap-2.5">
                                        <div className="flex items-center gap-2">
                                            {resource.initials && (
                                                <span className="inline-flex size-8 items-center justify-center rounded-full border text-xs font-bold">
                                                    {resource.initials}
                                                </span>
                                            )}
                                            <Badge variant="outline" className="text-[10px] font-bold tracking-wide">
                                                {resource.type}
                                            </Badge>
                                            {!resource.is_active && (
                                                <Badge variant="outline" className="text-[10px] opacity-60">Inactive</Badge>
                                            )}
                                            <Button
                                                variant="ghost"
                                                size="icon"
                                                className="size-8"
                                                disabled={isDeletePending}
                                                onClick={() => setShowDeleteConfirm(true)}
                                            >
                                                <Trash2 className="size-4" />
                                            </Button>
                                        </div>
                                        <Input
                                            value={localData.name ?? ""}
                                            onChange={(e) => setLocalData({ ...localData, name: e.target.value })}
                                            onBlur={() => handleBlur("name")}
                                            className="h-auto w-full border-0 px-2.5 py-1 text-xl font-bold shadow-none focus-visible:ring-0"
                                            placeholder="Resource Name"
                                        />
                                    </div>
                                </SheetTitle>
                                <SheetDescription className="text-[11px] font-medium uppercase tracking-wide text-muted-foreground/90">
                                    Created on {format(parseISO(resource.created_at), "MMMM do, yyyy")}
                                </SheetDescription>
                            </SheetHeader>
                        </div>

                        {/* Body */}
                        <div className="flex-1 space-y-6 overflow-y-auto p-4 sm:p-5">
                            <ResourceDetailsSection {...sectionProps} />
                            <div className="h-px w-full rounded-full bg-border/80" />
                            <ResourceRatesSection {...sectionProps} />
                            <div className="h-px w-full rounded-full bg-border/80" />
                            <ResourceStatusSection {...sectionProps} />
                        </div>
                    </div>
                )}
            </SheetContent>
        </Sheet>

        {resource && (
            <AlertDialog open={showDeleteConfirm} onOpenChange={setShowDeleteConfirm}>
                <AlertDialogContent variant="destructive">
                    <AlertDialogHeader>
                        <AlertDialogTitle>Delete resource?</AlertDialogTitle>
                        <AlertDialogDescription>
                            This will permanently delete "{resource.name}". Any assignments using this resource will also be removed.
                        </AlertDialogDescription>
                    </AlertDialogHeader>
                    <AlertDialogFooter>
                        <AlertDialogCancel>Cancel</AlertDialogCancel>
                        <AlertDialogAction
                            variant="destructive"
                            onClick={() => {
                                onDelete?.(resource.id);
                                setShowDeleteConfirm(false);
                            }}
                        >
                            Delete
                        </AlertDialogAction>
                    </AlertDialogFooter>
                </AlertDialogContent>
            </AlertDialog>
        )}
    </>);
}
