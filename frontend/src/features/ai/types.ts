export type AiTab = "chat" | "estimate" | "suggestions";

export interface UiContext {
  current_view: string;
  selected_task_id?: string | null;
  selected_task_ids?: string[];
}

export type AiMessageRole = "user" | "assistant" | "system";

export type ToolCallStatus = "running" | "done" | "error" | "denied";

export interface AiChatMessage {
  id: string;
  role: AiMessageRole;
  content: string;
  createdAt: number;
  toolName?: string;
  toolStatus?: ToolCallStatus;
  toolResult?: string;
}

export interface ConversationSummary {
  id: string;
  title: string | null;
  status: string;
  mode: string;
  created_at: string;
  updated_at: string;
}

export interface ConversationDetail {
  id: string;
  title: string | null;
  status: string;
  mode: string;
  messages: Array<{
    id: string;
    role: string;
    content: string;
    created_at: string;
  }>;
}

export interface AiChatRequest {
  message: string;
  conversation_id?: string | null;
  ui_context?: UiContext;
  history?: Array<{
    role: AiMessageRole;
    content: string;
  }>;
}

export interface AiUsageMeta {
  tokens_in: number;
  tokens_out: number;
  model?: string | null;
}

export type AiChatEvent =
  | {
      type: "start";
      conversation_id?: string;
      model?: string;
    }
  | {
      type: "chunk";
      content: string;
    }
  | {
      type: "done";
      message_id?: string;
      usage?: AiUsageMeta;
      model?: string;
    }
  | {
      type: "error";
      error: string;
    }
  | {
      type: "tool_call";
      tool_use_id: string;
      tool_name: string;
      tool_input?: Record<string, unknown>;
    }
  | {
      type: "tool_result";
      tool_use_id: string;
      tool_name: string;
      content: string;
    }
  | {
      type: "approval_required";
      approval_id: string;
      tool_use_id: string;
      tool_name: string;
      tool_input?: Record<string, unknown>;
    }
  | {
      type: "ui_action";
      action: string;
      tool_input?: Record<string, unknown>;
    }
  | {
      type: "plan";
      steps: Array<{ action: string; reason: string }>;
    }
  | {
      type: "plan_approved";
    }
  | {
      type: "reasoning";
      content: string;
    };

export interface PendingApproval {
  approval_id: string;
  tool_name: string;
  tool_input?: Record<string, unknown>;
}

export interface AiPreferences {
  auto_approve: Record<string, boolean>;
}

export interface AiEstimateRequest {
  task_ids?: string[];
  task_name?: string;
  task_description?: string;
  include_reasoning?: boolean;
  ui_context?: UiContext;
}

export interface AiEstimateItem {
  task_id?: string | null;
  task_name: string;
  optimistic_minutes: number;
  likely_minutes: number;
  pessimistic_minutes: number;
  recommended_minutes: number;
  confidence: number;
  reasoning?: string | null;
}

export interface AiEstimateResponse {
  estimates: AiEstimateItem[];
  usage: AiUsageMeta;
}

export type AiSuggestionActionType =
  | "NONE"
  | "UPDATE_TASK"
  | "ADD_DEPENDENCY"
  | "SET_PRIORITY";

export interface AiSuggestionAction {
  type: AiSuggestionActionType;
  payload: Record<string, unknown>;
}

export interface AiSuggestion {
  id: string;
  type: string;
  severity: "LOW" | "MEDIUM" | "HIGH";
  title: string;
  description: string;
  affected_task_id?: string | null;
  suggested_action?: AiSuggestionAction | null;
}

export interface AiSuggestionsResponse {
  suggestions: AiSuggestion[];
  usage: AiUsageMeta;
}
