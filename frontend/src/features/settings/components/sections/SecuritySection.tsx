import { zodResolver } from "@hookform/resolvers/zod";
import { Circle, CircleCheck, Loader2 } from "lucide-react";
import { useMemo } from "react";
import { useForm } from "react-hook-form";
import { Link } from "react-router";
import { toast } from "sonner";
import { z } from "zod";

import { useChangePassword } from "@/features/auth";
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

const changePasswordSchema = z
  .object({
    current_password: z.string().min(1, "Current password is required."),
    new_password: z
      .string()
      .min(8, "Password must be at least 8 characters.")
      .regex(/[A-Z]/, "Password must contain at least one uppercase letter")
      .regex(/[0-9]/, "Password must contain at least one number")
      .regex(/[^a-zA-Z0-9]/, "Password must contain at least one special character"),
    confirm_password: z.string().min(1, "Please confirm your password."),
  })
  .refine((data) => data.new_password === data.confirm_password, {
    message: "Passwords do not match",
    path: ["confirm_password"],
  });

type ChangePasswordFormValues = z.infer<typeof changePasswordSchema>;

export function SecuritySection() {
  const changePasswordMutation = useChangePassword();

  const securityForm = useForm<ChangePasswordFormValues>({
    resolver: zodResolver(changePasswordSchema),
    defaultValues: {
      current_password: "",
      new_password: "",
      confirm_password: "",
    },
  });

  const newPassword = securityForm.watch("new_password");

  const checklist = useMemo(
    () => [
      { label: "At least 8 characters", valid: newPassword.length >= 8 },
      { label: "One uppercase letter", valid: /[A-Z]/.test(newPassword) },
      { label: "One number", valid: /[0-9]/.test(newPassword) },
      { label: "One special character", valid: /[^a-zA-Z0-9]/.test(newPassword) },
    ],
    [newPassword],
  );

  return (
    <section className="space-y-5">
      <div className="space-y-1">
        <h2 className="text-xl font-semibold text-foreground">Security</h2>
        <p className="text-sm text-muted-foreground">Update your password while you are signed in.</p>
      </div>
      {changePasswordMutation.isError ? (
        <Alert variant="destructive" className="mb-5">
          <AlertDescription>{getErrorMessage(changePasswordMutation.error)}</AlertDescription>
        </Alert>
      ) : null}

      <Form {...securityForm}>
        <form
          className="w-full max-w-[42rem] space-y-6"
          onSubmit={securityForm.handleSubmit((data) => {
            changePasswordMutation.mutate(
              {
                current_password: data.current_password,
                new_password: data.new_password,
              },
              {
                onSuccess: () => {
                  securityForm.reset({
                    current_password: "",
                    new_password: "",
                    confirm_password: "",
                  });
                  toast.success("Password changed successfully");
                },
              },
            );
          })}
        >
          <div className="grid w-full gap-4">
            <FormField
              control={securityForm.control}
              name="current_password"
              render={({ field }) => (
                <FormItem className="w-full max-w-[28rem]">
                  <FormLabel>Current Password</FormLabel>
                  <FormControl>
                    <Input type="password" autoComplete="current-password" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={securityForm.control}
              name="new_password"
              render={({ field }) => (
                <FormItem className="w-full max-w-[28rem]">
                  <FormLabel>New Password</FormLabel>
                  <FormControl>
                    <Input type="password" autoComplete="new-password" {...field} />
                  </FormControl>
                  <ul className="space-y-1 text-xs text-muted-foreground">
                    {checklist.map((item) => (
                      <li key={item.label} className="flex items-center gap-2">
                        {item.valid ? (
                          <CircleCheck className="h-3.5 w-3.5 text-foreground" />
                        ) : (
                          <Circle className="h-3.5 w-3.5" />
                        )}
                        <span>{item.label}</span>
                      </li>
                    ))}
                  </ul>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={securityForm.control}
              name="confirm_password"
              render={({ field }) => (
                <FormItem className="w-full max-w-[28rem]">
                  <FormLabel>Confirm New Password</FormLabel>
                  <FormControl>
                    <Input type="password" autoComplete="new-password" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
          </div>

          <div className="space-y-3">
            <Link to="/forgot-password" className="text-sm text-muted-foreground underline-offset-4 hover:underline">
              Need account recovery?
            </Link>
            <div className="flex w-full justify-end">
              <Button type="submit" className="h-10 min-w-36 justify-center" disabled={changePasswordMutation.isPending}>
                {changePasswordMutation.isPending ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Updating...
                  </>
                ) : (
                  "Change Password"
                )}
              </Button>
            </div>
          </div>
        </form>
      </Form>
    </section>
  );
}
