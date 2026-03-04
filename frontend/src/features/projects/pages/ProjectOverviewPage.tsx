import { useParams } from "react-router";
import { LayoutDashboard } from "lucide-react";
import { PageShell } from "@/shared/components/layout/PageShell";
import { PageHeader } from "@/shared/components/layout/PageHeader";
import { PageEmpty } from "@/shared/components/state/PageEmpty";

export default function ProjectOverviewPage() {
  const { projectId } = useParams();

  return (
    <PageShell>
      <PageHeader
        title="Project Overview"
        description={`Overview for project ${projectId}.`}
      />
      <PageEmpty
        icon={LayoutDashboard}
        title="Overview widgets coming soon"
        description="Project summary, progress, and risk indicators will be shown here."
      />
    </PageShell>
  );
}
