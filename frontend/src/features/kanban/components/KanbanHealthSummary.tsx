import { Loader2, Sparkles } from "lucide-react";
import type { AiSuggestion } from "@/features/ai/types";
import { QueryError } from "@/shared/components/QueryError";
import { Badge } from "@/shared/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/shared/ui/card";

interface KanbanHealthSummaryProps {
    suggestions: AiSuggestion[];
    hasRequested: boolean;
    isLoading: boolean;
    isError: boolean;
    taskNameById: Record<string, string>;
    onRetry: () => void;
    onRiskClick: (taskId: string) => void;
}

function severityClassName(severity: "HIGH" | "MEDIUM"): string {
    return severity === "HIGH"
        ? "border-destructive/50 bg-destructive/15 text-destructive"
        : "border-chart-3/50 bg-chart-3/15 text-chart-3";
}

export function KanbanHealthSummary({
    suggestions,
    hasRequested,
    isLoading,
    isError,
    taskNameById,
    onRetry,
    onRiskClick,
}: KanbanHealthSummaryProps) {
    const riskSuggestions = suggestions.filter(
        (suggestion) => suggestion.severity === "HIGH" || suggestion.severity === "MEDIUM",
    );

    const grouped = new Map<string, AiSuggestion[]>();
    for (const suggestion of riskSuggestions) {
        const key = suggestion.affected_task_id ?? "__project__";
        const existing = grouped.get(key);
        if (existing) {
            existing.push(suggestion);
            continue;
        }
        grouped.set(key, [suggestion]);
    }

    return (
        <Card className="py-3">
            <CardHeader className="px-4">
                <CardTitle className="flex items-center gap-2 text-sm font-semibold">
                    <Sparkles className="size-4 text-muted-foreground" />
                    Sprint Health Summary
                </CardTitle>
            </CardHeader>
            <CardContent className="px-4">
                {isError ? (
                    <QueryError
                        message="Failed to load sprint health summary."
                        onRetry={onRetry}
                    />
                ) : isLoading ? (
                    <div className="rounded-lg border border-dashed p-4 text-sm text-muted-foreground">
                        <Loader2 className="mr-2 inline size-4 animate-spin" />
                        Generating sprint health summary...
                    </div>
                ) : riskSuggestions.length > 0 ? (
                    <div className="space-y-3">
                        {Array.from(grouped.entries()).map(([taskId, taskSuggestions]) => {
                            const taskName = taskNameById[taskId] ?? "Unknown task";
                            const isTaskScoped = taskId !== "__project__";
                            return (
                                <section
                                    key={taskId}
                                    className="rounded-lg border border-border/60 p-3"
                                >
                                    <div className="mb-2 flex items-center justify-between gap-2">
                                        <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                                            {isTaskScoped ? taskName : "Project-level risks"}
                                        </p>
                                    </div>
                                    <ul className="space-y-2">
                                        {taskSuggestions.map((suggestion) => (
                                            <li key={suggestion.id}>
                                                {suggestion.affected_task_id ? (
                                                    <button
                                                        type="button"
                                                        className="w-full rounded-md border border-transparent p-2 text-left transition-colors hover:border-border hover:bg-muted/30"
                                                        onClick={() => {
                                                            const taskId = suggestion.affected_task_id;
                                                            if (!taskId) return;
                                                            onRiskClick(taskId);
                                                        }}
                                                    >
                                                        <div className="flex items-start justify-between gap-3">
                                                            <p className="text-sm font-medium">
                                                                {suggestion.title}
                                                            </p>
                                                            <Badge
                                                                variant="outline"
                                                                className={severityClassName(suggestion.severity)}
                                                            >
                                                                {suggestion.severity.toLowerCase()}
                                                            </Badge>
                                                        </div>
                                                        <p className="mt-1 text-xs text-muted-foreground">
                                                            {suggestion.description}
                                                        </p>
                                                    </button>
                                                ) : (
                                                    <div className="rounded-md p-2">
                                                        <div className="flex items-start justify-between gap-3">
                                                            <p className="text-sm font-medium">
                                                                {suggestion.title}
                                                            </p>
                                                            <Badge
                                                                variant="outline"
                                                                className={severityClassName(suggestion.severity)}
                                                            >
                                                                {suggestion.severity.toLowerCase()}
                                                            </Badge>
                                                        </div>
                                                        <p className="mt-1 text-xs text-muted-foreground">
                                                            {suggestion.description}
                                                        </p>
                                                    </div>
                                                )}
                                            </li>
                                        ))}
                                    </ul>
                                </section>
                            );
                        })}
                    </div>
                ) : hasRequested ? (
                    <div className="rounded-lg border border-dashed p-4 text-sm text-muted-foreground">
                        No HIGH or MEDIUM risk signals right now.
                    </div>
                ) : (
                    <div className="rounded-lg border border-dashed p-4 text-sm text-muted-foreground">
                        Run Sprint Health to generate AI risk signals for this board.
                    </div>
                )}
            </CardContent>
        </Card>
    );
}
