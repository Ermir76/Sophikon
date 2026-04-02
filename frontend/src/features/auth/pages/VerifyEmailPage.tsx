import { ArrowLeft, CheckCircle2, Mail, XCircle } from "lucide-react";
import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router";

import { useResendVerificationEmail } from "@/features/auth/hooks/useAuth";
import { useAuthStore } from "@/features/auth/store/auth-store";
import { getErrorMessage } from "@/shared/lib/errors";
import { Alert, AlertDescription } from "@/shared/ui/alert";
import { Button } from "@/shared/ui/button";
import { Input } from "@/shared/ui/input";
import { Label } from "@/shared/ui/label";

export default function VerifyEmailPage() {
  const [searchParams] = useSearchParams();
  const queryStatus = searchParams.get("status");
  const checkSession = useAuthStore((state) => state.checkSession);
  const user = useAuthStore((state) => state.user);
  const resendMutation = useResendVerificationEmail();
  const [email, setEmail] = useState(user?.email ?? "");

  useEffect(() => {
    if (queryStatus === "success") {
      checkSession();
    }
  }, [queryStatus, checkSession]);

  useEffect(() => {
    if (user?.email) {
      setEmail(user.email);
    }
  }, [user?.email]);

  const resendFeedback = resendMutation.isError ? (
    <Alert variant="destructive">
      <AlertDescription>{getErrorMessage(resendMutation.error)}</AlertDescription>
    </Alert>
  ) : resendMutation.isSuccess ? (
    <Alert>
      <AlertDescription>
        If that email exists, a verification email was sent. Use the newest link in your
        inbox.
      </AlertDescription>
    </Alert>
  ) : null;

  function handleResend() {
    if (!email) {
      return;
    }
    resendMutation.mutate({ email });
  }

  const resendActions = (
    <div className="flex flex-col gap-3">
      <div className="space-y-2 text-left">
        <Label htmlFor="verification-email">Email address</Label>
        <Input
          id="verification-email"
          type="email"
          value={email}
          onChange={(event) => {
            setEmail(event.target.value);
            resendMutation.reset();
          }}
          placeholder="name@example.com"
          autoComplete="email"
        />
      </div>
      <Button
        onClick={handleResend}
        disabled={resendMutation.isPending || resendMutation.isSuccess || !email}
      >
        <Mail className="mr-2 h-4 w-4" />
        {resendMutation.isPending ? "Sending..." : "Resend Verification Email"}
      </Button>
      {resendFeedback}
      <Button asChild variant="outline">
        <Link to="/login">
          <ArrowLeft className="mr-2 h-4 w-4" />
          Go to Login
        </Link>
      </Button>
    </div>
  );

  if (queryStatus === "success") {
    return (
      <div className="text-center">
        <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full border">
          <CheckCircle2 className="h-6 w-6" />
        </div>
        <h2 className="mb-2 text-2xl font-semibold">Email Verified!</h2>
        <p className="mb-6 text-sm text-muted-foreground">
          Your email has been successfully verified. You can now access all features.
        </p>
        <Button asChild>
          <Link to="/">Go to Dashboard</Link>
        </Button>
      </div>
    );
  }

  if (queryStatus === "error") {
    return (
      <div className="rounded-xl border p-6 text-center">
        <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full border">
          <XCircle className="h-6 w-6" />
        </div>
        <h2 className="mb-2 text-2xl font-semibold">Verification Failed</h2>
        <p className="mb-6 text-sm text-muted-foreground">
          This link may have expired or already been used. Please request a new
          verification email.
        </p>
        {resendActions}
      </div>
    );
  }

  return (
    <div className="rounded-xl border p-6 text-center">
      <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full border">
        <XCircle className="h-6 w-6" />
      </div>
      <h2 className="mb-2 text-2xl font-semibold">Invalid Link</h2>
      <p className="mb-6 text-sm text-muted-foreground">
        This verification link appears to be invalid. Please check your email and try
        again.
      </p>
      {resendActions}
    </div>
  );
}
