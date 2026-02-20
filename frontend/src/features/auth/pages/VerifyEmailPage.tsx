import { useSearchParams, Link } from "react-router";
import { CheckCircle2, XCircle, ArrowLeft } from "lucide-react";

import { useAuthStore } from "@/features/auth/store/auth-store";

import { Button } from "@/shared/ui/button";
import { useEffect } from "react";

export default function VerifyEmailPage() {
    const [searchParams] = useSearchParams();
    const queryStatus = searchParams.get("status"); // "success" | "error" | null
    const checkSession = useAuthStore((state) => state.checkSession);

    // When the backend redirects here with ?status=success,
    // refresh the session so email_verified updates in the store.
    useEffect(() => {
        if (queryStatus === "success") {
            checkSession();
        }
    }, [queryStatus, checkSession]);

    // Success — backend verified the email and redirected here
    if (queryStatus === "success") {
        return (
            <div className="text-center">
                <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-primary/10">
                    <CheckCircle2 className="h-6 w-6 text-primary" />
                </div>
                <h2 className="text-2xl font-bold mb-2">Email Verified!</h2>
                <p className="text-muted-foreground text-sm mb-6">
                    Your email has been successfully verified. You can now access all
                    features.
                </p>
                <Button asChild>
                    <Link to="/">Go to Dashboard</Link>
                </Button>
            </div>
        );
    }

    // Error — token invalid/expired/already used
    if (queryStatus === "error") {
        return (
            <div className="text-center rounded-xl border-2 border-destructive/50 bg-destructive/5 p-6 -m-2">
                <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-destructive/10">
                    <XCircle className="h-6 w-6 text-destructive" />
                </div>
                <h2 className="text-2xl font-bold mb-2">Verification Failed</h2>
                <p className="text-muted-foreground text-sm mb-6">
                    This link may have expired or already been used. Please request a new
                    verification email.
                </p>
                <Button asChild variant="outline">
                    <Link to="/">
                        <ArrowLeft className="mr-2 h-4 w-4" />
                        Go to Dashboard
                    </Link>
                </Button>
            </div>
        );
    }

    // No status param — user navigated here directly without a valid link
    return (
        <div className="text-center rounded-xl border-2 border-destructive/50 bg-destructive/5 p-6 -m-2">
            <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-destructive/10">
                <XCircle className="h-6 w-6 text-destructive" />
            </div>
            <h2 className="text-2xl font-bold mb-2">Invalid Link</h2>
            <p className="text-muted-foreground text-sm mb-6">
                This verification link appears to be invalid. Please check your email
                and try again.
            </p>
            <Button asChild variant="outline">
                <Link to="/">
                    <ArrowLeft className="mr-2 h-4 w-4" />
                    Go to Dashboard
                </Link>
            </Button>
        </div>
    );
}
