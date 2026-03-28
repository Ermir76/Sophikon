import { useState } from "react";
import { CheckCircle2, CornerDownLeft } from "lucide-react";

import { Button } from "@/shared/ui/button";
import { Textarea } from "@/shared/ui/textarea";

interface PlanApprovalCardProps {
  steps: Array<{ action: string; reason: string }>;
  onApprove: () => void;
  onRedirect: (feedback: string) => void;
  disabled?: boolean;
}

export function PlanApprovalCard({ steps, onApprove, onRedirect, disabled }: PlanApprovalCardProps) {
  const [feedback, setFeedback] = useState("");
  const [showRedirect, setShowRedirect] = useState(false);

  const handleRedirect = () => {
    const trimmed = feedback.trim();
    if (!trimmed) return;
    onRedirect(trimmed);
    setFeedback("");
    setShowRedirect(false);
  };

  return (
    <div className="mx-3 mb-2 rounded-lg border bg-card p-3">
      <p className="mb-2 text-xs font-semibold text-foreground">Proposed plan</p>
      <ol className="mb-3 space-y-1.5">
        {steps.map((step, i) => (
          <li key={i} className="flex gap-2 text-xs">
            <span className="mt-0.5 shrink-0 text-[10px] font-medium text-muted-foreground">
              {i + 1}.
            </span>
            <div>
              <span className="font-medium">{step.action}</span>
              {step.reason ? (
                <span className="text-muted-foreground"> — {step.reason}</span>
              ) : null}
            </div>
          </li>
        ))}
      </ol>

      {showRedirect ? (
        <div className="space-y-2">
          <Textarea
            value={feedback}
            onChange={(e) => setFeedback(e.target.value)}
            placeholder="Tell the agent what to do differently..."
            className="min-h-[64px] resize-none text-xs"
            disabled={disabled}
            autoFocus
          />
          <div className="flex gap-2">
            <Button
              type="button"
              size="sm"
              className="h-7 flex-1 gap-1 text-xs"
              onClick={handleRedirect}
              disabled={disabled || !feedback.trim()}
            >
              <CornerDownLeft className="size-3" />
              Send feedback
            </Button>
            <Button
              type="button"
              variant="ghost"
              size="sm"
              className="h-7 text-xs"
              onClick={() => setShowRedirect(false)}
              disabled={disabled}
            >
              Cancel
            </Button>
          </div>
        </div>
      ) : (
        <div className="flex gap-2">
          <Button
            type="button"
            size="sm"
            className="h-7 flex-1 gap-1 text-xs"
            onClick={onApprove}
            disabled={disabled}
          >
            <CheckCircle2 className="size-3" />
            Approve
          </Button>
          <Button
            type="button"
            variant="outline"
            size="sm"
            className="h-7 flex-1 text-xs"
            onClick={() => setShowRedirect(true)}
            disabled={disabled}
          >
            Redirect
          </Button>
        </div>
      )}
    </div>
  );
}
