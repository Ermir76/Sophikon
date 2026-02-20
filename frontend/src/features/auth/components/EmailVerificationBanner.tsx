import { useState } from "react";
import { Mail, X, Loader2 } from "lucide-react";

import { useSendVerificationEmail } from "@/features/auth/hooks/useAuth";
import { useAuthStore } from "@/features/auth/store/auth-store";
import { getErrorMessage } from "@/shared/lib/errors";

import { Button } from "@/shared/ui/button";

export function EmailVerificationBanner() {
    const user = useAuthStore((state) => state.user);
    const [dismissed, setDismissed] = useState(false);
    const sendMutation = useSendVerificationEmail();

    // Don't show if user is verified, not logged in, or dismissed
    if (!user || user.email_verified || dismissed) {
        return null;
    }

    return (
        <div className="flex items-center justify-between gap-3 border-b border-border bg-primary/5 px-4 py-2.5 text-sm">
            <div className="flex items-center gap-2 text-foreground">
                <Mail className="h-4 w-4 shrink-0 text-primary" />
                <span>
                    Please verify your email address.
                    {sendMutation.isSuccess && (
                        <span className="ml-1 text-primary font-medium">Verification email sent!</span>
                    )}
                    {sendMutation.isError && (
                        <span className="ml-1 text-destructive">{getErrorMessage(sendMutation.error)}</span>
                    )}
                </span>
            </div>

            <div className="flex items-center gap-2 shrink-0">
                <Button
                    variant="outline"
                    size="sm"
                    className="h-7 text-xs"
                    disabled={sendMutation.isPending || sendMutation.isSuccess}
                    onClick={() => sendMutation.mutate()}
                >
                    {sendMutation.isPending ? (
                        <><Loader2 className="mr-1.5 h-3 w-3 animate-spin" />Sending...</>
                    ) : sendMutation.isSuccess ? (
                        "Sent ✓"
                    ) : (
                        "Resend Email"
                    )}
                </Button>
                <button
                    onClick={() => setDismissed(true)}
                    className="text-muted-foreground hover:text-foreground transition-colors"
                    aria-label="Dismiss verification banner"
                >
                    <X className="h-4 w-4" />
                </button>
            </div>
        </div>
    );
}
