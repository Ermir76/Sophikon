import { useEffect, useEffectEvent, useMemo, useRef, useState } from "react";
import { Link, useLocation, useNavigate, useSearchParams } from "react-router";
import { Loader2 } from "lucide-react";
import { toast } from "sonner";

import { useAuthStore } from "@/features/auth";
import { useOrganizations, useOrgStore } from "@/features/organizations";
import { projectService } from "@/features/projects/api/project.service";
import { useAcceptProjectInvitation } from "@/features/projects/hooks/useProjectMembers";
import type { AcceptProjectInvitationRequest } from "@/features/projects/types";
import { getErrorMessage } from "@/shared/lib/errors";
import { Button } from "@/shared/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/shared/ui/card";

type AcceptedInvitationData = {
  project_id: string;
  member_id: string;
};

type InvitationAcceptLocationState = {
  acceptedInvitation?: AcceptedInvitationData;
  review?: boolean;
  title?: string;
  message?: string;
};

const invitationAcceptSuccessCache = new Map<string, AcceptedInvitationData>();
const invitationAcceptPromiseCache = new Map<string, Promise<AcceptedInvitationData>>();

export default function ProjectInvitationAcceptPage() {
  const location = useLocation();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const token = searchParams.get("token");
  const invitationId = searchParams.get("invitation_id");
  const currentUserId = useAuthStore((state) => state.user?.id ?? null);
  const activeOrgId = useOrgStore((state) => state.activeOrgId);
  const setActiveOrg = useOrgStore((state) => state.setActiveOrg);
  const { data: organizationsData } = useOrganizations();
  const locationState = location.state as InvitationAcceptLocationState | null;
  const routeAcceptedInvitation = locationState?.acceptedInvitation ?? null;
  const isReviewMode = locationState?.review === true;
  const reviewTitle = locationState?.title ?? null;
  const reviewMessage = locationState?.message ?? null;
  const acceptPayload = useMemo<AcceptProjectInvitationRequest | null>(() => {
    if (token) {
      return { token };
    }
    if (invitationId) {
      return { invitation_id: invitationId };
    }
    return null;
  }, [invitationId, token]);
  const cacheKey = useMemo(
    () => (
      acceptPayload
        ? `${currentUserId ?? "anonymous"}:${token ? `token:${token}` : `invitation:${invitationId}`}`
        : null
    ),
    [acceptPayload, currentUserId, invitationId, token],
  );
  const acceptMutation = useAcceptProjectInvitation();
  const { mutateAsync } = acceptMutation;
  const [acceptedInvitation, setAcceptedInvitation] = useState<AcceptedInvitationData | null>(
    () => {
      if (cacheKey && routeAcceptedInvitation) {
        invitationAcceptSuccessCache.set(cacheKey, routeAcceptedInvitation);
        return routeAcceptedInvitation;
      }

      // In review mode, don't restore from cache — let the user review first
      if (isReviewMode) {
        return null;
      }

      return cacheKey ? invitationAcceptSuccessCache.get(cacheKey) ?? null : null;
    },
  );
  const [acceptError, setAcceptError] = useState<unknown>(null);
  const [isAccepting, setIsAccepting] = useState(() => (
    Boolean(cacheKey)
      && !isReviewMode
      && routeAcceptedInvitation === null
      && !invitationAcceptSuccessCache.has(cacheKey)
  ));
  const [openProjectError, setOpenProjectError] = useState<unknown>(null);
  const attemptRef = useRef(0);
  const autoAttemptedKeysRef = useRef<Set<string>>(new Set());
  const mountedRef = useRef(false);
  const openedProjectRef = useRef<string | null>(null);

  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
    };
  }, []);

  const startAcceptance = useEffectEvent((
    invitationPayload: AcceptProjectInvitationRequest,
    invitationCacheKey: string,
  ) => {
    const cachedSuccess = invitationAcceptSuccessCache.get(invitationCacheKey);
    if (cachedSuccess) {
      setAcceptedInvitation(cachedSuccess);
      setAcceptError(null);
      setIsAccepting(false);
      return;
    }

    const attemptId = attemptRef.current + 1;
    attemptRef.current = attemptId;
    setAcceptedInvitation(null);
    setAcceptError(null);
    setIsAccepting(true);

    const request = invitationAcceptPromiseCache.get(invitationCacheKey) ?? mutateAsync(
      invitationPayload,
    );
    if (!invitationAcceptPromiseCache.has(invitationCacheKey)) {
      invitationAcceptPromiseCache.set(invitationCacheKey, request);
    }

    void request
      .then((data) => {
        invitationAcceptSuccessCache.set(invitationCacheKey, data);
        invitationAcceptPromiseCache.delete(invitationCacheKey);
        if (!mountedRef.current || attemptRef.current !== attemptId) {
          return;
        }
        setAcceptedInvitation(data);
        setAcceptError(null);
        setIsAccepting(false);
      })
      .catch((error) => {
        invitationAcceptPromiseCache.delete(invitationCacheKey);
        if (!mountedRef.current || attemptRef.current !== attemptId) {
          return;
        }
        setAcceptError(error);
        setIsAccepting(false);
      });
  });

  useEffect(() => {
    if (cacheKey && routeAcceptedInvitation) {
      invitationAcceptSuccessCache.set(cacheKey, routeAcceptedInvitation);
      setAcceptedInvitation(routeAcceptedInvitation);
      setAcceptError(null);
      setIsAccepting(false);
      return;
    }

    if (!acceptPayload || !cacheKey) {
      setAcceptedInvitation(null);
      setAcceptError(null);
      setIsAccepting(false);
      return;
    }

    // In review mode, don't auto-accept — wait for the user to click Accept
    if (isReviewMode) {
      return;
    }

    const cachedSuccess = invitationAcceptSuccessCache.get(cacheKey);
    if (cachedSuccess) {
      setAcceptedInvitation(cachedSuccess);
      setAcceptError(null);
      setIsAccepting(false);
      return;
    }

    if (autoAttemptedKeysRef.current.has(cacheKey)) {
      return;
    }

    autoAttemptedKeysRef.current.add(cacheKey);
    startAcceptance(acceptPayload, cacheKey);
  }, [acceptPayload, cacheKey, isReviewMode, routeAcceptedInvitation, startAcceptance]);

  function handleRetry() {
    if (!acceptPayload || !cacheKey) {
      return;
    }

    autoAttemptedKeysRef.current.delete(cacheKey);
    invitationAcceptSuccessCache.delete(cacheKey);
    invitationAcceptPromiseCache.delete(cacheKey);
    startAcceptance(acceptPayload, cacheKey);
  }

  function handleReviewAccept() {
    if (!acceptPayload || !cacheKey) {
      return;
    }

    startAcceptance(acceptPayload, cacheKey);
  }

  function handleReviewCancel() {
    navigate("/", { replace: true });
  }

  const cardTitle = acceptedInvitation ? "Invitation Accepted" : "Project Invitation";
  const cardDescription = acceptedInvitation
    ? "You have accepted the invitation. Go to the project page."
    : isReviewMode
      ? "Review the invitation details before accepting."
      : "Accept your project invitation to continue.";

  const openAcceptedProject = useEffectEvent(async (projectId: string) => {
    if (openedProjectRef.current === projectId) {
      return;
    }

    openedProjectRef.current = projectId;
    setOpenProjectError(null);

    try {
      const project = await projectService.get(projectId);
      const nextOrgId = project.organization_id;
      const nextOrg = organizationsData?.items.find((organization) => organization.id === nextOrgId);

      if (activeOrgId !== nextOrgId) {
        setActiveOrg(nextOrgId);
        toast.success(
          nextOrg ? `Switched to ${nextOrg.name}` : "Switched organization",
          {
            description: "Opening your invited project.",
          },
        );
      }

      navigate(`/projects/${projectId}/tasks`, { replace: true });
    } catch (error) {
      openedProjectRef.current = null;
      setOpenProjectError(error);
      toast.error("Failed to open project", {
        description: getErrorMessage(error),
      });
    }
  });

  return (
    <div className="mx-auto flex min-h-[60vh] w-full max-w-xl flex-col justify-center gap-4 px-4 py-6">
      <Card className="bg-card/70">
        <CardHeader>
          <CardTitle>{cardTitle}</CardTitle>
          <CardDescription>{cardDescription}</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {!acceptPayload ? (
            <div className="space-y-3">
              <p className="text-sm text-destructive" role="alert">
                This invitation link is missing required details. It may be invalid or expired.
              </p>
              <Button asChild variant="outline">
                <Link to="/">Back to Dashboard</Link>
              </Button>
            </div>
          ) : isAccepting ? (
            <div aria-live="polite" className="flex items-center gap-2 text-sm text-muted-foreground">
              <Loader2 className="size-4 animate-spin" />
              <span>Accepting your invitation...</span>
            </div>
          ) : acceptedInvitation ? (
            <div className="space-y-3">
              {openProjectError ? (
                <p className="text-sm text-destructive" role="alert">
                  {getErrorMessage(openProjectError)}
                </p>
              ) : null}
              <Button onClick={() => void openAcceptedProject(acceptedInvitation.project_id)}>
                Go to Project
              </Button>
            </div>
          ) : acceptError ? (
            <div className="space-y-3">
              <p className="text-sm text-destructive" role="alert">
                {getErrorMessage(acceptError)}
              </p>
              <Button variant="outline" onClick={handleRetry}>
                Try Again
              </Button>
            </div>
          ) : isReviewMode ? (
            <div className="space-y-4">
              <div className="space-y-2 rounded-md border bg-muted/30 p-4">
                <p className="text-sm font-medium">
                  {reviewTitle ?? "Project invitation"}
                </p>
                {reviewMessage ? (
                  <p className="whitespace-pre-wrap text-sm text-muted-foreground">
                    {reviewMessage}
                  </p>
                ) : (
                  <p className="text-sm text-muted-foreground">
                    No personal message was included with this invitation.
                  </p>
                )}
              </div>
              <div className="flex items-center gap-2">
                <Button onClick={handleReviewAccept}>
                  Accept Invitation
                </Button>
                <Button variant="outline" onClick={handleReviewCancel}>
                  Cancel
                </Button>
              </div>
            </div>
          ) : null}
        </CardContent>
      </Card>
    </div>
  );
}
