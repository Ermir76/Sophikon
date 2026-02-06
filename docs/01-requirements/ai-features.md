# Sophikon V1.0 - AI Features Specification

**Version:** 1.0
**Date:** 2026-02-06
**Status:** Aligned with database-schema.md v1.0

---

## Document References

| Document                   | Relationship                                     |
| -------------------------- | ------------------------------------------------ |
| database-schema.md         | AI tables: ai_conversation, ai_message, ai_usage |
| api-specification.md       | AI endpoints: /api/v1/ai/\*                      |
| user-stories.md            | Epic 5: AI Assistant user stories                |
| functional-requirements.md | FR-AI-\* requirements                            |

---

## 1. Overview

This document defines AI-powered features across all versions:

| Version  | AI Features                                                          |
| -------- | -------------------------------------------------------------------- |
| **V1.0** | Chat Assistant, Task Estimation, Basic Suggestions                   |
| **V1.1** | Resource Optimization suggestions                                    |
| **V1.2** | Project Planner, Risk Detector, Schedule Optimizer, Report Generator |

---

## 2. AI Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend (React)                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐ │
│  │ AI Chat     │  │ AI Suggest  │  │ Estimation UI           │ │
│  │ Panel       │  │ Toasts      │  │                         │ │
│  └──────┬──────┘  └──────┬──────┘  └───────────┬─────────────┘ │
└─────────┼────────────────┼─────────────────────┼───────────────┘
          │                │                     │
          ▼                ▼                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Backend (FastAPI)                           │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    /api/v1/ai/                           │   │
│  │  POST /chat          - Chat with project                 │   │
│  │  POST /estimate      - Estimate task duration            │   │
│  │  GET  /suggestions   - Get contextual suggestions        │   │
│  │  POST /plan          - Generate project plan (V1.2)      │   │
│  │  GET  /risks         - Detect risks (V1.2)               │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              │                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                  AI Service Layer                        │   │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────┐│   │
│  │  │ ChatService │ │ Estimator   │ │ PromptManager       ││   │
│  │  └─────────────┘ └─────────────┘ └─────────────────────┘│   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      LLM Provider Layer                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ Claude API   │  │ OpenAI API   │  │ Local LLM (future)   │  │
│  │ (Primary)    │  │ (Fallback)   │  │ Ollama               │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```
---


## 3. V1.0 AI Features

### 3.1 AI Chat Assistant

**Priority:** Must Have
**Complexity:** Medium-High
 
#### Description

Natural language interface to query and interact with project data.

#### Capabilities

| Capability         | Example Query                     | Response Type         |
| ------------------ | --------------------------------- | --------------------- |
| Task queries       | "Show overdue tasks"              | Task list             |
| Status queries     | "What's the project progress?"    | Summary text          |
| Date queries       | "When does the API phase finish?" | Date + context        |
| Dependency queries | "What's blocking deployment?"     | Dependency chain      |
| Simple actions     | "Mark login task as 50% complete" | Confirmation + action |

#### Technical Implementation

```python
# Backend: app/ai/chat_service.py

class ChatService:
    def __init__(self, llm_provider: LLMProvider):
        self.llm = llm_provider
        self.prompt_manager = PromptManager()

    async def chat(
        self,
        message: str,
        project_id: UUID,
        user_id: UUID,
        conversation_history: list[Message]
    ) -> AsyncGenerator[str, None]:
        """
        Stream chat response.

        1. Load project context (tasks, deps, summary)
        2. Classify intent (query vs action)
        3. Build prompt with context
        4. Stream LLM response
        5. If action, return structured action for confirmation
        """

        # Get project context
        context = await self._build_project_context(project_id)

        # Build prompt
        prompt = self.prompt_manager.build_chat_prompt(
            message=message,
            context=context,
            history=conversation_history
        )

        # Stream response
        async for chunk in self.llm.stream(prompt):
            yield chunk

    async def _build_project_context(self, project_id: UUID) -> ProjectContext:
        """Build context with project data for LLM."""
        return ProjectContext(
            project=await self.project_repo.get(project_id),
            tasks=await self.task_repo.get_all(project_id),
            dependencies=await self.dependency_repo.get_all(project_id),
            summary=await self._calculate_summary(project_id)
        )
```

```typescript
// Frontend: src/components/ai/ChatPanel.tsx

export function ChatPanel({ projectId }: { projectId: string }) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);

  const sendMessage = async () => {
    const userMessage = { role: 'user', content: input };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsStreaming(true);

    // Stream response
    const response = await fetch('/api/v1/ai/chat', {
      method: 'POST',
      body: JSON.stringify({
        message: input,
        project_id: projectId,
        history: messages
      }),
    });

    const reader = response.body?.getReader();
    let assistantMessage = '';

    while (true) {
      const { done, value } = await reader!.read();
      if (done) break;

      const chunk = new TextDecoder().decode(value);
      assistantMessage += chunk;

      setMessages(prev => [
        ...prev.slice(0, -1),
        { role: 'assistant', content: assistantMessage }
      ]);
    }

    setIsStreaming(false);
  };

  return (
    <div className="chat-panel">
      <MessageList messages={messages} />
      <ChatInput
        value={input}
        onChange={setInput}
        onSend={sendMessage}
        disabled={isStreaming}
      />
    </div>
  );
}
```

#### Prompt Template

```markdown
# Project Assistant

