import * as React from "react";
import { useState, useEffect } from "react";
import { ChevronsUpDown, Plus, Check, Loader2 } from "lucide-react";

import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/shared/ui/dropdown-menu";
import {
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  useSidebar,
} from "@/shared/ui/sidebar";
import { useOrgStore } from "@/features/organizations/store/org-store";
import { useOrganizations, useOrganization } from "@/features/organizations/hooks/useOrganizations";
import { CreateOrgDialog } from "./CreateOrgDialog";

export function OrgSwitcher() {
  const { isMobile } = useSidebar();
  const [createOpen, setCreateOpen] = useState(false);
  const activeOrgId = useOrgStore((state) => state.activeOrgId);
  const setActiveOrg = useOrgStore((state) => state.setActiveOrg);

  const { data: organizationsData, isLoading } = useOrganizations();
  const { data: activeOrgData } = useOrganization(activeOrgId || "");

  const organizations = React.useMemo(
    () => organizationsData?.items || [],
    [organizationsData?.items],
  );

  // Auto-select first organization if none is selected
  useEffect(() => {
    if (!activeOrgId && organizations.length > 0) {
      setActiveOrg(organizations[0].id);
    }
  }, [activeOrgId, organizations, setActiveOrg]);

  // Default to a placeholder if no org is selected
  const activeOrg = activeOrgData || {
    name: "Select Organization",
    slug: "none",
    id: "",
  };

  return (
    <SidebarMenu>
      <SidebarMenuItem>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <SidebarMenuButton
              size="lg"
              className="data-[state=open]:bg-sidebar-accent data-[state=open]:text-sidebar-accent-foreground"
            >
              <div className="flex aspect-square size-8 items-center justify-center rounded-lg bg-sidebar-primary text-sidebar-primary-foreground">
                <span className="text-xs font-bold">
                  {activeOrg.name.substring(0, 2).toUpperCase()}
                </span>
              </div>
              <div className="grid flex-1 text-left text-sm leading-tight">
                <span className="truncate font-semibold">{activeOrg.name}</span>
                <span className="truncate text-xs">{activeOrg.slug}</span>
              </div>
              <ChevronsUpDown className="ml-auto" />
            </SidebarMenuButton>
          </DropdownMenuTrigger>
          <DropdownMenuContent
            className="w-[--radix-dropdown-menu-trigger-width] min-w-56 rounded-lg"
            align="start"
            side={isMobile ? "bottom" : "right"}
            sideOffset={4}
          >
            <DropdownMenuLabel className="text-xs text-muted-foreground">
              Organizations
            </DropdownMenuLabel>

            {isLoading && organizations.length === 0 ? (
              <div className="flex justify-center p-2">
                <Loader2 className="size-4 animate-spin text-muted-foreground" />
              </div>
            ) : (
              organizations.map((org) => (
                <DropdownMenuItem
                  key={org.id}
                  onClick={() => setActiveOrg(org.id)}
                  className="gap-2 p-2 cursor-pointer"
                >
                  <div className="flex size-6 items-center justify-center rounded-sm border">
                    <span className="text-xs font-bold">
                      {org.name.substring(0, 2).toUpperCase()}
                    </span>
                  </div>
                  <div className="flex-1 truncate">{org.name}</div>
                  {activeOrg.id === org.id && (
                    <Check className="ml-auto size-4" />
                  )}
                </DropdownMenuItem>
              ))
            )}

            <DropdownMenuSeparator />
            <DropdownMenuItem
              className="gap-2 p-2 cursor-pointer"
              onClick={() => setCreateOpen(true)}
            >
              <div className="flex size-6 items-center justify-center rounded-md border bg-background">
                <Plus className="size-4" />
              </div>
              <div className="font-medium text-muted-foreground">
                Add Organization
              </div>
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
        <CreateOrgDialog open={createOpen} onOpenChange={setCreateOpen} />
      </SidebarMenuItem>
    </SidebarMenu>
  );
}
