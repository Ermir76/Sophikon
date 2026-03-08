import { type FormEvent, useState } from "react";
import { Plus } from "lucide-react";
import { toast } from "sonner";

import { useAuthStore } from "@/features/auth";
import {
  useInviteProjectMember,
  useProjectInvitations,
  useProjectMembers,
  useRemoveProjectMember,
  useResendProjectInvitation,
  useRevokeProjectInvitation,
  useUpdateProjectMemberRole,
} from "@/features/projects/hooks/useProjectMembers";
import type {
  InviteProjectMemberRequest,
  ProjectMember,
  ProjectMemberRole,
} from "@/features/projects/types";
import { QueryError } from "@/shared/components/QueryError";
import { PageLoading } from "@/shared/components/state/PageLoading";
import { getErrorMessage } from "@/shared/lib/errors";
import { Badge } from "@/shared/ui/badge";
import { Button } from "@/shared/ui/button";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/shared/ui/alert-dialog";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/shared/ui/dialog";
import { Input } from "@/shared/ui/input";
import { Label } from "@/shared/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/shared/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/shared/ui/table";
import { Textarea } from "@/shared/ui/textarea";

const OWNER_ROLE_OPTIONS: ProjectMemberRole[] = ["owner", "manager", "member", "viewer"];
const MANAGER_ROLE_OPTIONS: ProjectMemberRole[] = ["member", "viewer"];

function roleBadgeClass(role: ProjectMemberRole): string {
  if (role === "owner") return "border-destructive/45 bg-destructive/12 text-destructive";
  if (role === "manager") return "border-primary/45 bg-primary/12 text-primary";
  if (role === "member") return "border-emerald-500/40 bg-emerald-500/10 text-emerald-700 dark:text-emerald-300";
  return "border-muted-foreground/30 bg-muted/35 text-muted-foreground";
}

function formatDate(date: string): string {
  return new Date(date).toLocaleDateString();
}

interface InviteProjectMemberDialogProps {
  isPending: boolean;
  roleOptions: ProjectMemberRole[];
  onInvite: (data: InviteProjectMemberRequest) => Promise<void>;
}

