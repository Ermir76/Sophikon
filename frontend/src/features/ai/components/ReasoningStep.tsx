import { useState } from "react";
import { ChevronDown, ChevronRight, Loader2 } from "lucide-react";

import { cn } from "@/shared/lib/utils";

interface ReasoningStepProps {
  text: string;
  isStreaming: boolean;
}

export function ReasoningStep({ text, isStreaming }: ReasoningStepProps) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="mr-6 rounded-lg border border-dashed bg-muted px-2.5 py-2 text-xs">
      <button
        type="button"
        className="flex w-full items-center gap-1.5 text-muted-foreground"
        onClick={() => setExpanded((v) => !v)}
      >
        {isStreaming ? (
          <Loader2 className="size-3 animate-spin shrink-0" />
        ) : expanded ? (
          <ChevronDown className="size-3 shrink-0" />
        ) : (
          <ChevronRight className="size-3 shrink-0" />
        )}
        <span className="font-medium">{isStreaming ? "Thinking..." : "Reasoning"}</span>
      </button>

      {expanded && text ? (
        <p className={cn("mt-1.5 whitespace-pre-wrap leading-relaxed text-muted-foreground")}>
          {text}
        </p>
      ) : null}
    </div>
  );
}
