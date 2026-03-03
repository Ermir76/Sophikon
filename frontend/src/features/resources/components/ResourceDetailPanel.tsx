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
        let originalValue: any = resource[field as keyof typeof resource];

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
    };

    return (<>
        <Sheet open={isOpen} onOpenChange={(open) => !open && onClose()}>
            <SheetContent className="w-full sm:max-w-md md:max-w-2xl overflow-y-auto p-0 border-l border-border/50 shadow-2xl">
                {isLoading || !resource ? (
                    <div className="flex justify-center items-center h-full">
                        <Loader2 className="size-8 animate-spin text-muted-foreground" />
                    </div>
                ) : (
                    <div className="flex flex-col h-full bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
                        {/* Header */}
                        <div className="px-6 py-6 border-b border-border/50 bg-muted/20">
                            <SheetHeader className="space-y-4">
                                <SheetTitle className="flex justify-between items-start gap-4 pr-8">
                                    <div className="flex flex-col gap-3 flex-1">
                                        <div className="flex items-center gap-2">
                                            {resource.initials && (
                                                <span className="inline-flex items-center justify-center size-8 rounded-full bg-primary/10 text-xs font-bold text-primary">
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
                                                className="size-8 text-muted-foreground hover:text-destructive hover:bg-destructive/10"
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
                                            className="text-2xl font-bold h-auto px-3 py-1.5 bg-transparent border-none hover:bg-muted/30 focus-visible:ring-0 focus-visible:outline-none focus-visible:shadow-none shadow-none rounded-md transition-colors w-full"
                                            placeholder="Resource Name"
                                        />
                                    </div>
                                </SheetTitle>
                                <SheetDescription className="text-xs font-medium uppercase tracking-wider text-muted-foreground/70">
                                    Created on {format(parseISO(resource.created_at), "MMMM do, yyyy")}
                                </SheetDescription>
                            </SheetHeader>
                        </div>

                        {/* Body */}
                        <div className="flex-1 overflow-y-auto p-6 space-y-10">
                            <ResourceDetailsSection {...sectionProps} />
                            <div className="h-px w-full bg-border/50 rounded-full" />
                            <ResourceRatesSection {...sectionProps} />
                            <div className="h-px w-full bg-border/50 rounded-full" />
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
