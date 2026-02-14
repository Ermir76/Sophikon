import { useOrgStore } from "@/store/org-store";

export default function DashboardPage() {
  const { activeOrganization } = useOrgStore();

  return (
    <div className="flex flex-1 flex-col gap-4 p-4">
      <div>
        <h1 className="text-2xl font-semibold">
          {activeOrganization
            ? `${activeOrganization.name} Dashboard`
            : "Dashboard"}
        </h1>
        <p className="text-muted-foreground">
          Overview of your projects and organization metrics.
        </p>
      </div>
      <div className="grid auto-rows-min gap-4 md:grid-cols-3">
        <div className="aspect-video rounded-xl bg-muted/50 flex items-center justify-center p-4 text-center">
          <span className="text-sm font-medium">Projects Overview</span>
        </div>
        <div className="aspect-video rounded-xl bg-muted/50 flex items-center justify-center p-4 text-center">
          <span className="text-sm font-medium">Active Tasks</span>
        </div>
        <div className="aspect-video rounded-xl bg-muted/50 flex items-center justify-center p-4 text-center">
          <span className="text-sm font-medium">Team Activity</span>
        </div>
      </div>
      <div className="min-h-[50vh] flex-1 rounded-xl bg-muted/50 p-6">
        <h3 className="text-lg font-medium mb-4">Recent Activity</h3>
        <p className="text-sm text-muted-foreground">
          No recent activity to show.
        </p>
      </div>
    </div>
  );
}
