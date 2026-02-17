import { Outlet } from "react-router";
import { useOrgStore } from "@/features/organizations/store/org-store";

export function OrgGuard() {
  const activeOrgId = useOrgStore((state) => state.activeOrgId);

  // If we had a global loading state for orgs, we'd check it here.
  // For now, we assume if activeOrgId is null, we need selection.

  if (!activeOrgId) {
    return (
      <div className="flex h-full flex-col items-center justify-center space-y-4 p-8 text-center">
        <h3 className="text-xl font-medium">No Organization Selected</h3>
        <p className="text-muted-foreground">
          Please select an organization from the sidebar to continue.
        </p>
      </div>
    );
  }

  return <Outlet />;
}
