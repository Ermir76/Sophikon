import { ArrowLeft, CheckCircle2, Mail, XCircle } from "lucide-react";
import { useEffect } from "react";
import { Link, useSearchParams } from "react-router";

import { useSendVerificationEmail } from "@/features/auth/hooks/useAuth";
import { useAuthStore } from "@/features/auth/store/auth-store";
import { getErrorMessage } from "@/shared/lib/errors";
import { Alert, AlertDescription } from "@/shared/ui/alert";
import { Button } from "@/shared/ui/button";

export default function VerifyEmailPage() {
  const [searchParams] = useSearchParams();
  const queryStatus = searchParams.get("status");
  const checkSession = useAuthStore((state) => state.checkSession);
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const resendMutation = useSendVerificationEmail();

  useEffect(() => {
    if (queryStatus === "success") {
      checkSession();
    }
  }, [queryStatus, checkSession]);

  const resendErrorAlert = resendMutation.isError ? (
    <Alert variant="destructive">
      <AlertDescription>{getErrorMessage(resendMutation.error)}</AlertDescription>
    </Alert>
  ) : null;

  const resendActions = (
    <div className="flex flex-col gap-3">
      <Button
        onClick={() => resendMutation.mutate()}
        disabled={resendMutation.isPending || resendMutation.isSuccess}
      >
        <Mail className="mr-2 h-4 w-4" />
        {resendMutation.isSuccess ? "Email Sent!" : "Resend Verification Email"}
      </Button>
      {resendErrorAlert}
      <Button asChild variant="outline">
        <Link to="/">
          <ArrowLeft className="mr-2 h-4 w-4" />
          Go to Dashboard
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
        {isAuthenticated ? resendActions : (
          <Button asChild>
            <Link to="/login">Go to Login</Link>
          </Button>
        )}
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
      {isAuthenticated ? resendActions : (
        <Button asChild>
          <Link to="/login">Go to Login</Link>
        </Button>
      )}
    </div>
  );
}
