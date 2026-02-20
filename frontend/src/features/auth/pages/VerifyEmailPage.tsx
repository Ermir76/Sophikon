import { useEffect } from "react";
import { useSearchParams, Link } from "react-router";
import { Loader2, CheckCircle2, XCircle, ArrowLeft } from "lucide-react";

import { useVerifyEmail } from "@/features/auth/hooks/useAuth";
import { useAuthStore } from "@/features/auth/store/auth-store";

import { Button } from "@/shared/ui/button";

export default function VerifyEmailPage() {
    const [searchParams] = useSearchParams();
    const token = searchParams.get("token");

    const verifyMutation = useVerifyEmail();
    const checkSession = useAuthStore((state) => state.checkSession);

    useEffect(() => {
        if (token && !verifyMutation.isSuccess && !verifyMutation.isError) {
            verifyMutation.mutate(token, {
                onSuccess: () => {
                    // Refresh user data so email_verified updates in the store
                    checkSession();
                },
            });
        }
    }, [token]); // eslint-disable-line react-hooks/exhaustive-deps

    // No token in URL
    if (!token) {
        return (
            <div className="text-center">
                <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-destructive/10">
                    <XCircle className="h-6 w-6 text-destructive" />
                </div>
                <h2 className="text-2xl font-bold mb-2">Invalid Link</h2>
                <p className="text-muted-foreground text-sm mb-6">
                    This verification link is missing a token. Please check your email and try again.
                </p>
                <Button asChild variant="outline">
                    <Link to="/login">
                        <ArrowLeft className="mr-2 h-4 w-4" />
                        Back to Login
                    </Link>
                </Button>
            </div>
        );
    }

    // Loading
    if (verifyMutation.isPending) {
        return (
            <div className="text-center">
                <Loader2 className="mx-auto h-8 w-8 animate-spin text-primary mb-4" />
                <h2 className="text-2xl font-bold mb-2">Verifying your email...</h2>
                <p className="text-muted-foreground text-sm">
                    Please wait while we confirm your email address.
                </p>
            </div>
        );
    }

    // Success
    if (verifyMutation.isSuccess) {
        return (
            <div className="text-center">
                <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-primary/10">
                    <CheckCircle2 className="h-6 w-6 text-primary" />
                </div>
                <h2 className="text-2xl font-bold mb-2">Email Verified!</h2>
                <p className="text-muted-foreground text-sm mb-6">
                    Your email has been successfully verified. You can now access all features.
                </p>
                <Button asChild>
                    <Link to="/">Go to Dashboard</Link>
                </Button>
            </div>
        );
    }

    // Error
    return (
        <div className="text-center">
            <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-destructive/10">
                <XCircle className="h-6 w-6 text-destructive" />
            </div>
            <h2 className="text-2xl font-bold mb-2">Verification Failed</h2>
            <p className="text-muted-foreground text-sm mb-6">
                This link may have expired or already been used. Please request a new verification email.
            </p>
            <Button asChild variant="outline">
                <Link to="/login">
                    <ArrowLeft className="mr-2 h-4 w-4" />
                    Back to Login
                </Link>
            </Button>
        </div>
    );
}
