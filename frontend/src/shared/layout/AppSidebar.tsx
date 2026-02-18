import * as React from "react";
import { Link, useLocation } from "react-router";
import {
  BarChart3,
  Calendar,
  GanttChart,
  LayoutDashboard,
  ListTodo,
  Settings,
  Users,
  FolderKanban,
  ArrowLeft,
} from "lucide-react";

import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarRail,
} from "@/shared/ui/sidebar";
import { NavUser } from "@/shared/layout/NavUser";
import { OrgSwitcher } from "@/features/organizations/components/OrgSwitcher";
import { useMyOrgRole } from "@/features/organizations/hooks/useMyOrgRole";

export function AppSidebar({ ...props }: React.ComponentProps<typeof Sidebar>) {
  const location = useLocation();

  // Check if we are in a project context
  // Regex matches /projects/{uuid}/... but not just /projects
  const projectMatch = location.pathname.match(/^\/projects\/([^/]+)/);
  const projectId = projectMatch ? projectMatch[1] : null;
  const isProjectContext = !!projectId;

  const { role: currentRole } = useMyOrgRole();
  const isAdminOrOwner = currentRole === "admin" || currentRole === "owner";

  const globalNavItems = [
    { title: "Dashboard", url: "/", icon: LayoutDashboard },
    { title: "Projects", url: "/projects", icon: FolderKanban },
    ...(isAdminOrOwner
      ? [
          { title: "Members", url: "/members", icon: Users },
          { title: "Settings", url: "/settings", icon: Settings },
        ]
      : []),
  ];

  const projectNavItems = [
    { title: "Back to Projects", url: "/projects", icon: ArrowLeft },
    { title: "Overview", url: `/projects/${projectId}`, icon: LayoutDashboard },
    { title: "Tasks", url: `/projects/${projectId}/tasks`, icon: ListTodo },
    { title: "Gantt", url: `/projects/${projectId}/gantt`, icon: GanttChart },
    {
      title: "Resources",
      url: `/projects/${projectId}/resources`,
      icon: Users,
    },
    {
      title: "Calendar",
      url: `/projects/${projectId}/calendar`,
      icon: Calendar,
    },
    {
      title: "Reports",
      url: `/projects/${projectId}/reports`,
      icon: BarChart3,
    },
  ];

  const navItems = isProjectContext ? projectNavItems : globalNavItems;
  const groupLabel = isProjectContext ? "Project" : "Organization";

  return (
    <Sidebar collapsible="icon" {...props}>
      <SidebarHeader>
        <OrgSwitcher />
      </SidebarHeader>

      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupLabel>{groupLabel}</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {navItems.map((item) => {
                const isActive =
                  item.url === "/"
                    ? location.pathname === "/"
                    : location.pathname === item.url ||
                      (item.url !== "/projects" &&
                        location.pathname.startsWith(item.url + "/"));

                return (
                  <SidebarMenuItem key={item.title}>
                    <SidebarMenuButton
                      asChild
                      isActive={isActive}
                      tooltip={item.title}
                    >
                      <Link to={item.url}>
                        <item.icon />
                        <span>{item.title}</span>
                      </Link>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                );
              })}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>

      <SidebarFooter>
        <NavUser />
      </SidebarFooter>

      <SidebarRail />
    </Sidebar>
  );
}
