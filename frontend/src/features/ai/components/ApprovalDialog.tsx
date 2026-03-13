import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/shared/ui/alert-dialog";
import type { PendingApproval } from "@/features/ai/types";

const TOOL_DESCRIPTIONS: Record<string, string> = {
  delete_task: "Ta bort task",
  delete_dependency: "Ta bort beroende",
};

interface ApprovalDialogProps {
  approval: PendingApproval;
  onApprove: () => void;
  onDeny: () => void;
}

export function ApprovalDialog({ approval, onApprove, onDeny }: ApprovalDialogProps) {
  const action = TOOL_DESCRIPTIONS[approval.tool_name] ?? approval.tool_name;

  return (
    <AlertDialog open>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>AI vill utföra en åtgärd</AlertDialogTitle>
          <AlertDialogDescription className="space-y-2">
            <strong>{action}</strong> kräver ditt godkännande.
            {approval.tool_input ? (
              <pre className="mt-2 max-h-40 overflow-auto rounded bg-muted px-3 py-2 text-xs text-foreground">
                {JSON.stringify(approval.tool_input, null, 2)}
              </pre>
            ) : null}
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel onClick={onDeny}>Avvisa</AlertDialogCancel>
          <AlertDialogAction
            onClick={onApprove}
            className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
          >
            Godkänn
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}
