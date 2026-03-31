import * as React from "react";
import { Link, useLocation } from "react-router";
import {
  BarChart3,
  Calendar,
  GanttChart,
  LayoutDashboard,
  Kanban,
  ListTodo,
  FolderKanban,
  ArrowLeft,
  Sparkles,
  Users,
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
  SidebarSeparator,
} from "@/shared/ui/sidebar";
import { NavUser } from "@/shared/layout/NavUser";
import { OrgSwitcher } from "@/features/organizations";
import { useAiPanelStore } from "@/features/ai";

export function AppSidebar({ ...props }: React.ComponentProps<typeof Sidebar>) {
  const location = useLocation();

  // Check if we are in a project context
  // Regex matches /projects/{uuid}/... but not just /projects
  const projectMatch = location.pathname.match(/^\/projects\/([^/]+)/);
  const projectId = projectMatch ? projectMatch[1] : null;
  const isProjectContext = !!projectId;
  const isAiPanelOpen = useAiPanelStore((state) =>
    projectId ? (state.projects[projectId]?.isOpen ?? false) : false,
  );
  const toggleAiPanel = useAiPanelStore((state) => state.togglePanel);
  const setAiActiveTab = useAiPanelStore((state) => state.setActiveTab);

  type NavItem = {
    title: string;
    url: string;
    icon: React.ComponentType<{ className?: string }>;
  };

  type NavGroup = {
    label: string;
    items: NavItem[];
  };

  const globalNavItems: NavItem[] = [
    {
      title: "Dashboard",
      url: "/",
      icon: LayoutDashboard,
    },
    {
      title: "Projects",
      url: "/projects",
      icon: FolderKanban,
    },
  ];

  const projectBackNavItems: NavItem[] = [
    {
      title: "Back to Projects",
      url: "/projects",
      icon: ArrowLeft,
    },
  ];

  const projectPrimaryNavItems: NavItem[] = [
    {
      title: "Overview",
      url: `/projects/${projectId}`,
      icon: LayoutDashboard,
    },
    {
      title: "Tasks",
      url: `/projects/${projectId}/tasks`,
      icon: ListTodo,
    },
    {
      title: "Kanban",
      url: `/projects/${projectId}/kanban`,
      icon: Kanban,
    },
  ];

  const projectPlanningNavItems: NavItem[] = [
    {
      title: "Gantt",
      url: `/projects/${projectId}/gantt`,
      icon: GanttChart,
    },
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
  ];

  const projectAnalysisNavItems: NavItem[] = [
    {
      title: "Utilization",
      url: `/projects/${projectId}/utilization`,
      icon: BarChart3,
    },
    {
      title: "Reports",
      url: `/projects/${projectId}/reports`,
      icon: BarChart3,
    },
  ];

  const projectNavGroups: NavGroup[] = [
    { label: "Project", items: projectBackNavItems },
    { label: "Work", items: projectPrimaryNavItems },
    { label: "Planning", items: projectPlanningNavItems },
    { label: "Insights", items: projectAnalysisNavItems },
  ];

  const renderNavItems = (items: NavItem[]) => (
    <SidebarMenu>
      {items.map((item) => {
        const isActive =
          item.url === "/"
            ? location.pathname === "/"
            : location.pathname === item.url ||
              (item.url !== "/projects" && location.pathname.startsWith(item.url + "/"));

        return (
          <SidebarMenuItem key={item.title}>
            <SidebarMenuButton asChild isActive={isActive} tooltip={item.title}>
              <Link to={item.url}>
                <item.icon />
                <span>{item.title}</span>
              </Link>
            </SidebarMenuButton>
          </SidebarMenuItem>
        );
      })}
    </SidebarMenu>
  );

  return (
    <Sidebar collapsible="icon" {...props}>
      <SidebarHeader>
        <OrgSwitcher />
      </SidebarHeader>

      <SidebarContent>
        {isProjectContext ? (
          <>
            {projectNavGroups.map((group, index) => (
              <SidebarGroup key={group.label}>
                <SidebarGroupLabel>{group.label}</SidebarGroupLabel>
                <SidebarSeparator className="my-1" />
                <SidebarGroupContent>
                  {renderNavItems(group.items)}
                  {group.label === "Insights" ? (
                    <SidebarMenu>
                      <SidebarMenuItem key="AI Assistant">
                        <SidebarMenuButton
                          type="button"
                          isActive={isAiPanelOpen}
                          tooltip="AI Assistant"
                          onClick={() => {
                            if (!projectId) return;
                            setAiActiveTab(projectId, "chat");
                            toggleAiPanel(projectId);
                          }}
                        >
                          <Sparkles />
                          <span>AI Assistant</span>
                        </SidebarMenuButton>
                      </SidebarMenuItem>
                    </SidebarMenu>
                  ) : null}
                  {index < projectNavGroups.length - 1 ? <SidebarSeparator className="mt-2" /> : null}
                </SidebarGroupContent>
              </SidebarGroup>
            ))}
          </>
        ) : (
          <SidebarGroup>
            <SidebarGroupLabel>Organization</SidebarGroupLabel>
            <SidebarSeparator className="my-1" />
            <SidebarGroupContent>
              {renderNavItems(globalNavItems)}
              <SidebarSeparator className="mt-2" />
            </SidebarGroupContent>
          </SidebarGroup>
        )}
      </SidebarContent>

      <SidebarFooter>
        <NavUser />
      </SidebarFooter>

      <SidebarRail />
    </Sidebar>
  );
}
