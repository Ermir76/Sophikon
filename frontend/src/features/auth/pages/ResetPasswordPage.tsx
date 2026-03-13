import { zodResolver } from "@hookform/resolvers/zod";
import { Loader2 } from "lucide-react";
import { useState } from "react";
import { Link } from "react-router";
import { useForm } from "react-hook-form";
import { useSearchParams } from "react-router";
import { z } from "zod";

import { useConfirmPasswordReset } from "@/features/auth/hooks/useAuth";
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

const resetPasswordSchema = z
  .object({
    new_password: z
      .string()
      .min(8, "Password must be at least 8 characters.")
      .regex(/[A-Z]/, "Password must contain at least one uppercase letter")
      .regex(/[0-9]/, "Password must contain at least one number")
      .regex(
        /[^a-zA-Z0-9]/,
        "Password must contain at least one special character",
      ),
    confirmPassword: z.string().min(8, "Password confirmation is required."),
  })
  .refine((data) => data.new_password === data.confirmPassword, {
    message: "Passwords do not match",
    path: ["confirmPassword"],
  });

type ResetPasswordFormValues = z.infer<typeof resetPasswordSchema>;

export default function ResetPasswordPage() {
  const [searchParams] = useSearchParams();
  const token = searchParams.get("token");
  const resetMutation = useConfirmPasswordReset();
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const form = useForm<ResetPasswordFormValues>({
    resolver: zodResolver(resetPasswordSchema),
    defaultValues: {
      new_password: "",
      confirmPassword: "",
    },
  });

  if (!token) {
    return (
      <div className="rounded-xl border p-6 text-center">
        <h2 className="mb-2 text-2xl font-semibold">Invalid Reset Link</h2>
        <p className="mb-6 text-sm text-muted-foreground">
          This reset link is missing a token. Please request a new one.
        </p>
        <Button asChild variant="outline">
          <Link to="/forgot-password">Request new reset link</Link>
        </Button>
      </div>
    );
  }

  return (
    <div>
      <div className="mb-8">
        <h2 className="mb-2 text-3xl font-semibold">Set New Password</h2>
        <p className="text-sm text-muted-foreground">
          Choose a strong password for your account.
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
            resetMutation.mutate(
              {
                token,
                new_password: data.new_password,
              },
              {
                onSuccess: (response) => {
                  setSuccessMessage(response.message);
                },
              },
            );
          })}
          className="space-y-5"
        >
          <FormField
            control={form.control}
            name="new_password"
            render={({ field }) => (
              <FormItem>
                <FormLabel>New Password</FormLabel>
                <FormControl>
                  <Input
                    type="password"
                    placeholder="********"
                    autoComplete="new-password"
                    {...field}
                  />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          <FormField
            control={form.control}
            name="confirmPassword"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Confirm Password</FormLabel>
                <FormControl>
                  <Input
                    type="password"
                    placeholder="********"
                    autoComplete="new-password"
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
                Resetting password...
              </>
            ) : (
              "Reset Password"
            )}
          </Button>
        </form>
      </Form>

      <p className="mt-7 text-center text-sm text-muted-foreground">
        Back to{" "}
        <Link to="/login" className="underline">
          Sign in
        </Link>
      </p>
    </div>
  );
}
