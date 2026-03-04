import { BarChart3 } from "lucide-react";
import { PageShell } from "@/shared/components/layout/PageShell";
import { PageHeader } from "@/shared/components/layout/PageHeader";
import { PageEmpty } from "@/shared/components/state/PageEmpty";

export default function ReportsPage() {
  return (
    <PageShell>
      <PageHeader
        title="Reports"
        description="Analyze project health, budget, and performance metrics."
      />
      <PageEmpty
        icon={BarChart3}
        title="Reports coming soon"
        description="Performance and budget reporting widgets will be available here."
      />
    </PageShell>
  );
}
