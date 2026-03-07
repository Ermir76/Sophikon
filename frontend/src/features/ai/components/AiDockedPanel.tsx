import { useMemo, useState } from "react";
import { useLocation } from "react-router";
import {
  Bot,
  Lightbulb,
  RefreshCcw,
  SendHorizontal,
  WandSparkles,
  X,
} from "lucide-react";
import { toast } from "sonner";

import { aiService } from "@/features/ai/api/ai.service";
import { useAiEstimate, useAiSuggestions } from "@/features/ai/hooks/useAi";
import { useAiPanelStore } from "@/features/ai/store/ai-panel-store";
import type { AiEstimateItem, AiSuggestion, AiTab } from "@/features/ai/types";
import { useTasks, useUpdateTask } from "@/features/tasks/hooks/useTasks";
import { useCreateDependency } from "@/features/tasks/hooks/useDependencies";
import { getErrorMessage } from "@/shared/lib/errors";
import { cn } from "@/shared/lib/utils";
import { Badge } from "@/shared/ui/badge";
import { Button } from "@/shared/ui/button";
import { Input } from "@/shared/ui/input";
import { ScrollArea } from "@/shared/ui/scroll-area";
import { Separator } from "@/shared/ui/separator";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/shared/ui/tabs";
import { Textarea } from "@/shared/ui/textarea";

interface AiDockedPanelProps {
  projectId: string;
  mode?: "docked" | "drawer";
  onClose?: () => void;
}

function formatDuration(minutes: number): string {
  if (minutes < 60) return `${minutes}m`;
  const hours = Math.floor(minutes / 60);
  const rem = minutes % 60;
  if (hours < 8) return rem > 0 ? `${hours}h ${rem}m` : `${hours}h`;
  const days = (minutes / 480).toFixed(1).replace(/\.0$/, "");
  return `${days}d`;
}

function suggestionToneClass(severity: AiSuggestion["severity"]): string {
  if (severity === "HIGH") return "text-destructive";
  if (severity === "MEDIUM") return "text-amber-500";
  return "text-emerald-500";
}

function readString(payload: Record<string, unknown>, key: string): string | null {
  const value = payload[key];
  return typeof value === "string" ? value : null;
}

function readNumber(payload: Record<string, unknown>, key: string): number | null {
  const value = payload[key];
  return typeof value === "number" ? value : null;
}

