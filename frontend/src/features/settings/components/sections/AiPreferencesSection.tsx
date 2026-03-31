import { Bot } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";

import { useAiPreferences, useUpdateAiPreferences } from "@/features/auth";
import { QueryError } from "@/shared/components/QueryError";
import { getErrorMessage } from "@/shared/lib/errors";
import { Label } from "@/shared/ui/label";
import { Separator } from "@/shared/ui/separator";
import { Switch } from "@/shared/ui/switch";

const AI_TOOL_LABELS: Record<string, string> = {
  create_task: "Create task",
  update_task: "Update task",
  bulk_create_tasks: "Bulk create tasks",
  add_dependency: "Add dependency",
  indent_task: "Indent task",
  outdent_task: "Outdent task",
  reorder_task: "Reorder task",
  calculate_schedule: "Calculate schedule",
  navigate: "Navigate view",
  highlight_tasks: "Highlight tasks",
  open_task: "Open task panel",
  filter_view: "Filter view",
};

const AI_TOOL_GROUPS = [
  {
    title: "Task creation and updates",
    description: "Tools that create or modify project data",
    tools: [
      "create_task",
      "update_task",
      "bulk_create_tasks",
      "add_dependency",
      "indent_task",
      "outdent_task",
      "reorder_task",
      "calculate_schedule",
    ],
  },
  {
    title: "Navigation and focus",
    description: "Tools that change the current view without modifying data",
    tools: ["navigate", "highlight_tasks", "open_task", "filter_view"],
  },
];

export function AiPreferencesSection() {
  const aiPreferencesQuery = useAiPreferences();
  const updateAiPreferencesMutation = useUpdateAiPreferences();
  const [optimisticOverrides, setOptimisticOverrides] = useState<Record<string, boolean>>({});
  const [pendingAiToolName, setPendingAiToolName] = useState<string | null>(null);

  const aiAutoApprove = {
    ...(aiPreferencesQuery.data?.auto_approve ?? {}),
    ...optimisticOverrides,
  };

  const handleAiToggle = (toolName: string, value: boolean) => {
    if (pendingAiToolName) {
      return;
    }

    setPendingAiToolName(toolName);
    setOptimisticOverrides((current) => ({ ...current, [toolName]: value }));
    updateAiPreferencesMutation.mutate(
      { auto_approve: { [toolName]: value } },
      {
        onSuccess: () => {
          setPendingAiToolName(null);
          setOptimisticOverrides((current) => {
            const next = { ...current };
            delete next[toolName];
            return next;
          });
          toast.success("Preferences saved");
        },
        onError: (error) => {
          setPendingAiToolName(null);
          setOptimisticOverrides((current) => {
            const next = { ...current };
            delete next[toolName];
            return next;
          });
          toast.error(getErrorMessage(error));
        },
      },
    );
  };

  return (
    <section className="space-y-5">
      <div className="space-y-1">
        <h2 className="flex items-center gap-2 text-xl font-semibold text-foreground">
          <Bot className="h-4 w-4" />
          AI Preferences
        </h2>
        <p className="text-sm text-muted-foreground">
          Control which actions the AI can take autonomously. Delete actions always require approval.
        </p>
      </div>
      {aiPreferencesQuery.isLoading ? (
        <p className="text-sm text-muted-foreground">Loading preferences...</p>
      ) : aiPreferencesQuery.isError ? (
        <QueryError
          message={getErrorMessage(aiPreferencesQuery.error)}
          onRetry={() => aiPreferencesQuery.refetch()}
        />
      ) : (
        <div className="space-y-6">
          {AI_TOOL_GROUPS.map((group, index) => (
            <div key={group.title} className="space-y-3">
              <div>
                <p className="text-sm font-medium">{group.title}</p>
                <p className="text-xs text-muted-foreground">{group.description}</p>
              </div>

              <div className="rounded-md border">
                <div className="grid grid-cols-[1fr_auto] border-b px-3 py-2 text-xs font-medium text-muted-foreground">
                  <span>Tool</span>
                  <span>Auto-approve</span>
                </div>
                {group.tools.map((toolName) => (
                  <div
                    key={toolName}
                    className="grid grid-cols-[1fr_auto] items-center border-b px-3 py-2 last:border-b-0"
                  >
                    <Label htmlFor={`ai-tool-${toolName}`} className="text-sm font-normal">
                      {AI_TOOL_LABELS[toolName] ?? toolName}
                    </Label>
                    <Switch
                      id={`ai-tool-${toolName}`}
                      checked={aiAutoApprove[toolName] ?? true}
                      onCheckedChange={(checked) => handleAiToggle(toolName, checked)}
                      aria-busy={pendingAiToolName === toolName}
                    />
                  </div>
                ))}
              </div>

              {index < AI_TOOL_GROUPS.length - 1 ? <Separator /> : null}
            </div>
          ))}
        </div>
      )}
    </section>
  );
}
