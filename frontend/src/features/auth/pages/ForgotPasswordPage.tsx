import { zodResolver } from "@hookform/resolvers/zod";
import { Loader2 } from "lucide-react";
import { useState } from "react";
import { Link, useSearchParams } from "react-router";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { useRequestPasswordReset } from "@/features/auth/hooks/useAuth";
import { getErrorMessage } from "@/shared/lib/errors";
import { Alert, AlertDescription } from "@/shared/ui/alert";
import { Button } from "@/shared/ui/button";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/shared/ui/form";
import { Input } from "@/shared/ui/input";

const forgotPasswordSchema = z.object({
  email: z.email("Please enter a valid email address."),
});

type ForgotPasswordFormValues = z.infer<typeof forgotPasswordSchema>;

export default function ForgotPasswordPage() {
  const [searchParams] = useSearchParams();
  const next = searchParams.get("next");
  const loginHref = next ? `/login?next=${encodeURIComponent(next)}` : "/login";
  const resetMutation = useRequestPasswordReset();
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const form = useForm<ForgotPasswordFormValues>({
    resolver: zodResolver(forgotPasswordSchema),
    defaultValues: { email: "" },
  });

  return (
    <div>
      <div className="mb-8">
        <h2 className="mb-2 text-3xl font-semibold">Reset Password</h2>
        <p className="text-sm text-muted-foreground">
          Enter your email and we&apos;ll send you reset instructions.
        </p>
      </div>

      {successMessage ? (
        <Alert className="mb-5">
          <AlertDescription>{successMessage}</AlertDescription>
        </Alert>
      ) : null}

      {resetMutation.isError ? (
        <Alert variant="destructive" className="mb-5">
          <AlertDescription>{getErrorMessage(resetMutation.error)}</AlertDescription>
        </Alert>
      ) : null}

      <Form {...form}>
        <form
          onSubmit={form.handleSubmit((data) => {
            resetMutation.mutate(data, {
              onSuccess: (response) => {
                setSuccessMessage(response.message);
              },
            });
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
                    autoComplete="email"
                    {...field}
                  />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          <Button type="submit" className="w-full" disabled={resetMutation.isPending}>
            {resetMutation.isPending ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Sending reset link...
              </>
            ) : (
              "Send Reset Link"
            )}
          </Button>
        </form>
      </Form>

      <p className="mt-7 text-center text-sm text-muted-foreground">
        Back to{" "}
        <Link to={loginHref} className="underline">
          Sign in
        </Link>
      </p>
    </div>
  );
}
