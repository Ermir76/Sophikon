import { createColumnHelper } from "@tanstack/react-table";
import { Checkbox } from "@/shared/ui/checkbox";
import { Badge } from "@/shared/ui/badge";
import type { Resource } from "@/features/resources/types";
import { OverAllocationBadge } from "@/features/resources/components/OverAllocationBadge";
import { MoreHorizontal, Trash2, PanelRight } from "lucide-react";
import { Button } from "@/shared/ui/button";
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuSeparator,
    DropdownMenuTrigger,
} from "@/shared/ui/dropdown-menu";

// ── Type augmentation for table meta ──

declare module "@tanstack/react-table" {
    interface TableMeta<TData> {
        onViewDetails?: (resourceId: string) => void;
        onDeleteResource?: (resourceId: string) => void;
        isDeleteResourcePending?: boolean;
        overAllocatedResourceIds?: Set<string>;
    }
}

// ── Helper: type badge color ──

function resourceTypeBadge(type: Resource["type"]) {
    switch (type) {
        case "WORK":
            return (
                <Badge
                    variant="outline"
                    className="resource-type-badge text-[10px] font-bold tracking-wide"
                    data-resource-type="WORK"
                >
                    Work
                </Badge>
            );
        case "MATERIAL":
            return (
                <Badge
                    variant="outline"
                    className="resource-type-badge text-[10px] font-bold tracking-wide"
                    data-resource-type="MATERIAL"
                >
                    Material
                </Badge>
            );
        case "COST":
            return (
                <Badge
                    variant="outline"
                    className="resource-type-badge text-[10px] font-bold tracking-wide"
                    data-resource-type="COST"
                >
                    Cost
                </Badge>
            );
    }
}

// ── Column Definitions ──

const columnHelper = createColumnHelper<Resource>();

export const resourceColumns = [
    columnHelper.display({
        id: "select",
        header: ({ table }) => (
            <div onClick={(e) => e.stopPropagation()} className="flex items-center justify-center">
                <Checkbox
                    checked={table.getIsAllPageRowsSelected() || (table.getIsSomePageRowsSelected() && "indeterminate")}
                    onCheckedChange={(value) => table.toggleAllPageRowsSelected(!!value)}
                    aria-label="Select all"
                />
            </div>
        ),
        cell: ({ row }) => (
            <div onClick={(e) => e.stopPropagation()} className="flex items-center justify-center">
                <Checkbox
                    checked={row.getIsSelected()}
                    onCheckedChange={(value) => row.toggleSelected(!!value)}
                    aria-label="Select row"
                />
            </div>
        ),
    }),
    columnHelper.accessor("name", {
        header: "Name",
        cell: (info) => {
            const resource = info.row.original;
            const meta = info.table.options.meta;
            const isOverAllocated = meta?.overAllocatedResourceIds?.has(resource.id);
            return (
                <div className="flex items-center gap-2">
                    {resource.initials && (
                        <span className="inline-flex items-center justify-center size-7 rounded-full bg-primary/10 text-[10px] font-bold text-primary shrink-0">
                            {resource.initials}
                        </span>
                    )}
                    <span className="font-medium truncate">{info.getValue()}</span>
                    {isOverAllocated && <OverAllocationBadge />}
                    {!resource.is_active && (
                        <Badge variant="outline" className="text-[10px] opacity-60">Inactive</Badge>
                    )}
                </div>
            );
        },
    }),
    columnHelper.accessor("type", {
        header: "Type",
        cell: (info) => resourceTypeBadge(info.getValue()),
    }),
    columnHelper.accessor("email", {
        header: "Email",
        cell: (info) => info.getValue() || "—",
    }),
    columnHelper.accessor("group_name", {
        header: "Group",
        cell: (info) => info.getValue() || "—",
    }),
    columnHelper.accessor("max_units", {
        header: "Max Units",
        cell: (info) => `${Math.round(Number(info.getValue()) * 100)}%`,
    }),
    columnHelper.accessor("standard_rate", {
        header: "Std Rate",
        cell: (info) => {
            const val = Number(info.getValue());
            return val > 0 ? `$${val.toFixed(2)}/h` : "—";
        },
    }),
    columnHelper.display({
        id: "actions",
        header: "",
        cell: (info) => {
            const resource = info.row.original;
            const meta = info.table.options.meta;
            return (
                <div onClick={(e) => e.stopPropagation()}>
                    <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                            <Button
                                variant="ghost"
                                size="icon"
                                className="size-8 text-muted-foreground hover:text-foreground"
                            >
                                <MoreHorizontal className="size-4" />
                                <span className="sr-only">Open actions menu</span>
                            </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                            <DropdownMenuItem onClick={() => meta?.onViewDetails?.(resource.id)}>
                                <PanelRight className="size-4" />
                                View Details
                            </DropdownMenuItem>
                            <DropdownMenuSeparator />
                            <DropdownMenuItem
                                disabled={meta?.isDeleteResourcePending}
                                className="text-destructive focus:text-destructive focus:bg-destructive/10"
                                onClick={() => meta?.onDeleteResource?.(resource.id)}
                            >
                                <Trash2 className="size-4" />
                                Delete
                            </DropdownMenuItem>
                        </DropdownMenuContent>
                    </DropdownMenu>
                </div>
            );
        },
    }),
];
