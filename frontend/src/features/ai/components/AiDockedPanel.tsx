import { useEffect, useMemo, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { useLocation, useNavigate } from "react-router";
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
import { ApprovalDialog } from "@/features/ai/components/ApprovalDialog";
import { PlanApprovalCard } from "@/features/ai/components/PlanApprovalCard";
import { ReasoningStep } from "@/features/ai/components/ReasoningStep";
import { ToolCallRow } from "@/features/ai/components/ToolCallRow";
import { useAiEstimate, useAiSuggestions, useApprovePlan } from "@/features/ai/hooks/useAi";
import { useConversations } from "@/features/ai/hooks/useConversations";
import { useAiPanelStore } from "@/features/ai/store/ai-panel-store";
import type { AiChatMessage, AiEstimateItem, AiSuggestion, AiTab } from "@/features/ai/types";
import { useAiPreferences, useUpdateAiPreferences } from "@/features/auth/hooks/useAuth";
import { taskKeys, useTasks, useUpdateTask } from "@/features/tasks/hooks/useTasks";
import { useCreateDependency } from "@/features/tasks/hooks/useDependencies";
import { getErrorMessage } from "@/shared/lib/errors";
import { cn } from "@/shared/lib/utils";
import { Alert, AlertDescription } from "@/shared/ui/alert";
import { Badge } from "@/shared/ui/badge";
import { Button } from "@/shared/ui/button";
import { Input } from "@/shared/ui/input";
import { ScrollArea } from "@/shared/ui/scroll-area";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/shared/ui/select";
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
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const currentView = location.pathname.split("/")[3] ?? "overview";

  const projectPanel = useAiPanelStore((state) => state.projects[projectId]);
  const activeTab = projectPanel?.activeTab ?? "chat";
  const conversationId = projectPanel?.conversationId ?? null;
  const conversationStatus = projectPanel?.conversationStatus ?? null;
  const messages = projectPanel?.messages ?? [];
  const pendingApproval = projectPanel?.pendingApproval ?? null;
  const pendingPlan = projectPanel?.pendingPlan ?? null;
  const isThinking = projectPanel?.isThinking ?? false;
  const reasoningText = projectPanel?.reasoningText ?? "";

  const setActiveTab = useAiPanelStore((state) => state.setActiveTab);
  const setConversationId = useAiPanelStore((state) => state.setConversationId);
  const setConversationStatus = useAiPanelStore((state) => state.setConversationStatus);
  const appendMessage = useAiPanelStore((state) => state.appendMessage);
  const appendToMessage = useAiPanelStore((state) => state.appendToMessage);
  const replaceMessageContent = useAiPanelStore((state) => state.replaceMessageContent);
  const clearConversation = useAiPanelStore((state) => state.clearConversation);
  const loadConversationMessages = useAiPanelStore((state) => state.loadConversationMessages);
  const setPendingApproval = useAiPanelStore((state) => state.setPendingApproval);
  const updateToolStatus = useAiPanelStore((state) => state.updateToolStatus);
  const setToolResult = useAiPanelStore((state) => state.setToolResult);
  const setPendingPlan = useAiPanelStore((state) => state.setPendingPlan);
  const setThinking = useAiPanelStore((state) => state.setThinking);
  const appendReasoningText = useAiPanelStore((state) => state.appendReasoningText);
  const clearReasoningText = useAiPanelStore((state) => state.clearReasoningText);

  const [chatInput, setChatInput] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const [selectedTaskIds, setSelectedTaskIds] = useState<string[]>([]);
  const [adHocTaskName, setAdHocTaskName] = useState("");
  const [adHocTaskDescription, setAdHocTaskDescription] = useState("");
  const [estimateResults, setEstimateResults] = useState<AiEstimateItem[]>([]);
  const [loadingHistory, setLoadingHistory] = useState(false);

  const { data: tasksData } = useTasks(projectId);
  const estimateMutation = useAiEstimate(projectId);
  const suggestionsQuery = useAiSuggestions(projectId, 8, activeTab === "suggestions");
  const updateTaskMutation = useUpdateTask(projectId);
  const createDependencyMutation = useCreateDependency(projectId);
  const aiPreferencesQuery = useAiPreferences();
  const updateAiPreferencesMutation = useUpdateAiPreferences();
  const approvePlanMutation = useApprovePlan(projectId);
  const { data: conversations } = useConversations(projectId);

  const taskOptions = useMemo(() => (tasksData?.items ?? []).slice(0, 20), [tasksData]);
  const aiProviders = aiPreferencesQuery.data?.providers ?? [];
  const selectedProvider =
    aiPreferencesQuery.data?.provider ?? aiPreferencesQuery.data?.defaults?.provider ?? "";
  const selectedModel =
    aiPreferencesQuery.data?.model ?? aiPreferencesQuery.data?.defaults?.model ?? "";
  const providerRecord = aiProviders.find((provider) => provider.provider_id === selectedProvider);
  const providerModels = providerRecord?.models ?? [];
  const modelSelectDisabled = !selectedProvider || providerModels.length === 0;

  const inputBlocked = isStreaming || Boolean(pendingPlan);

  const applyAiPreferencePatch = (patch: { provider?: string | null; model?: string | null }) => {
    updateAiPreferencesMutation.mutate(patch, {
      onSuccess: () => {
        void aiPreferencesQuery.refetch();
      },
      onError: (error) => {
        toast.error(getErrorMessage(error));
      },
    });
  };

  const VIEW_PATHS: Record<string, string> = {
    overview: `/projects/${projectId}`,
    tasks: `/projects/${projectId}/tasks`,
    gantt: `/projects/${projectId}/gantt`,
    calendar: `/projects/${projectId}/calendar`,
    resources: `/projects/${projectId}/resources`,
    reports: `/projects/${projectId}/reports`,
  };

  const handleUiAction = (action: string, payload: Record<string, unknown>) => {
    if (action === "navigate") {
      const view = payload.view as string | undefined;
      const path = view ? (VIEW_PATHS[view] ?? `/projects/${projectId}`) : `/projects/${projectId}`;
      void navigate(path);
    }
  };

  const handleApproval = async (approved: boolean) => {
    if (!pendingApproval) return;
    const { approval_id } = pendingApproval;
    setPendingApproval(projectId, null);
    try {
      await aiService.resolveApproval(projectId, approval_id, approved);
    } catch (error) {
      toast.error(getErrorMessage(error));
    }
  };

  const handlePlanApprove = () => {
    if (!conversationId) return;
    const planSnapshot = pendingPlan;
    approvePlanMutation.mutate(
      { conversationId, approved: true },
      {
        onSuccess: () => {
          setPendingPlan(projectId, null);
          setConversationStatus(projectId, "executing");
        },
        onError: (error) => {
          setPendingPlan(projectId, planSnapshot);
          setConversationStatus(projectId, "awaiting_plan_approval");
          toast.error(getErrorMessage(error));
        },
      },
    );
  };

  const handlePlanRedirect = (feedback: string) => {
    if (!conversationId) return;
    const planSnapshot = pendingPlan;
    setPendingPlan(projectId, null);
    approvePlanMutation.mutate(
      { conversationId, approved: false, feedback },
      {
        onError: (error) => {
          setPendingPlan(projectId, planSnapshot);
          toast.error(getErrorMessage(error));
        },
      },
    );
  };

  const handleSelectConversation = async (selectedId: string) => {
    if (selectedId === conversationId) return;
    setLoadingHistory(true);
    try {
      const detail = await aiService.getConversation(projectId, selectedId);
      const converted: AiChatMessage[] = detail.messages
        .filter((m) => m.role === "user" || m.role === "assistant")
        .map((m) => ({
          id: m.id,
          role: m.role as "user" | "assistant",
          content: m.content,
          createdAt: new Date(m.created_at).getTime(),
        }));
      loadConversationMessages(projectId, selectedId, converted);
      setConversationStatus(projectId, detail.status);
    } catch (error) {
      toast.error(getErrorMessage(error));
    } finally {
      setLoadingHistory(false);
    }
  };

  const sendMessage = async () => {
    const trimmed = chatInput.trim();
    if (!trimmed || inputBlocked) return;

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

    const toolMessageIds = new Map<string, string>();

    let hadChunk = false;
    let hadToolOrUiEvent = false;
    let streamErrorMessage: string | null = null;
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
          history: messages
            .filter((m) => m.role === "user" || m.role === "assistant")
            .filter((m) => !m.toolName)
            .slice(-8)
            .map((message) => ({ role: message.role, content: message.content })),
        },
        (event) => {
          if (event.type === "start" && event.conversation_id) {
            setConversationId(projectId, event.conversation_id);
          }
          if (event.type === "chunk") {
            hadChunk = true;
            appendToMessage(projectId, assistantMessageId, event.content);
          }
          if (event.type === "reasoning") {
            setThinking(projectId, true);
            appendReasoningText(projectId, event.content);
          }
          if (event.type === "plan") {
            setPendingPlan(projectId, event.steps);
            setConversationStatus(projectId, "awaiting_plan_approval");
          }
          if (event.type === "plan_approved") {
            setPendingPlan(projectId, null);
            setConversationStatus(projectId, "executing");
          }
          if (event.type === "tool_call") {
            hadToolOrUiEvent = true;
            const toolMsgId = crypto.randomUUID();
            toolMessageIds.set(event.tool_use_id, toolMsgId);
            appendMessage(projectId, {
              id: toolMsgId,
              role: "assistant",
              content: "",
              createdAt: Date.now(),
              toolName: event.tool_name,
              toolStatus: "running",
            });
          }
          if (event.type === "tool_result") {
            hadToolOrUiEvent = true;
            const toolMsgId = toolMessageIds.get(event.tool_use_id);
            if (toolMsgId) {
              updateToolStatus(projectId, toolMsgId, "done");
              setToolResult(projectId, toolMsgId, event.content);
            }
            const writeTool = [
              "create_task", "update_task", "delete_task",
              "bulk_create_tasks", "indent_task", "outdent_task",
              "reorder_task", "calculate_schedule",
            ];
            if (event.tool_name && writeTool.includes(event.tool_name)) {
              queryClient.invalidateQueries({ queryKey: taskKeys.list(projectId) });
            }
          }
          if (event.type === "approval_required") {
            hadToolOrUiEvent = true;
            setPendingApproval(projectId, {
              approval_id: event.approval_id,
              tool_name: event.tool_name,
              tool_input: event.tool_input,
            });
            const toolMsgId = toolMessageIds.get(event.tool_use_id) ?? crypto.randomUUID();
            appendMessage(projectId, {
              id: toolMsgId,
              role: "assistant",
              content: "",
              createdAt: Date.now(),
              toolName: event.tool_name,
              toolStatus: "running",
            });
          }
          if (event.type === "ui_action") {
            hadToolOrUiEvent = true;
            handleUiAction(event.action, event.tool_input ?? {});
          }
          if (event.type === "done") {
            setThinking(projectId, false);
            clearReasoningText(projectId);
            setConversationStatus(projectId, "idle");
          }
          if (event.type === "error") {
            streamErrorMessage = event.error || "AI chat failed";
            toast.error(streamErrorMessage);
            setThinking(projectId, false);
            setConversationStatus(projectId, "idle");
          }
        },
      );
    } catch (error) {
      replaceMessageContent(projectId, assistantMessageId, "Unable to generate a response.");
      toast.error(getErrorMessage(error));
    } finally {
      try {
        const activeApproval = useAiPanelStore.getState().projects[projectId]?.pendingApproval;
        if (activeApproval) {
          void aiService
            .resolveApproval(projectId, activeApproval.approval_id, false)
            .catch(() => {});
        }
      } catch {
        // ignore
      }
      setPendingApproval(projectId, null);
      setPendingPlan(projectId, null);
      setThinking(projectId, false);
      if (streamErrorMessage && !hadChunk) {
        replaceMessageContent(projectId, assistantMessageId, streamErrorMessage);
      } else if (!hadChunk && hadToolOrUiEvent) {
        replaceMessageContent(
          projectId,
          assistantMessageId,
          "Action processed. See tool activity below.",
        );
      } else if (!hadChunk && !hadToolOrUiEvent) {
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
        ui_context: { current_view: currentView, selected_task_ids: selectedTaskIds },
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
        data: { duration: Math.max(0, Math.round(estimate.recommended_minutes)) },
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
        if (!taskId || priority === null) throw new Error("Invalid SET_PRIORITY suggestion payload");
        await updateTaskMutation.mutateAsync({ taskId, data: { priority } });
      } else if (action.type === "UPDATE_TASK") {
        const taskId = readString(action.payload, "task_id");
        if (!taskId) throw new Error("Invalid UPDATE_TASK suggestion payload");
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
      {pendingApproval ? (
        <ApprovalDialog
          approval={pendingApproval}
          onApprove={() => void handleApproval(true)}
          onDeny={() => void handleApproval(false)}
        />
      ) : null}

      {/* Header */}
      <div className="shrink-0 border-b">
        <div className="flex items-center justify-between px-3 py-2">
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

        {/* Conversation selector */}
        {conversations && conversations.length > 0 ? (
          <div className="px-3 pb-2">
            <Select
              value={conversationId ?? ""}
              onValueChange={(id) => void handleSelectConversation(id)}
              disabled={isStreaming || loadingHistory}
            >
              <SelectTrigger className="h-7 text-[11px]">
                <SelectValue placeholder="Resume a past conversation..." />
              </SelectTrigger>
              <SelectContent>
                {conversations.map((c) => (
                  <SelectItem key={c.id} value={c.id} className="text-xs">
                    {c.title ?? "Untitled"}{" "}
                    <span className="text-muted-foreground">({c.status})</span>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        ) : null}

        {/* Status banner */}
        {conversationStatus === "interrupted" ? (
          <div className="border-t bg-amber-50 px-3 py-1.5 text-[11px] text-amber-700 dark:bg-amber-950/30 dark:text-amber-400">
            Conversation interrupted — resume or start a new one.
          </div>
        ) : conversationStatus === "awaiting_plan_approval" ? (
          <div className="border-t bg-blue-50 px-3 py-1.5 text-[11px] text-blue-700 dark:bg-blue-950/30 dark:text-blue-400">
            Waiting for plan approval.
          </div>
        ) : null}
      </div>

      <Tabs
        className="flex min-h-0 flex-1 flex-col"
        value={activeTab}
        onValueChange={(value) => setActiveTab(projectId, value as AiTab)}
      >
        <div className="shrink-0 border-b px-2 py-2">
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
                messages.map((message) =>
                  message.toolName ? (
                    <ToolCallRow
                      key={message.id}
                      toolName={message.toolName}
                      status={message.toolStatus ?? "running"}
                      result={message.toolResult}
                    />
                  ) : (
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
                  ),
                )
              )}

              {/* Live reasoning bubble */}
              {(isThinking || reasoningText) ? (
                <ReasoningStep text={reasoningText} isStreaming={isThinking} />
              ) : null}
            </div>
          </ScrollArea>

          {/* Plan approval card */}
          {pendingPlan ? (
            <PlanApprovalCard
              steps={pendingPlan}
              onApprove={handlePlanApprove}
              onRedirect={handlePlanRedirect}
              disabled={approvePlanMutation.isPending}
            />
          ) : null}

          <div className="shrink-0 border-t p-3">
            {aiPreferencesQuery.isError || updateAiPreferencesMutation.isError ? (
              <Alert variant="destructive" className="mb-3">
                <AlertDescription>
                  {getErrorMessage(
                    aiPreferencesQuery.error ?? updateAiPreferencesMutation.error,
                  )}
                </AlertDescription>
              </Alert>
            ) : null}
            <div className="mb-3 grid grid-cols-2 gap-2">
              <Select
                value={selectedProvider}
                onValueChange={(providerId) => {
                  const provider = aiProviders.find((item) => item.provider_id === providerId);
                  const recommendedModel =
                    provider?.models.find((item) => item.recommended)?.model_id ??
                    provider?.models[0]?.model_id ??
                    null;
                  applyAiPreferencePatch({ provider: providerId, model: recommendedModel });
                }}
                disabled={aiPreferencesQuery.isLoading || updateAiPreferencesMutation.isPending}
              >
                <SelectTrigger className="h-8 text-xs">
                  <SelectValue placeholder="Provider" />
                </SelectTrigger>
                <SelectContent>
                  {aiProviders.map((provider) => (
                    <SelectItem
                      key={provider.provider_id}
                      value={provider.provider_id}
                      disabled={!provider.available}
                    >
                      {provider.display_name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>

              <Select
                value={selectedModel}
                onValueChange={(modelId) => {
                  applyAiPreferencePatch({ model: modelId });
                }}
                disabled={
                  aiPreferencesQuery.isLoading ||
                  updateAiPreferencesMutation.isPending ||
                  modelSelectDisabled
                }
              >
                <SelectTrigger className="h-8 text-xs">
                  <SelectValue placeholder="Model" />
                </SelectTrigger>
                <SelectContent>
                  {providerModels.map((model) => (
                    <SelectItem key={model.model_id} value={model.model_id}>
                      {model.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
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
              disabled={inputBlocked}
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
                disabled={inputBlocked || !chatInput.trim()}
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
                    <div
                      key={`${estimate.task_id ?? estimate.task_name}`}
                      className="rounded-md border p-2.5"
                    >
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
                      <Badge
                        variant="outline"
                        className={suggestionToneClass(suggestion.severity)}
                      >
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
