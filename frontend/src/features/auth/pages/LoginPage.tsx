import { useEffect, useState } from "react";
import { zodResolver } from "@hookform/resolvers/zod";
import { Eye, EyeOff, Loader2 } from "lucide-react";
import { useForm } from "react-hook-form";
import { Link, useSearchParams } from "react-router";
import { z } from "zod";

import { authService } from "@/features/auth/api/auth.service";
import { useLogin } from "@/features/auth/hooks/useAuth";
import {
  consumeBlockedUnverifiedEmail,
  consumeDeactivatedAccountNotice,
} from "@/shared/api/api";
import { getErrorMessage } from "@/shared/lib/errors";
import { Alert, AlertDescription } from "@/shared/ui/alert";
import { Button } from "@/shared/ui/button";
import { Checkbox } from "@/shared/ui/checkbox";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/shared/ui/form";
import { Input } from "@/shared/ui/input";
import { Label } from "@/shared/ui/label";

const loginSchema = z.object({
  email: z.email("Please enter a valid email address."),
  password: z.string().min(1, "Password is required."),
  remember_me: z.boolean(),
});

type LoginFormValues = z.infer<typeof loginSchema>;

function getErrorCode(error: unknown): string | null {
  if (
    typeof error === "object" &&
    error !== null &&
    "response" in error &&
    typeof error.response === "object" &&
    error.response !== null &&
    "data" in error.response &&
    typeof error.response.data === "object" &&
    error.response.data !== null &&
    "error" in error.response.data &&
    typeof error.response.data.error === "object" &&
    error.response.data.error !== null &&
    "code" in error.response.data.error
  ) {
    return String(error.response.data.error.code);
  }
  return null;
}