You are an AI assistant for the project management tool. Answer questions about the project based on the context provided.

## Project Context

- Name: {{project.name}}
- Status: {{project.status}}
- Start: {{project.start_date}}
- Progress: {{summary.percent_complete}}%
- Tasks: {{summary.total_tasks}} total, {{summary.completed_tasks}} completed, {{summary.overdue_tasks}} overdue

## Tasks

{{#each tasks}}

- [{{status_icon}}] {{name}} ({{start_date}} - {{finish_date}}) {{percent_complete}}%
  {{/each}}

## User Question

{{message}}

## Instructions

- Answer concisely and helpfully
- Reference specific tasks by name when relevant
- If asked to make changes, describe what would change and ask for confirmation
- Format dates as human-readable
- Use markdown for formatting
```

---

### 3.2 AI Task Estimation

**Priority:** Must Have
**Complexity:** Medium

#### Description

Suggest realistic task durations based on task name and description.

#### Features

- Estimate single task
- Bulk estimate multiple tasks
- Provide reasoning
- Show confidence level
- PERT estimates (optimistic, likely, pessimistic)

#### API Endpoint

```python
# POST /api/v1/ai/estimate

class EstimationRequest(BaseModel):
    task_ids: list[UUID]  # Tasks to estimate (or empty for new task)
    task_name: str | None = None  # For new task
    task_description: str | None = None
    project_id: UUID

class TaskEstimate(BaseModel):
    task_id: UUID | None
    task_name: str
    optimistic_days: float
    likely_days: float
    pessimistic_days: float
    confidence: float  # 0-1
    reasoning: str

class EstimationResponse(BaseModel):
    estimates: list[TaskEstimate]
```

#### Implementation

```python
class EstimationService:
    async def estimate_tasks(
        self,
        request: EstimationRequest
    ) -> EstimationResponse:
        """
        Estimate task durations using LLM.
        """
        tasks_to_estimate = []

        if request.task_ids:
            tasks_to_estimate = await self.task_repo.get_many(request.task_ids)
        elif request.task_name:
            tasks_to_estimate = [Task(name=request.task_name, description=request.task_description)]

        # Get project context for better estimates
        project = await self.project_repo.get(request.project_id)
        existing_tasks = await self.task_repo.get_all(request.project_id)

        prompt = self.prompt_manager.build_estimation_prompt(
            tasks=tasks_to_estimate,
            project_context=project,
            existing_tasks=existing_tasks
        )

        response = await self.llm.complete(prompt, response_format="json")
        return EstimationResponse.model_validate_json(response)
```

#### UI Integration

```typescript
// In TaskDetailPanel or TaskRow

function EstimateButton({ task }: { task: Task }) {
  const { mutate: estimate, isLoading } = useEstimateTask();
  const [showResult, setShowResult] = useState(false);
  const [result, setResult] = useState<TaskEstimate | null>(null);

  const handleEstimate = async () => {
    const response = await estimate({ task_ids: [task.id] });
    setResult(response.estimates[0]);
    setShowResult(true);
  };

  return (
    <>
      <Button onClick={handleEstimate} disabled={isLoading}>
        {isLoading ? <Spinner /> : <WandIcon />}
        Estimate with AI
      </Button>

      {showResult && result && (
        <EstimateResultDialog
          estimate={result}
          onAccept={(days) => updateTask(task.id, { duration: days })}
          onClose={() => setShowResult(false)}
        />
      )}
    </>
  );
}
```

---

### 3.3 AI Smart Suggestions

**Priority:** Should Have
**Complexity:** Low-Medium

#### Description

Contextual suggestions that appear as non-intrusive toasts/cards.

#### Suggestion Types (V1.0)

| Type               | Trigger                                    | Suggestion                            |
| ------------------ | ------------------------------------------ | ------------------------------------- |
| Missing dependency | Task name contains "after X"               | "This task might depend on 'X'"       |
| Short duration     | Duration < 1 day for complex-sounding task | "Similar tasks usually take 3-5 days" |
| No progress        | Task in progress for 5+ days, 0% complete  | "Task hasn't been updated in 5 days"  |

#### Implementation

```python
class SuggestionService:
    async def get_suggestions(
        self,
        project_id: UUID,
        limit: int = 5
    ) -> list[Suggestion]:
        """
        Analyze project and return actionable suggestions.

        Uses rule-based checks + optional LLM for complex suggestions.
        """
        suggestions = []

        tasks = await self.task_repo.get_all(project_id)
        dependencies = await self.dependency_repo.get_all(project_id)

        # Rule-based suggestions (fast, no LLM cost)
        suggestions.extend(self._check_stale_tasks(tasks))
        suggestions.extend(self._check_missing_dependencies(tasks, dependencies))
        suggestions.extend(self._check_short_durations(tasks))

        # LLM-enhanced suggestions (optional, cached)
        if self.settings.ai_suggestions_enabled:
            suggestions.extend(await self._get_llm_suggestions(tasks))
        return sorted(suggestions, key=lambda s: s.priority)[:limit]
```
        
---

## 4. V1.1 AI Features (Future)

### 4.1 AI Project Planner

Generate complete project plan from natural language description.

**Input:**

```
"Build a mobile banking app with account management, fund transfers,
bill payments, and biometric authentication. Team of 4 developers,
2 QA, 1 designer. Target: 4 months."
```

**Output:**

- 50+ tasks organized in WBS
- Dependencies between tasks
- Duration estimates
- Phase milestones

---

### 4.2 AI Risk Detector

Continuous monitoring for project risks.

**Risk Categories:**

- Schedule risks (critical path issues, unrealistic deadlines)
- Dependency risks (long chains, blocking tasks)
- Progress risks (falling behind, velocity decline)

---

### 4.3 AI Schedule Optimizer

Suggest schedule optimizations to meet deadlines.

**Capabilities:**

- Identify parallelization opportunities
- Suggest task reordering
- Recommend resource reallocation (V2.2+)

---

### 4.4 AI Report Generator

Generate narrative status reports from project data.

**Output:**

- Executive summary
- Accomplishments this week
- Upcoming milestones
- Risks and blockers

---

## 5. Technical Requirements

### 5.1 LLM Provider Abstraction

```python
from abc import ABC, abstractmethod

class LLMProvider(ABC):
    @abstractmethod
    async def complete(self, prompt: str, **kwargs) -> str:
        """Get completion from LLM."""
        pass

    @abstractmethod
    async def stream(self, prompt: str, **kwargs) -> AsyncGenerator[str, None]:
        """Stream completion from LLM."""
        pass

class ClaudeProvider(LLMProvider):
    """Anthropic Claude - primary provider."""

    def __init__(self, api_key: str):
        self.client = anthropic.AsyncClient(api_key=api_key)
        self.model = "claude-sonnet-4-5-20250929"  # Latest Sonnet 4.5

    async def complete(self, prompt: str, **kwargs) -> str:
        response = await self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text

    async def stream(self, prompt: str, **kwargs) -> AsyncGenerator[str, None]:
        async with self.client.messages.stream(
            model=self.model,
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}]
        ) as stream:
            async for text in stream.text_stream:
                yield text

