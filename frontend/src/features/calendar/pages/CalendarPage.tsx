import { CalendarDays } from "lucide-react";
import { PageShell } from "@/shared/components/layout/PageShell";
import { PageHeader } from "@/shared/components/layout/PageHeader";
import { PageEmpty } from "@/shared/components/state/PageEmpty";

export default function CalendarPage() {
  return (
    <PageShell>
      <PageHeader
        title="Calendar"
        description="Track project milestones and deadlines."
      />
      <PageEmpty
        icon={CalendarDays}
        title="Calendar view coming soon"
        description="Your project timeline and key dates will appear here."
      />
    </PageShell>
  );
}
