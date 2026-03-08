import { useEffect, useRef } from "react";
import { Link, useSearchParams } from "react-router";

import { useAcceptProjectInvitation } from "@/features/projects/hooks/useProjectMembers";
import { getErrorMessage } from "@/shared/lib/errors";
import { Button } from "@/shared/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/shared/ui/card";

export default function ProjectInvitationAcceptPage() {
  const [searchParams] = useSearchParams();
  const token = searchParams.get("token");
  const acceptMutation = useAcceptProjectInvitation();
  const { mutate } = acceptMutation;
  const hasAttemptedRef = useRef(false);

  useEffect(() => {
    if (!token || hasAttemptedRef.current) return;
    hasAttemptedRef.current = true;
    mutate({ token });
  }, [token, mutate]);

  return (
    <div className="mx-auto flex w-full max-w-xl flex-col gap-4 py-6">
      <Card className="bg-card/70">
        <CardHeader>
          <CardTitle>Project Invitation</CardTitle>
          <CardDescription>Accept your project invitation to continue.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {!token ? (
            <p className="text-sm text-destructive">Missing invitation token.</p>
          ) : acceptMutation.isPending ? (
            <p className="text-sm text-muted-foreground">Accepting invitation...</p>
          ) : acceptMutation.isSuccess ? (
            <div className="space-y-3">
              <p className="text-sm text-emerald-700 dark:text-emerald-300">
                Invitation accepted successfully.
              </p>
              <Button asChild>
                <Link to={`/projects/${acceptMutation.data.project_id}/tasks`}>
                  Open Project
                </Link>
              </Button>
            </div>
          ) : acceptMutation.isError ? (
            <div className="space-y-3">
              <p className="text-sm text-destructive">
                {getErrorMessage(acceptMutation.error)}
              </p>
              <Button variant="outline" onClick={() => token && mutate({ token })}>
                Try Again
              </Button>
            </div>
          ) : null}
        </CardContent>
      </Card>
    </div>
  );
}