export function AiDockedPanel({
  projectId,
  mode = "docked",
  onClose,
}: AiDockedPanelProps) {
  const location = useLocation();
  const currentView = location.pathname.split("/")[3] ?? "overview";

  const projectPanel = useAiPanelStore((state) => state.projects[projectId]);
  const activeTab = projectPanel?.activeTab ?? "chat";
  const conversationId = projectPanel?.conversationId ?? null;
  const messages = projectPanel?.messages ?? [];

  const setActiveTab = useAiPanelStore((state) => state.setActiveTab);
  const setConversationId = useAiPanelStore((state) => state.setConversationId);
  const appendMessage = useAiPanelStore((state) => state.appendMessage);
  const appendToMessage = useAiPanelStore((state) => state.appendToMessage);
  const replaceMessageContent = useAiPanelStore(
    (state) => state.replaceMessageContent,
  );
  const clearConversation = useAiPanelStore((state) => state.clearConversation);

  const [chatInput, setChatInput] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const [selectedTaskIds, setSelectedTaskIds] = useState<string[]>([]);
  const [adHocTaskName, setAdHocTaskName] = useState("");
  const [adHocTaskDescription, setAdHocTaskDescription] = useState("");
  const [estimateResults, setEstimateResults] = useState<AiEstimateItem[]>([]);

  const { data: tasksData } = useTasks(projectId);
  const estimateMutation = useAiEstimate(projectId);
  const suggestionsQuery = useAiSuggestions(
    projectId,
    8,
    activeTab === "suggestions",
  );
  const updateTaskMutation = useUpdateTask(projectId);
  const createDependencyMutation = useCreateDependency(projectId);

  const taskOptions = useMemo(() => (tasksData?.items ?? []).slice(0, 20), [tasksData]);

  const sendMessage = async () => {
    const trimmed = chatInput.trim();
    if (!trimmed || isStreaming) return;

    const userMessageId = crypto.randomUUID();
    const assistantMessageId = crypto.randomUUID();

    appendMessage(projectId, {
      id: userMessageId,
      role: "user",
      content: trimmed,
      createdAt: Date.now(),
    });
    appendMessage(projectId, {
      id: assistantMessageId,
      role: "assistant",
      content: "",
      createdAt: Date.now(),
    });
    setChatInput("");
    setIsStreaming(true);

    let hadChunk = false;
    try {
      await aiService.streamChat(
        projectId,
        {
          message: trimmed,
          conversation_id: conversationId,
          ui_context: {
            current_view: currentView,
            selected_task_ids: selectedTaskIds,
          },
          history: messages.slice(-8).map((message) => ({
            role: message.role,
            content: message.content,
          })),
        },
        (event) => {
          if (event.type === "start" && event.conversation_id) {
            setConversationId(projectId, event.conversation_id);
          }
          if (event.type === "chunk") {
            hadChunk = true;
            appendToMessage(projectId, assistantMessageId, event.content);
          }
          if (event.type === "error") {
            toast.error(event.error || "AI chat failed");
          }
        },
      );
    } catch (error) {
      replaceMessageContent(projectId, assistantMessageId, "Unable to generate a response.");
      toast.error(getErrorMessage(error));
    } finally {
      if (!hadChunk) {
        replaceMessageContent(
          projectId,
          assistantMessageId,
          "No response generated for this prompt.",
        );
      }
      setIsStreaming(false);
    }
  };

  const runEstimate = async () => {
    if (!selectedTaskIds.length && !adHocTaskName.trim()) {
      toast.error("Select task(s) or provide an ad-hoc task name");
      return;
    }

    try {
      const response = await estimateMutation.mutateAsync({
        task_ids: selectedTaskIds.length ? selectedTaskIds : undefined,
        task_name: selectedTaskIds.length ? undefined : adHocTaskName.trim(),
        task_description: selectedTaskIds.length
          ? undefined
          : adHocTaskDescription.trim() || undefined,
        include_reasoning: true,
        ui_context: {
          current_view: currentView,
          selected_task_ids: selectedTaskIds,
        },
      });
      setEstimateResults(response.estimates);
    } catch (error) {
      toast.error(getErrorMessage(error));
    }
  };

  const applyEstimate = async (estimate: AiEstimateItem) => {
    if (!estimate.task_id) {
      toast.error("This estimate is not linked to an existing task");
      return;
    }

    try {
      await updateTaskMutation.mutateAsync({
        taskId: estimate.task_id,
        data: {
          duration: Math.max(0, Math.round(estimate.recommended_minutes)),
        },
      });
      toast.success("Task duration updated from AI estimate");
    } catch (error) {
      toast.error(getErrorMessage(error));
    }
  };

  const applySuggestion = async (suggestion: AiSuggestion) => {
    const action = suggestion.suggested_action;
    if (!action || action.type === "NONE") {
      toast.message("No direct action available for this suggestion");
      return;
    }

    try {
      if (action.type === "SET_PRIORITY") {
        const taskId = readString(action.payload, "task_id");
        const priority = readNumber(action.payload, "priority");
        if (!taskId || priority === null) {
          throw new Error("Invalid SET_PRIORITY suggestion payload");
        }
        await updateTaskMutation.mutateAsync({
          taskId,
          data: { priority },
        });
      } else if (action.type === "UPDATE_TASK") {
        const taskId = readString(action.payload, "task_id");
        if (!taskId) {
          throw new Error("Invalid UPDATE_TASK suggestion payload");
        }
        const duration = readNumber(action.payload, "duration");
        const priority = readNumber(action.payload, "priority");
        const percentComplete = readNumber(action.payload, "percent_complete");
        if (duration === null && priority === null && percentComplete === null) {
          throw new Error("No supported fields in UPDATE_TASK suggestion payload");
        }
        await updateTaskMutation.mutateAsync({
          taskId,
          data: {
            duration: duration === null ? undefined : Math.max(0, Math.round(duration)),
            priority: priority === null ? undefined : Math.round(priority),
            percent_complete:
              percentComplete === null ? undefined : Math.min(100, Math.max(0, percentComplete)),
          },
        });
      } else if (action.type === "ADD_DEPENDENCY") {
        const predecessorId = readString(action.payload, "predecessor_id");
        const successorId = readString(action.payload, "successor_id");
        if (!predecessorId || !successorId) {
          throw new Error("Invalid ADD_DEPENDENCY suggestion payload");
        }
        const dependencyType = readString(action.payload, "dependency_type");
        await createDependencyMutation.mutateAsync({
          predecessor_id: predecessorId,
          successor_id: successorId,
          type:
            dependencyType === "FS" ||
            dependencyType === "FF" ||
            dependencyType === "SS" ||
            dependencyType === "SF"
              ? dependencyType
              : "FS",
        });
      }

      toast.success("Suggestion applied");
      await suggestionsQuery.refetch();
    } catch (error) {
      toast.error(getErrorMessage(error));
    }
  };

  return (
    <div
      className={cn(
        "flex h-full min-h-0 flex-col bg-card",
        mode === "docked" ? "border-l" : "",
      )}
    >
      <div className="flex items-center justify-between border-b px-3 py-2">
        <div className="flex items-center gap-2">
          <Bot className="size-4 text-primary" />
          <div>
            <p className="text-sm font-semibold">AI Assistant</p>
            <p className="text-[11px] text-muted-foreground">Project-aware guidance</p>
          </div>
        </div>
        <div className="flex items-center gap-1">
          <Button
            type="button"
            variant="ghost"
            size="sm"
            className="h-7 px-2 text-[11px]"
            onClick={() => clearConversation(projectId)}
          >
            New
          </Button>
          {onClose ? (
            <Button
              type="button"
              variant="ghost"
              size="icon"
              className="size-7"
              onClick={onClose}
            >
              <X className="size-4" />
            </Button>
          ) : null}
        </div>
      </div>

      <Tabs
        className="flex min-h-0 flex-1 flex-col"
        value={activeTab}
        onValueChange={(value) => setActiveTab(projectId, value as AiTab)}
      >
        <div className="border-b px-2 py-2">
          <TabsList variant="line" className="w-full justify-start">
            <TabsTrigger value="chat">Chat</TabsTrigger>
            <TabsTrigger value="estimate">Estimate</TabsTrigger>
            <TabsTrigger value="suggestions">Suggestions</TabsTrigger>
          </TabsList>
        </div>

        <TabsContent value="chat" className="flex min-h-0 flex-1 flex-col">
          <ScrollArea className="flex-1 px-3 py-3">
            <div className="space-y-2.5">
              {messages.length === 0 ? (
                <div className="rounded-lg border border-dashed p-4 text-xs text-muted-foreground">
                  Ask about schedule status, overdue tasks, or what to do next.
                </div>
              ) : (
                messages.map((message) => (
                  <div
                    key={message.id}
                    className={cn(
                      "rounded-lg px-3 py-2 text-sm",
                      message.role === "user"
                        ? "ml-6 bg-primary/10 text-foreground"
                        : "mr-6 border bg-card/70 text-foreground",
                    )}
                  >
                    <p className="mb-1 text-[10px] uppercase tracking-wide text-muted-foreground">
                      {message.role}
                    </p>
                    <p className="whitespace-pre-wrap">{message.content}</p>
                  </div>
                ))
              )}
            </div>
          </ScrollArea>
          <div className="border-t p-3">
            <Textarea
              value={chatInput}
              onChange={(event) => setChatInput(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter" && !event.shiftKey) {
                  event.preventDefault();
                  void sendMessage();
                }
              }}
              placeholder="Ask the assistant about this project..."
              className="min-h-[72px] resize-none"
              disabled={isStreaming}
            />
            <div className="mt-2 flex items-center justify-between">
              <p className="text-[11px] text-muted-foreground">
                Enter to send, Shift+Enter for newline
              </p>
              <Button
                type="button"
                size="sm"
                className="h-8 gap-1.5"
                onClick={() => void sendMessage()}
                disabled={isStreaming || !chatInput.trim()}
              >
                <SendHorizontal className="size-3.5" />
                {isStreaming ? "Sending..." : "Send"}
              </Button>
            </div>
          </div>
        </TabsContent>

        <TabsContent value="estimate" className="flex min-h-0 flex-1 flex-col">
          <ScrollArea className="flex-1 px-3 py-3">
            <div className="space-y-3">
              <div className="rounded-md border bg-card/70 p-3">
                <p className="text-xs font-semibold">Select Existing Tasks</p>
                <p className="mt-1 text-[11px] text-muted-foreground">
                  Select one or more tasks to estimate.
                </p>
                <div className="mt-2 max-h-40 space-y-1 overflow-y-auto pr-1">
                  {taskOptions.length ? (
                    taskOptions.map((task) => (
                      <label
                        key={task.id}
                        className="flex cursor-pointer items-center gap-2 rounded px-1.5 py-1 text-xs hover:bg-muted/40"
                      >
                        <input
                          type="checkbox"
                          checked={selectedTaskIds.includes(task.id)}
                          onChange={(event) => {
                            setSelectedTaskIds((prev) =>
                              event.target.checked
                                ? [...prev, task.id]
                                : prev.filter((id) => id !== task.id),
                            );
                          }}
                          className="size-3.5 rounded border border-input bg-background"
                        />
                        <span className="truncate">{task.name}</span>
                      </label>
                    ))
                  ) : (
                    <p className="text-[11px] text-muted-foreground">
                      No tasks available for selection.
                    </p>
                  )}
                </div>
              </div>

              <div className="rounded-md border bg-card/70 p-3">
                <p className="text-xs font-semibold">Or Estimate Ad-Hoc Task</p>
                <div className="mt-2 space-y-2">
                  <Input
                    value={adHocTaskName}
                    onChange={(event) => setAdHocTaskName(event.target.value)}
                    placeholder="Task name"
                    className="h-8 text-xs"
                  />
                  <Textarea
                    value={adHocTaskDescription}
                    onChange={(event) => setAdHocTaskDescription(event.target.value)}
                    placeholder="Task description (optional)"
                    className="min-h-[70px] resize-none text-xs"
                  />
                </div>
              </div>

              <Button
                type="button"
                className="h-8 w-full gap-1.5"
                onClick={() => void runEstimate()}
                disabled={estimateMutation.isPending}
              >
                <WandSparkles className="size-3.5" />
                {estimateMutation.isPending ? "Estimating..." : "Run Estimate"}
              </Button>

              {estimateResults.length ? (
                <div className="space-y-2">
                  <Separator />
                  {estimateResults.map((estimate) => (
                    <div key={`${estimate.task_id ?? estimate.task_name}`} className="rounded-md border p-2.5">
                      <div className="flex items-start justify-between gap-2">
                        <p className="text-sm font-medium">{estimate.task_name}</p>
                        <Badge variant="outline">
                          {Math.round(estimate.confidence * 100)}% conf.
                        </Badge>
                      </div>
                      <p className="mt-1 text-xs text-muted-foreground">
                        O: {formatDuration(estimate.optimistic_minutes)} | L:{" "}
                        {formatDuration(estimate.likely_minutes)} | P:{" "}
                        {formatDuration(estimate.pessimistic_minutes)}
                      </p>
                      {estimate.reasoning ? (
                        <p className="mt-1 text-xs text-muted-foreground">{estimate.reasoning}</p>
                      ) : null}
                      <div className="mt-2 flex justify-end">
                        <Button
                          type="button"
                          variant="outline"
                          size="sm"
                          className="h-7 text-xs"
                          onClick={() => void applyEstimate(estimate)}
                          disabled={!estimate.task_id || updateTaskMutation.isPending}
                        >
                          Apply {formatDuration(estimate.recommended_minutes)}
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              ) : null}
            </div>
          </ScrollArea>
        </TabsContent>

        <TabsContent value="suggestions" className="flex min-h-0 flex-1 flex-col">
          <div className="flex items-center justify-between border-b px-3 py-2">
            <p className="text-xs text-muted-foreground">
              Contextual schedule and dependency suggestions
            </p>
            <Button
              type="button"
              variant="ghost"
              size="icon"
              className="size-7"
              onClick={() => void suggestionsQuery.refetch()}
            >
              <RefreshCcw className="size-3.5" />
            </Button>
          </div>
          <ScrollArea className="flex-1 px-3 py-3">
            <div className="space-y-2">
              {suggestionsQuery.isLoading ? (
                <p className="text-xs text-muted-foreground">Loading suggestions...</p>
              ) : suggestionsQuery.data?.suggestions?.length ? (
                suggestionsQuery.data.suggestions.map((suggestion) => (
                  <div key={suggestion.id} className="rounded-md border p-2.5">
                    <div className="flex items-start justify-between gap-2">
                      <p className="text-sm font-medium">{suggestion.title}</p>
                      <Badge variant="outline" className={suggestionToneClass(suggestion.severity)}>
                        {suggestion.severity}
                      </Badge>
                    </div>
                    <p className="mt-1 text-xs text-muted-foreground">{suggestion.description}</p>
                    <div className="mt-2 flex justify-end">
                      <Button
                        type="button"
                        size="sm"
                        variant="outline"
                        className="h-7 gap-1 text-xs"
                        onClick={() => void applySuggestion(suggestion)}
                        disabled={
                          updateTaskMutation.isPending || createDependencyMutation.isPending
                        }
                      >
                        <Lightbulb className="size-3.5" />
                        Apply
                      </Button>
                    </div>
                  </div>
                ))
              ) : (
                <p className="text-xs text-muted-foreground">
                  No actionable suggestions right now.
                </p>
              )}
            </div>
          </ScrollArea>
        </TabsContent>
      </Tabs>
    </div>
  );
}
