import { Navigate, Outlet, useParams } from "react-router";

import { AiDockedPanel, useAiPanelStore } from "@/features/ai";
import { useIsMobile } from "@/shared/hooks/use-mobile";
import {
  ResizableHandle,
  ResizablePanel,
  ResizablePanelGroup,
} from "@/shared/ui/resizable";
import { Drawer, DrawerContent } from "@/shared/ui/drawer";

export function ProjectLayout() {
  const { projectId } = useParams<{ projectId: string }>();
  const isMobile = useIsMobile();

  if (!projectId) {
    return <Navigate to="/projects" replace />;
  }

  const projectPanelState = useAiPanelStore((state) => state.projects[projectId]);
  const isOpen = projectPanelState?.isOpen ?? false;
  const panelSize = projectPanelState?.panelSize ?? 34;

  const setPanelOpen = useAiPanelStore((state) => state.setPanelOpen);
  const setPanelSize = useAiPanelStore((state) => state.setPanelSize);

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
          onClose={() => setPanelOpen(projectId, false)}
        />
      </ResizablePanel>
    </ResizablePanelGroup>
  );
}
