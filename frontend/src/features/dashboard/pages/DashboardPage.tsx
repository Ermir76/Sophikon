import { useOrgStore, useOrganization } from "@/features/organizations";
import { QueryError } from "@/shared/components/QueryError";
import { getErrorMessage } from "@/shared/lib/errors";
import { PageShell } from "@/shared/components/layout/PageShell";
import { PageHeader } from "@/shared/components/layout/PageHeader";
import { PageLoading } from "@/shared/components/state/PageLoading";
import { PageEmpty } from "@/shared/components/state/PageEmpty";

export default function DashboardPage() {
  const activeOrgId = useOrgStore((state) => state.activeOrgId);
  const {
    data: activeOrganization,
    isLoading,
    isError,
    error,
  } = useOrganization(activeOrgId);

  if (isLoading) {
    return <PageLoading message="Loading dashboard..." />;
  }

  if (isError) {
    return (
      <PageShell>
        <QueryError message={getErrorMessage(error)} />
      </PageShell>
    );
  }

  if (!activeOrganization) {
    return (
      <PageShell>
        <PageEmpty
          title="Welcome to Sophikon"
          description="Please select or create an organization to get started."
        />
      </PageShell>
    );
  }

  return (
    <PageShell>
      <PageHeader
        title={activeOrganization ? `${activeOrganization.name} Dashboard` : "Dashboard"}
        description="Overview of your projects and organization metrics."
      />
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
    </PageShell>
  );
}
