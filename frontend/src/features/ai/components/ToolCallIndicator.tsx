import { CheckCircle2, Loader2, XCircle } from "lucide-react";
import { cn } from "@/shared/lib/utils";

interface ToolCallIndicatorProps {
  toolName: string;
  status: "running" | "done" | "error" | "denied";
}

const TOOL_LABELS: Record<string, string> = {
  get_tasks: "Hämtar tasks",
  get_task: "Hämtar task",
  search_tasks: "Söker tasks",
  get_dependencies: "Hämtar beroenden",
  get_critical_path: "Analyserar kritisk väg",
  get_project_summary: "Hämtar projektöversikt",
  get_members: "Hämtar projektmedlemmar",
  create_task: "Skapar task",
  update_task: "Uppdaterar task",
  bulk_create_tasks: "Skapar tasks",
  add_dependency: "Lägger till beroende",
  indent_task: "Indentar task",
  outdent_task: "Outdentar task",
  reorder_task: "Sorterar om task",
  calculate_schedule: "Beräknar schema",
  delete_task: "Tar bort task",
  delete_dependency: "Tar bort beroende",
  navigate: "Navigerar",
  highlight_tasks: "Markerar tasks",
  open_task: "Öppnar task",
  filter_view: "Filtrerar vy",
};

export function ToolCallIndicator({ toolName, status }: ToolCallIndicatorProps) {
  const label = TOOL_LABELS[toolName] ?? toolName;

  return (
    <div
      className={cn(
        "flex items-center gap-2 rounded-md border px-2.5 py-1.5 text-xs",
        status === "running" && "border-border bg-muted/40 text-muted-foreground",
        status === "done" && "border-emerald-200 bg-emerald-50 text-emerald-700 dark:border-emerald-800 dark:bg-emerald-950/30 dark:text-emerald-400",
        status === "error" && "border-destructive/30 bg-destructive/5 text-destructive",
        status === "denied" && "border-amber-200 bg-amber-50 text-amber-700 dark:border-amber-800 dark:bg-amber-950/30 dark:text-amber-400",
      )}
    >
      {status === "running" && <Loader2 className="size-3 animate-spin" />}
      {status === "done" && <CheckCircle2 className="size-3" />}
      {status === "error" && <XCircle className="size-3" />}
      {status === "denied" && <XCircle className="size-3" />}
      <span>
        {status === "running" && `${label}...`}
        {status === "done" && `${label}`}
        {status === "error" && `${label} misslyckades`}
        {status === "denied" && `${label} avvisades`}
      </span>
    </div>
  );
}
