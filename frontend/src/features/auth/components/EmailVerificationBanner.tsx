import { useState } from "react";
import { Loader2, Mail, X } from "lucide-react";

import { useSendVerificationEmail } from "@/features/auth/hooks/useAuth";
import { useAuthStore } from "@/features/auth/store/auth-store";
import { getErrorMessage } from "@/shared/lib/errors";
import { Button } from "@/shared/ui/button";

export function EmailVerificationBanner() {
  const user = useAuthStore((state) => state.user);
  const [dismissed, setDismissed] = useState(false);
  const sendMutation = useSendVerificationEmail();

  if (!user || user.email_verified || dismissed) {
    return null;
  }

  return (
    <div className="flex items-center justify-between gap-3 px-4 py-2.5">
      <div className="flex items-center gap-2">
        <Mail className="h-4 w-4 shrink-0" />
        <span>
          Please verify your email address.
          {sendMutation.isSuccess && (
            <span className="ml-1 font-medium">Verification email sent!</span>
          )}
          {sendMutation.isError && (
            <span className="ml-1">{getErrorMessage(sendMutation.error)}</span>
          )}
        </span>
      </div>

      <div className="flex shrink-0 items-center gap-2">
        <Button
          variant="outline"
          size="sm"
          className="h-7"
          disabled={sendMutation.isPending || sendMutation.isSuccess}
          onClick={() => sendMutation.mutate()}
        >
          {sendMutation.isPending ? (
            <>
              <Loader2 className="mr-1.5 h-3 w-3 animate-spin" />
              Sending...
            </>
          ) : sendMutation.isSuccess ? (
            "Sent"
          ) : (
            "Resend Email"
          )}
        </Button>
        <Button
          variant="ghost"
          size="icon"
          className="h-7 w-7"
          onClick={() => setDismissed(true)}
          aria-label="Dismiss verification banner"
        >
          <X className="h-4 w-4" />
        </Button>
      </div>
    </div>
  );
}
