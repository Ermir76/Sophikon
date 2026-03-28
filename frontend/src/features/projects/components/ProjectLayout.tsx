import { isAxiosError } from "axios";
import { Link, Navigate, Outlet, useParams } from "react-router";

import { AiDockedPanel, useAiPanelStore } from "@/features/ai";
import { useProject } from "@/features/projects/hooks/useProjects";
import { useProjectWebSocket } from "@/features/projects/hooks/useProjectWebSocket";
import { QueryError } from "@/shared/components/QueryError";
import { useIsMobile } from "@/shared/hooks/use-mobile";
import {
  ResizableHandle,
  ResizablePanel,
  ResizablePanelGroup,
} from "@/shared/ui/resizable";
import { Button } from "@/shared/ui/button";
import { Drawer, DrawerContent } from "@/shared/ui/drawer";

export function ProjectLayout() {
  const { projectId } = useParams<{ projectId: string }>();
  const isMobile = useIsMobile();
  const resolvedProjectId = projectId ?? "";
  const projectQuery = useProject(projectId);
  const hasProjectAccessError = isAxiosError(projectQuery.error)
    && projectQuery.error.response?.status === 403;
  const isAgentEnabled = projectQuery.data?.settings?.agent_enabled !== false;

  useProjectWebSocket(projectId);

  const projectPanelState = useAiPanelStore(
    (state) => state.projects[resolvedProjectId],
  );
  const isOpen = projectPanelState?.isOpen ?? false;
  const panelSize = projectPanelState?.panelSize ?? 34;

  const setPanelOpen = useAiPanelStore((state) => state.setPanelOpen);
  const setPanelSize = useAiPanelStore((state) => state.setPanelSize);

  if (!projectId) {
    return <Navigate to="/projects" replace />;
  }

  if (hasProjectAccessError) {
    return (
      <div className="mx-auto flex h-full w-full max-w-3xl flex-col justify-center gap-4 px-6 py-8">
        <QueryError message="You no longer have access to this project." />
        <div>
          <Button asChild variant="outline">
            <Link to="/projects">Back to Projects</Link>
          </Button>
        </div>
      </div>
    );
  }

  if (isMobile) {
    return (
      <>
        <div className="flex h-full w-full min-h-0 min-w-0 flex-col">
          <Outlet />
        </div>
        <Drawer open={isOpen} onOpenChange={(open) => setPanelOpen(projectId, open)} direction="right">
          <DrawerContent className="p-0">
            <AiDockedPanel
              projectId={projectId}
              isAgentEnabled={isAgentEnabled}
              mode="drawer"
              onClose={() => setPanelOpen(projectId, false)}
            />
          </DrawerContent>
        </Drawer>
      </>
    );
  }

  if (!isOpen) {
    return (
      <div className="flex h-full w-full min-h-0 min-w-0 flex-col">
        <Outlet />
      </div>
    );
  }

  return (
    <ResizablePanelGroup orientation="horizontal" className="h-full w-full min-h-0 min-w-0">
      <ResizablePanel defaultSize={`${100 - panelSize}%`} minSize="45%">
        <div className="h-full w-full min-h-0 min-w-0">
          <Outlet />
        </div>
      </ResizablePanel>
      <ResizableHandle withHandle />
      <ResizablePanel
        defaultSize={`${panelSize}%`}
        minSize="20%"
        maxSize="55%"
        onResize={(size) => setPanelSize(projectId, Number.parseFloat(String(size)))}
      >
        <AiDockedPanel
          projectId={projectId}
          isAgentEnabled={isAgentEnabled}
          onClose={() => setPanelOpen(projectId, false)}
        />
      </ResizablePanel>
    </ResizablePanelGroup>
  );
}
