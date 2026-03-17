import { useState } from "react";
import { CheckCircle2, ChevronDown, ChevronRight, Loader2, XCircle } from "lucide-react";

import { cn } from "@/shared/lib/utils";
import type { ToolCallStatus } from "@/features/ai/types";

const TOOL_LABELS: Record<string, string> = {
  get_tasks: "Hämtar tasks",
  get_task: "Hämtar task",
  search_tasks: "Söker tasks",
  get_dependencies: "Hämtar beroenden",
  get_critical_path: "Analyserar kritisk väg",
  get_project_summary: "Hämtar projektöversikt",
  get_members: "Hämtar projektmedlemmar",
  get_resources: "Hämtar resurser",
  get_utilization: "Hämtar resursutnyttjande",
  get_assignments: "Hämtar tilldelningar",
  get_activity_log: "Hämtar aktivitetslogg",
  get_comments: "Hämtar kommentarer",
  get_calendar: "Hämtar kalender",
  get_insights: "Hämtar insikter",
  create_task: "Skapar task",
  update_task: "Uppdaterar task",
  bulk_create_tasks: "Skapar tasks",
  add_dependency: "Lägger till beroende",
  indent_task: "Indentar task",
  outdent_task: "Outdentar task",
  reorder_task: "Sorterar om task",
  calculate_schedule: "Beräknar schema",
  assign_resource: "Tilldelar resurs",
  unassign_resource: "Tar bort resurstilldelning",
  post_comment: "Skriver kommentar",
  send_notification: "Skickar notis",
  delete_task: "Tar bort task",
  delete_dependency: "Tar bort beroende",
  navigate: "Navigerar",
  highlight_tasks: "Markerar tasks",
  open_task: "Öppnar task",
  filter_view: "Filtrerar vy",
};

interface ToolCallRowProps {
  toolName: string;
  status: ToolCallStatus;
  result?: string;
}

export function ToolCallRow({ toolName, status, result }: ToolCallRowProps) {
  const [expanded, setExpanded] = useState(false);
  const label = TOOL_LABELS[toolName] ?? toolName;
  const hasResult = status === "done" && Boolean(result);

  return (
    <div
      className={cn(
        "rounded-md border px-2.5 py-1.5 text-xs",
        status === "running" && "border-border bg-muted/40 text-muted-foreground",
        status === "done" &&
          "border-emerald-200 bg-emerald-50 text-emerald-700 dark:border-emerald-800 dark:bg-emerald-950/30 dark:text-emerald-400",
        status === "error" && "border-destructive/30 bg-destructive/5 text-destructive",
        status === "denied" &&
          "border-amber-200 bg-amber-50 text-amber-700 dark:border-amber-800 dark:bg-amber-950/30 dark:text-amber-400",
      )}
    >
      <div className="flex items-center gap-2">
        {status === "running" && <Loader2 className="size-3 shrink-0 animate-spin" />}
        {status === "done" && <CheckCircle2 className="size-3 shrink-0" />}
        {status === "error" && <XCircle className="size-3 shrink-0" />}
        {status === "denied" && <XCircle className="size-3 shrink-0" />}
        <span className="flex-1">
          {status === "running" && `${label}...`}
          {status === "done" && label}
          {status === "error" && `${label} misslyckades`}
          {status === "denied" && `${label} avvisades`}
        </span>
        {hasResult ? (
          <button
            type="button"
            className="shrink-0 opacity-60 hover:opacity-100"
            onClick={() => setExpanded((v) => !v)}
          >
            {expanded ? <ChevronDown className="size-3" /> : <ChevronRight className="size-3" />}
          </button>
        ) : null}
      </div>

      {expanded && result ? (
        <pre className="mt-1.5 max-h-40 overflow-auto whitespace-pre-wrap break-all rounded bg-black/5 px-2 py-1 text-[10px] dark:bg-white/5">
          {result}
        </pre>
      ) : null}
    </div>
  );
}
