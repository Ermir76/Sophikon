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
import { OrgSwitcher, useMyOrgRole } from "@/features/organizations";

export function AppSidebar({ ...props }: React.ComponentProps<typeof Sidebar>) {
  const location = useLocation();

  // Check if we are in a project context
  // Regex matches /projects/{uuid}/... but not just /projects
  const projectMatch = location.pathname.match(/^\/projects\/([^/]+)/);
  const projectId = projectMatch ? projectMatch[1] : null;
  const isProjectContext = !!projectId;

  const { role: currentRole } = useMyOrgRole();
  const isAdminOrOwner = currentRole === "admin" || currentRole === "owner";

  type NavItem = {
    title: string;
    url: string;
    icon: React.ComponentType<{ className?: string }>;
    routeKey: string;
    routeColor: string;
  };

  const globalNavItems: NavItem[] = [
    {
      title: "Dashboard",
      url: "/",
      icon: LayoutDashboard,
      routeKey: "dashboard",
      routeColor: "var(--route-dashboard)",
    },
    {
      title: "Projects",
      url: "/projects",
      icon: FolderKanban,
      routeKey: "projects",
      routeColor: "var(--route-projects)",
    },
    ...(isAdminOrOwner
      ? [
          {
            title: "Members",
            url: "/members",
            icon: Users,
            routeKey: "members",
            routeColor: "var(--route-members)",
          },
          {
            title: "Settings",
            url: "/settings",
            icon: Settings,
            routeKey: "settings",
            routeColor: "var(--route-settings)",
          },
        ]
      : []),
  ];

  const projectNavItems: NavItem[] = [
    {
      title: "Back to Projects",
      url: "/projects",
      icon: ArrowLeft,
      routeKey: "projects",
      routeColor: "var(--route-projects)",
    },
    {
      title: "Overview",
      url: `/projects/${projectId}`,
      icon: LayoutDashboard,
      routeKey: "overview",
      routeColor: "var(--route-overview)",
    },
    {
      title: "Tasks",
      url: `/projects/${projectId}/tasks`,
      icon: ListTodo,
      routeKey: "tasks",
      routeColor: "var(--route-tasks)",
    },
    {
      title: "Gantt",
      url: `/projects/${projectId}/gantt`,
      icon: GanttChart,
      routeKey: "gantt",
      routeColor: "var(--route-gantt)",
    },
    {
      title: "Resources",
      url: `/projects/${projectId}/resources`,
      icon: Users,
      routeKey: "resources",
      routeColor: "var(--route-resources)",
    },
    {
      title: "Utilization",
      url: `/projects/${projectId}/utilization`,
      icon: BarChart3,
      routeKey: "utilization",
      routeColor: "var(--route-resources)",
    },
    {
      title: "Calendar",
      url: `/projects/${projectId}/calendar`,
      icon: Calendar,
      routeKey: "calendar",
      routeColor: "var(--route-calendar)",
    },
    {
      title: "Reports",
      url: `/projects/${projectId}/reports`,
      icon: BarChart3,
      routeKey: "reports",
      routeColor: "var(--route-reports)",
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
                      data-route={item.routeKey}
                      style={{ "--route-color": item.routeColor } as React.CSSProperties}
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