function InviteProjectMemberDialog({
  isPending,
  roleOptions,
  onInvite,
}: InviteProjectMemberDialogProps) {
  const [open, setOpen] = useState(false);
  const [email, setEmail] = useState("");
  const [role, setRole] = useState<ProjectMemberRole>(roleOptions[0] ?? "member");
  const [message, setMessage] = useState("");

  const onSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    await onInvite({
      email: email.trim(),
      role,
      message: message.trim() || undefined,
    });
    setEmail("");
    setRole(roleOptions[0] ?? "member");
    setMessage("");
    setOpen(false);
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button size="sm" className="h-8 px-3 text-xs">
          <Plus className="mr-1.5 size-3.5" />
          Invite Member
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Invite to Project</DialogTitle>
          <DialogDescription>
            Send an email invitation to join this project.
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={onSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="invite-email">Email</Label>
            <Input
              id="invite-email"
              type="email"
              required
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              placeholder="teammate@company.com"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="invite-role">Role</Label>
            <Select value={role} onValueChange={(value) => setRole(value as ProjectMemberRole)}>
              <SelectTrigger id="invite-role">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {roleOptions.map((roleOption) => (
                  <SelectItem key={roleOption} value={roleOption}>
                    {roleOption}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2">
            <Label htmlFor="invite-message">Message (optional)</Label>
            <Textarea
              id="invite-message"
              value={message}
              onChange={(event) => setMessage(event.target.value)}
              placeholder="Optional context for the invite email."
              className="min-h-20 resize-y"
            />
          </div>
          <DialogFooter>
            <Button type="submit" disabled={isPending}>
              {isPending ? "Sending..." : "Send Invitation"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

interface ProjectMembersTabProps {
  projectId: string;
}

export function ProjectMembersTab({ projectId }: ProjectMembersTabProps) {
  const currentUserId = useAuthStore((state) => state.user?.id);
  const [memberToRemove, setMemberToRemove] = useState<ProjectMember | null>(null);

  const {
    data: membersResponse,
    isLoading: isMembersLoading,
    isError: isMembersError,
    refetch: refetchMembers,
  } = useProjectMembers(projectId);
  const members = membersResponse?.items ?? [];
  const myMembership = members.find((member) => member.user_id === currentUserId);
  const myRole = myMembership?.role;
  const canInviteOrRemove = myRole === "owner" || myRole === "manager";
  const canChangeRoles = myRole === "owner";
  const inviteRoleOptions = myRole === "manager" ? MANAGER_ROLE_OPTIONS : OWNER_ROLE_OPTIONS;
  const {
    data: invitationsResponse,
    isLoading: isInvitationsLoading,
    isError: isInvitationsError,
    refetch: refetchInvitations,
  } = useProjectInvitations(projectId, canInviteOrRemove);

  const inviteMutation = useInviteProjectMember(projectId);
  const updateRoleMutation = useUpdateProjectMemberRole(projectId);
  const removeMemberMutation = useRemoveProjectMember(projectId);
  const resendMutation = useResendProjectInvitation(projectId);
  const revokeMutation = useRevokeProjectInvitation(projectId);

  const invitations = invitationsResponse?.items ?? [];

  const onInvite = async (data: InviteProjectMemberRequest) => {
    try {
      await inviteMutation.mutateAsync(data);
      toast.success("Invitation sent", {
        description: `Invited ${data.email} as ${data.role}.`,
      });
    } catch (error) {
      toast.error("Failed to invite member", {
        description: getErrorMessage(error),
      });
    }
  };

  const onUpdateRole = async (member: ProjectMember, role: ProjectMemberRole) => {
    try {
      await updateRoleMutation.mutateAsync({ memberId: member.id, role });
      toast.success("Role updated", {
        description: `${member.user_full_name || member.user_email} is now ${role}.`,
      });
    } catch (error) {
      toast.error("Failed to update role", {
        description: getErrorMessage(error),
      });
    }
  };

  const onRemoveMember = async (member: ProjectMember) => {
    try {
      await removeMemberMutation.mutateAsync(member.id);
      toast.success("Member removed", {
        description: `${member.user_full_name || member.user_email} was removed from the project.`,
      });
      setMemberToRemove(null);
    } catch (error) {
      toast.error("Failed to remove member", {
        description: getErrorMessage(error),
      });
    }
  };

  const onResend = async (invitationId: string) => {
    try {
      await resendMutation.mutateAsync(invitationId);
      toast.success("Invitation resent");
    } catch (error) {
      toast.error("Failed to resend invitation", {
        description: getErrorMessage(error),
      });
    }
  };

  const onRevoke = async (invitationId: string) => {
    try {
      await revokeMutation.mutateAsync(invitationId);
      toast.success("Invitation revoked");
    } catch (error) {
      toast.error("Failed to revoke invitation", {
        description: getErrorMessage(error),
      });
    }
  };

  if (isMembersError) {
    return (
      <QueryError
        message="Failed to load project members."
        onRetry={() => refetchMembers()}
      />
    );
  }

  if (isMembersLoading) {
    return <PageLoading message="Loading members..." />;
  }

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between gap-3">
        <div>
          <h3 className="text-sm font-semibold uppercase tracking-wide text-muted-foreground">
            Active Members
          </h3>
          <p className="text-sm text-muted-foreground">
            Manage roles and access for this project.
          </p>
        </div>
        {canInviteOrRemove ? (
          <InviteProjectMemberDialog
            isPending={inviteMutation.isPending}
            roleOptions={inviteRoleOptions}
            onInvite={onInvite}
          />
        ) : null}
      </div>

      <div className="overflow-hidden rounded-lg border bg-card/70">
        <Table>
          <TableHeader className="sticky top-0 z-20 bg-card/95 backdrop-blur supports-[backdrop-filter]:bg-card/85">
            <TableRow>
              <TableHead>User</TableHead>
              <TableHead>Role</TableHead>
              <TableHead>Joined</TableHead>
              <TableHead className="w-[220px]">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {members.length === 0 ? (
              <TableRow>
                <TableCell colSpan={4} className="h-20 text-center text-muted-foreground">
                  No members found.
                </TableCell>
              </TableRow>
            ) : (
              members.map((member) => {
                const isCurrentUser = member.user_id === currentUserId;
                const managerCanRemove = myRole === "manager" && (member.role === "member" || member.role === "viewer");
                const ownerCanRemove = myRole === "owner" && !isCurrentUser;
                const canRemove = ownerCanRemove || managerCanRemove;

                return (
                  <TableRow key={member.id}>
                    <TableCell>
                      <div className="flex flex-col gap-0.5">
                        <span className="font-medium">{member.user_full_name || "Unknown user"}</span>
                        <span className="text-xs text-muted-foreground">
                          {member.user_email || "No email"}
                        </span>
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline" className={roleBadgeClass(member.role)}>
                        {member.role}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-sm text-muted-foreground">
                      {formatDate(member.joined_at)}
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        {canChangeRoles && !isCurrentUser ? (
                          <Select
                            value={member.role}
                            onValueChange={(value) =>
                              onUpdateRole(member, value as ProjectMemberRole)
                            }
                          >
                            <SelectTrigger className="h-8 w-32">
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              {OWNER_ROLE_OPTIONS.map((role) => (
                                <SelectItem key={role} value={role}>
                                  {role}
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                        ) : null}
                        {canRemove ? (
                          <Button
                            variant="outline"
                            size="sm"
                            className="h-8"
                            onClick={() => setMemberToRemove(member)}
                            disabled={removeMemberMutation.isPending}
                          >
                            Remove
                          </Button>
                        ) : null}
                      </div>
                    </TableCell>
                  </TableRow>
                );
              })
            )}
          </TableBody>
        </Table>
      </div>

      <div>
        <h3 className="text-sm font-semibold uppercase tracking-wide text-muted-foreground">
          Pending Invitations
        </h3>
        <p className="text-sm text-muted-foreground">
          Invitations waiting to be accepted.
        </p>
      </div>

      {!canInviteOrRemove ? (
        <div className="rounded-lg border bg-card/70 p-4 text-sm text-muted-foreground">
          Only owners and managers can view pending invitations.
        </div>
      ) : isInvitationsError ? (
        <QueryError
          message="Failed to load pending invitations."
          onRetry={() => refetchInvitations()}
        />
      ) : isInvitationsLoading ? (
        <PageLoading message="Loading invitations..." />
      ) : (
        <div className="overflow-hidden rounded-lg border bg-card/70">
          <Table>
            <TableHeader className="sticky top-0 z-20 bg-card/95 backdrop-blur supports-[backdrop-filter]:bg-card/85">
              <TableRow>
                <TableHead>Email</TableHead>
                <TableHead>Role</TableHead>
                <TableHead>Invited by</TableHead>
                <TableHead>Expires</TableHead>
                <TableHead className="w-[200px]">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {invitations.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={5} className="h-20 text-center text-muted-foreground">
                    No pending invitations.
                  </TableCell>
                </TableRow>
              ) : (
                invitations.map((invitation) => (
                  <TableRow key={invitation.id}>
                    <TableCell className="font-medium">{invitation.email}</TableCell>
                    <TableCell>
                      <Badge variant="outline" className={roleBadgeClass(invitation.role)}>
                        {invitation.role}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-sm text-muted-foreground">
                      {invitation.invited_by_full_name || invitation.invited_by_email || "Unknown"}
                    </TableCell>
                    <TableCell className="text-sm text-muted-foreground">
                      {formatDate(invitation.expires_at)}
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <Button
                          variant="outline"
                          size="sm"
                          className="h-8"
                          onClick={() => onResend(invitation.id)}
                          disabled={resendMutation.isPending}
                        >
                          Resend
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          className="h-8"
                          onClick={() => onRevoke(invitation.id)}
                          disabled={revokeMutation.isPending}
                        >
                          Revoke
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </div>
      )}

      <AlertDialog
        open={!!memberToRemove}
        onOpenChange={(open) => !open && setMemberToRemove(null)}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Remove member?</AlertDialogTitle>
            <AlertDialogDescription>
              This will remove{" "}
              {memberToRemove?.user_full_name || memberToRemove?.user_email}{" "}
              from the project immediately.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => memberToRemove && onRemoveMember(memberToRemove)}
              disabled={removeMemberMutation.isPending}
              className="bg-destructive hover:bg-destructive/90"
            >
              {removeMemberMutation.isPending ? "Removing..." : "Remove Member"}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