class OpenAIProvider(LLMProvider):
    """OpenAI - fallback provider."""
    pass
```

### 5.2 Prompt Management

```python
class PromptManager:
    """Manage prompt templates with versioning."""

    def __init__(self):
        self.templates = self._load_templates()

    def _load_templates(self) -> dict[str, str]:
        """Load templates from files."""
        templates = {}
        template_dir = Path("app/ai/prompts")
        for file in template_dir.glob("*.md"):
            templates[file.stem] = file.read_text()
        return templates

    def build_chat_prompt(
        self,
        message: str,
        context: ProjectContext,
        history: list[Message]
    ) -> str:
        template = self.templates["chat"]
        return template.format(
            project=context.project,
            tasks=context.tasks,
            summary=context.summary,
            history=self._format_history(history),
            message=message
        )
```

### 5.3 Cost Management

```python
class AIUsageTracker:
    """Track AI API usage for cost management."""

    async def track_usage(
        self,
        user_id: UUID,
        feature: str,
        tokens_in: int,
        tokens_out: int,
        model: str
    ):
        await self.repo.create(AIUsage(
            user_id=user_id,
            feature=feature,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            model=model,
            estimated_cost=self._calculate_cost(tokens_in, tokens_out, model),
            created_at=datetime.utcnow()
        ))

    async def get_user_usage(self, user_id: UUID, period: str = "month") -> UsageSummary:
        """Get user's AI usage for rate limiting / billing."""
        pass
```

### 5.4 Rate Limiting

```python
# Limits per user per day (V2.0)
AI_LIMITS = {
    "chat_messages": 100,
    "estimations": 50,
    "suggestions_refresh": 20,
}
```

---

## 6. FastAPI Features Demonstrated

| Feature              | Usage in AI Module                   |
| -------------------- | ------------------------------------ |
| Async/await          | All LLM calls are async              |
| Streaming Response   | Chat uses `StreamingResponse`        |
| Dependency Injection | `LLMProvider` injected into services |
| Background Tasks     | Cache warming, usage tracking        |
| Pydantic             | Request/response validation          |
| WebSocket            | Real-time suggestion updates         |

---

## 7. Success Metrics

| Metric               | V1.0 Target                  |
| -------------------- | ---------------------------- |
| Chat response start  | < 2 seconds                  |
| Estimation accuracy  | Within 30% of actual         |
| User adoption        | 50% of users try AI features |
| Suggestions accepted | 20% acceptance rate          |

---

## Document History

| Version | Date       | Author    | Changes                                          |
| ------- | ---------- | --------- | ------------------------------------------------ |
| 1.0     | 2026-02-05 | Ermir | Initial draft                                    |
| 2.0     | 2026-02-05 | Ermir | Scoped to versions, added implementation details |
| 3.0     | 2026-02-06 | Ermir | Aligned with schema v3.0, added doc references   |
