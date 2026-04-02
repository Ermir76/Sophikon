import { zodResolver } from "@hookform/resolvers/zod";
import { Loader2 } from "lucide-react";
import { useForm } from "react-hook-form";
import { Link, useSearchParams } from "react-router";
import { z } from "zod";

import { useRegister } from "@/features/auth/hooks/useAuth";
import { createPasswordSchema } from "@/features/auth/lib/passwordPolicy";
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

const DUPLICATE_EMAIL_MESSAGE = "Email already registered";
const NEUTRAL_REGISTER_ERROR_MESSAGE =
  "We couldn't complete sign up with that email. Try signing in, resetting your password, or checking your inbox for a verification email.";

const registerSchema = z
  .object({
    full_name: z.string().min(2, "Name must be at least 2 characters."),
    email: z.email("Please enter a valid email address."),
    password: createPasswordSchema(),
    confirmPassword: z.string().min(8, "Password confirmation is required."),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: "Passwords do not match",
    path: ["confirmPassword"],
  });

type RegisterFormValues = z.infer<typeof registerSchema>;

export default function RegisterPage() {
  const [searchParams] = useSearchParams();
  const next = searchParams.get("next");
  const registerMutation = useRegister(next);
  const loginHref = next ? `/login?next=${encodeURIComponent(next)}` : "/login";
  const forgotPasswordHref = "/forgot-password";

  const form = useForm<RegisterFormValues>({
    resolver: zodResolver(registerSchema),
    defaultValues: {
      full_name: "",
      email: "",
      password: "",
      confirmPassword: "",
    },
  });

  function onSubmit(data: RegisterFormValues) {
    const { confirmPassword: _confirmPassword, ...apiData } = data;
    registerMutation.mutate(apiData);
  }

  const registerErrorMessage = getErrorMessage(registerMutation.error);
  const visibleRegisterErrorMessage =
    registerErrorMessage === DUPLICATE_EMAIL_MESSAGE
      ? NEUTRAL_REGISTER_ERROR_MESSAGE
      : registerErrorMessage;

  return (
    <div>
      <div className="mb-8">
        <h2 className="mb-2 text-3xl font-semibold">Create an account</h2>
        <p className="text-sm text-muted-foreground">
          Enter your information to get started.
        </p>
      </div>

      {registerMutation.isError && (
        <Alert variant="destructive" className="mb-5">
          <AlertDescription className="space-y-2">
            <p>{visibleRegisterErrorMessage}</p>
            {registerErrorMessage === DUPLICATE_EMAIL_MESSAGE ? (
              <p>
                <Link to={loginHref} className="underline">
                  Sign in
                </Link>{" "}
                or{" "}
                <Link to={forgotPasswordHref} className="underline">
                  reset your password
                </Link>
                .
              </p>
            ) : null}
          </AlertDescription>
        </Alert>
      )}

      <Form {...form}>
        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-5">
          <FormField
            control={form.control}
            name="full_name"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Full Name</FormLabel>
                <FormControl>
                  <Input placeholder="John Doe" autoComplete="name" {...field} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          <FormField
            control={form.control}
            name="email"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Email</FormLabel>
                <FormControl>
                  <Input
                    placeholder="name@example.com"
                    autoComplete="email"
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
                <FormLabel>Password</FormLabel>
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

          <Button type="submit" className="w-full" disabled={registerMutation.isPending}>
            {registerMutation.isPending ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Creating account...
              </>
            ) : (
              "Sign Up"
            )}
          </Button>
        </form>
      </Form>

      <p className="mt-7 text-center text-sm text-muted-foreground">
        Already have an account?{" "}
        <Link to={loginHref} className="underline">
          Sign in
        </Link>
      </p>
    </div>
  );
}
