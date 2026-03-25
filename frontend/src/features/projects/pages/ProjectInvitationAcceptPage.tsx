import { useEffect, useEffectEvent, useMemo, useRef, useState } from "react";
import { useLocation, useNavigate, useSearchParams } from "react-router";
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
  const routeAcceptedInvitation = (
    (location.state as InvitationAcceptLocationState | null)?.acceptedInvitation ?? null
  );
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

      return cacheKey ? invitationAcceptSuccessCache.get(cacheKey) ?? null : null;
    },
  );
  const [acceptError, setAcceptError] = useState<unknown>(null);
  const [isAccepting, setIsAccepting] = useState(() => (
    Boolean(cacheKey)
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
  }, [acceptPayload, cacheKey, routeAcceptedInvitation, startAcceptance]);

  function handleRetry() {
    if (!acceptPayload || !cacheKey) {
      return;
    }

    autoAttemptedKeysRef.current.delete(cacheKey);
    invitationAcceptSuccessCache.delete(cacheKey);
    invitationAcceptPromiseCache.delete(cacheKey);
    startAcceptance(acceptPayload, cacheKey);
  }

  const cardTitle = acceptedInvitation ? "Invitation Accepted" : "Project Invitation";
  const cardDescription = acceptedInvitation
    ? "You have accepted the invitation. Go to the project page."
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
    <div className="mx-auto flex w-full max-w-xl flex-col gap-4 py-6">
      <Card className="bg-card/70">
        <CardHeader>
          <CardTitle>{cardTitle}</CardTitle>
          <CardDescription>{cardDescription}</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {!acceptPayload ? (
            <p className="text-sm text-destructive">Missing invitation details.</p>
          ) : isAccepting ? (
            <p className="text-sm text-muted-foreground">Accepting invitation...</p>
          ) : acceptedInvitation ? (
            <div className="space-y-3">
              {openProjectError ? (
                <p className="text-sm text-destructive">
                  {getErrorMessage(openProjectError)}
                </p>
              ) : null}
              <Button onClick={() => void openAcceptedProject(acceptedInvitation.project_id)}>
                Go to Project
              </Button>
            </div>
          ) : acceptError ? (
            <div className="space-y-3">
              <p className="text-sm text-destructive">
                {getErrorMessage(acceptError)}
              </p>
              <Button variant="outline" onClick={handleRetry}>
                Try Again
              </Button>
            </div>
          ) : null}
        </CardContent>
      </Card>
    </div>
  );
}
