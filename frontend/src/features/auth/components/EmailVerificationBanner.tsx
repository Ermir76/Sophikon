import { useEffect, useState } from "react";
import { Loader2, Mail } from "lucide-react";

import { useResendVerificationEmail } from "@/features/auth/hooks/useAuth";
import { useAuthStore } from "@/features/auth/store/auth-store";
import { getErrorMessage } from "@/shared/lib/errors";
import { Button } from "@/shared/ui/button";

const VERIFICATION_BANNER_SNOOZE_KEY = "auth.verification-banner-snooze-until";
const VERIFICATION_BANNER_SNOOZE_MS = 2 * 60 * 60 * 1000;

function getSnoozeKey(userId: string): string {
  return `${VERIFICATION_BANNER_SNOOZE_KEY}.${userId}`;
}

function getInitialSnoozeUntil(snoozeKey: string | null): number | null {
  if (!snoozeKey) {
    return null;
  }

  const raw = window.localStorage.getItem(snoozeKey);
  if (!raw) {
    return null;
  }

  const snoozeUntil = Number(raw);
  if (Number.isNaN(snoozeUntil) || snoozeUntil <= Date.now()) {
    window.localStorage.removeItem(snoozeKey);
    return null;
  }
  return snoozeUntil;
}

export function EmailVerificationBanner() {
  const user = useAuthStore((state) => state.user);
  const snoozeKey = user ? getSnoozeKey(user.id) : null;
  const [snoozeUntil, setSnoozeUntil] = useState<number | null>(() =>
    getInitialSnoozeUntil(snoozeKey),
  );
  const sendMutation = useResendVerificationEmail();
  const isSnoozed = snoozeUntil !== null && snoozeUntil > Date.now();

  useEffect(() => {
    setSnoozeUntil(getInitialSnoozeUntil(snoozeKey));
  }, [snoozeKey]);

  useEffect(() => {
    if (!snoozeUntil || !snoozeKey) {
      return;
    }

    const timeoutMs = Math.max(snoozeUntil - Date.now(), 0);
    const timer = window.setTimeout(() => {
      window.localStorage.removeItem(snoozeKey);
      setSnoozeUntil(null);
    }, timeoutMs);

    return () => {
      window.clearTimeout(timer);
    };
  }, [snoozeKey, snoozeUntil]);

  if (!user || user.email_verified || isSnoozed) {
    return null;
  }

  const handleSnooze = () => {
    if (!snoozeKey) {
      return;
    }
    const nextSnoozeUntil = Date.now() + VERIFICATION_BANNER_SNOOZE_MS;
    window.localStorage.setItem(
      snoozeKey,
      String(nextSnoozeUntil),
    );
    setSnoozeUntil(nextSnoozeUntil);
  };

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
          onClick={() => sendMutation.mutate({ email: user.email })}
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
          size="sm"
          className="h-7"
          onClick={handleSnooze}
        >
          Remind me later
        </Button>
      </div>
    </div>
  );
}