export default function LoginPage() {
  const [showPassword, setShowPassword] = useState(false);
  const [blockedEmail, setBlockedEmail] = useState<string | null>(null);
  const [isDeactivatedAccount, setIsDeactivatedAccount] = useState(false);
  const [resendState, setResendState] = useState<{
    pending: boolean;
    success: boolean;
    error: string | null;
  }>({
    pending: false,
    success: false,
    error: null,
  });
  const [searchParams] = useSearchParams();
  const next = searchParams.get("next");
  const oauthStatus = searchParams.get("oauth");
  const loginMutation = useLogin(next);
  const registerHref = next ? `/register?next=${encodeURIComponent(next)}` : "/register";
  const forgotHref = next ? `/forgot-password?next=${encodeURIComponent(next)}` : "/forgot-password";

  const form = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: { email: "", password: "", remember_me: false },
  });
  const watchedEmail = form.watch("email");
  const loginErrorCode = getErrorCode(loginMutation.error);
  const requiresVerification = Boolean(blockedEmail) || loginErrorCode === "EMAIL_VERIFICATION_REQUIRED";
  const requiresDeactivatedAccountNotice =
    isDeactivatedAccount || loginErrorCode === "ACCOUNT_DEACTIVATED";
  const recoveryEmail =
    blockedEmail ?? (loginErrorCode === "EMAIL_VERIFICATION_REQUIRED" ? watchedEmail : "");

  useEffect(() => {
    if (consumeDeactivatedAccountNotice()) {
      setIsDeactivatedAccount(true);
    }

    const email = consumeBlockedUnverifiedEmail();
    if (!email) {
      return;
    }
    setBlockedEmail(email);
    form.setValue("email", email, {
      shouldDirty: false,
      shouldTouch: false,
      shouldValidate: false,
    });
  }, [form]);

  async function handleResendVerification() {
    if (!recoveryEmail) {
      setResendState({
        pending: false,
        success: false,
        error: "Enter your email address first.",
      });
      return;
    }

    setResendState({ pending: true, success: false, error: null });
    try {
      await authService.resendVerificationEmail({ email: recoveryEmail });
      setResendState({ pending: false, success: true, error: null });
    } catch (error) {
      setResendState({
        pending: false,
        success: false,
        error: getErrorMessage(error),
      });
    }
  }

  return (
    <div>
      <div className="mb-8">
        <h2 className="mb-2 text-3xl font-semibold">Welcome Back</h2>
        <p className="text-sm text-muted-foreground">
          Please enter your details to sign in.
        </p>
      </div>

      {loginMutation.isError && !requiresVerification && !requiresDeactivatedAccountNotice && (
        <Alert variant="destructive" className="mb-5">
          <AlertDescription>{getErrorMessage(loginMutation.error)}</AlertDescription>
        </Alert>
      )}

      {requiresDeactivatedAccountNotice && (
        <Alert variant="destructive" className="mb-5">
          <AlertDescription className="space-y-3">
            <p>Your account has been deactivated.</p>
            <p className="text-sm">
              Contact support or your administrator if you think this is a mistake.
            </p>
          </AlertDescription>
        </Alert>
      )}

      {requiresVerification && (
        <Alert className="mb-5">
          <AlertDescription className="space-y-3">
            <p>
              Your email verification window expired. Request a new verification email
              to continue.
            </p>
            <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
              <Button
                type="button"
                variant="outline"
                disabled={resendState.pending || resendState.success || !recoveryEmail}
                onClick={() => void handleResendVerification()}
              >
                {resendState.pending ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Sending...
                  </>
                ) : resendState.success ? (
                  "Verification Email Sent"
                ) : (
                  "Resend Verification Email"
                )}
              </Button>
              <Button asChild type="button" variant="ghost">
                <Link to="/verify-email?status=error">Open verification help</Link>
              </Button>
            </div>
            {resendState.error ? <p className="text-sm">{resendState.error}</p> : null}
            {resendState.success ? (
              <p className="text-sm">
                Check your inbox for the newest verification link. Older links may no
                longer work.
              </p>
            ) : null}
          </AlertDescription>
        </Alert>
      )}

      {oauthStatus === "error" && (
        <Alert variant="destructive" className="mb-5">
          <AlertDescription>
            Google login failed. Please try again or use email and password.
          </AlertDescription>
        </Alert>
      )}

      <Form {...form}>
        <form
          onSubmit={form.handleSubmit((data) => {
            setBlockedEmail(null);
            setIsDeactivatedAccount(false);
            setResendState({ pending: false, success: false, error: null });
            loginMutation.mutate(data);
          })}
          className="space-y-5"
        >
          <FormField
            control={form.control}
            name="email"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Email Address</FormLabel>
                <FormControl>
                  <Input
                    placeholder="name@company.com"
                    autoComplete="username"
                    {...field}
                  />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          <FormField
            control={form.control}
            name="password"
            render={({ field }) => (
              <FormItem>
                <div className="mb-1.5 flex items-center justify-between">
                  <FormLabel>Password</FormLabel>
                  <Link to={forgotHref} className="text-sm underline">
                    Forgot password?
                  </Link>
                </div>
                <FormControl>
                  <div className="relative">
                    <Input
                      type={showPassword ? "text" : "password"}
                      placeholder="********"
                      autoComplete="current-password"
                      {...field}
                    />
                    <button
                      type="button"
                      className="absolute right-3 top-1/2 -translate-y-1/2"
                      onClick={() => setShowPassword((v) => !v)}
                    >
                      {showPassword ? <EyeOff className="size-4" /> : <Eye className="size-4" />}
                    </button>
                  </div>
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          <FormField
            control={form.control}
            name="remember_me"
            render={({ field }) => (
              <FormItem className="flex items-center gap-2 space-y-0">
                <FormControl>
                  <Checkbox
                    id="remember"
                    checked={field.value}
                    onCheckedChange={field.onChange}
                  />
                </FormControl>
                <Label htmlFor="remember" className="text-sm font-normal">
                  Keep me logged in
                </Label>
              </FormItem>
            )}
          />

          <Button type="submit" className="w-full" disabled={loginMutation.isPending}>
            {loginMutation.isPending ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Signing in...
              </>
            ) : (
              "Sign In"
            )}
          </Button>
        </form>
      </Form>

      <div className="relative my-7">
        <div className="absolute inset-0 flex items-center">
          <div className="w-full border-t" />
        </div>
        <div className="relative flex justify-center text-xs">
          <span className="bg-background px-4 text-muted-foreground">Or continue with</span>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3">
        <Button
          variant="outline"
          type="button"
          onClick={() => authService.startGoogleOAuth(next)}
        >
          <svg
            className="mr-2 h-4 w-4"
            viewBox="0 0 24 24"
            xmlns="http://www.w3.org/2000/svg"
          >
            <path
              d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
              fill="#4285F4"
            />
            <path
              d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
              fill="#34A853"
            />
            <path
              d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l3.66-2.84z"
              fill="#FBBC05"
            />
            <path
              d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
              fill="#EA4335"
            />
          </svg>
          Google
        </Button>
        <Button variant="outline" type="button" disabled>
          <svg
            className="mr-2 h-4 w-4"
            viewBox="0 0 24 24"
            fill="currentColor"
            xmlns="http://www.w3.org/2000/svg"
          >
            <path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z" />
          </svg>
          GitHub (Soon)
        </Button>
      </div>

      <p className="mt-7 text-center text-sm text-muted-foreground">
        Don&apos;t have an account?{" "}
        <Link to={registerHref} className="underline">
          Sign up
        </Link>
      </p>
    </div>
  );
}
