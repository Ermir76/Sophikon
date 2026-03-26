import { useState } from "react";
import { toast } from "sonner";
import { Separator } from "@/shared/ui/separator";
import { Badge } from "@/shared/ui/badge";
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
import { useOrgStore } from "@/features/organizations/store/org-store";
import { useAuthStore } from "@/features/auth";
import type { OrganizationMember, OrgRole } from "@/features/organizations/types";
import {
  useOrgMembers,
  useInviteMember,
  useRemoveMember,
  useUpdateMemberRole,
  useOrganization,
} from "@/features/organizations/hooks/useOrganizations";
import { useMyOrgRole } from "@/features/organizations/hooks/useMyOrgRole";
import { QueryError } from "@/shared/components/QueryError";
import { getErrorMessage } from "@/shared/lib/errors";
import { MembersTable } from "@/features/organizations/components/MembersTable";
import {
  InviteMemberDialog,
  type InviteFormValues,
} from "@/features/organizations/components/InviteMemberDialog";

import { PageShell } from "@/shared/components/layout/PageShell";
import { PageHeader } from "@/shared/components/layout/PageHeader";
import { PageLoading } from "@/shared/components/state/PageLoading";
import { PageEmpty } from "@/shared/components/state/PageEmpty";

export default function OrgMembersPage() {
  const shellClassName = "h-full overflow-y-auto";
  const activeOrgId = useOrgStore((state) => state.activeOrgId);
  const currentUser = useAuthStore((state) => state.user);
  const { role: myRole } = useMyOrgRole();
  const canManage = myRole === "owner" || myRole === "admin";

  const { data: activeOrganization } = useOrganization(activeOrgId);
  const {
    data: membersData,
    isLoading: isLoadingMembers,
    isError: isMembersError,
    refetch: refetchMembers,
  } = useOrgMembers(activeOrgId);

  const inviteMutation = useInviteMember(activeOrgId);
  const removeMemberMutation = useRemoveMember(activeOrgId);
  const updateRoleMutation = useUpdateMemberRole(activeOrgId);

  const [memberToRemove, setMemberToRemove] =
    useState<OrganizationMember | null>(null);
  const [pendingRoleChange, setPendingRoleChange] = useState<{
    member: OrganizationMember;
    newRole: OrgRole;
  } | null>(null);
  const [updatingRoleMemberId, setUpdatingRoleMemberId] = useState<string | null>(null);

  const onInvite = async (data: InviteFormValues) => {
    try {
      await inviteMutation.mutateAsync(data);
      toast.success("Invitation sent", {
        description: `Invited ${data.email} as ${data.role}.`,
      });
    } catch (error) {
      toast.error("Error", {
        description: getErrorMessage(error),
      });
    }
  };

  const confirmRemoveMember = async () => {
    if (!memberToRemove) return;
    try {
      await removeMemberMutation.mutateAsync(memberToRemove.id);
      toast.success("Member removed", {
        description: "The member has been removed from the organization.",
      });
      setMemberToRemove(null);
    } catch (error) {
      toast.error("Error", {
        description: getErrorMessage(error),
      });
    }
  };

  const applyRoleChange = async (member: OrganizationMember, newRole: OrgRole) => {
    setUpdatingRoleMemberId(member.id);
    try {
      await updateRoleMutation.mutateAsync({
        memberId: member.id,
        data: { role: newRole },
      });
      toast.success("Role updated", {
        description: `${member.user_full_name || member.user_email}'s role updated to ${newRole}.`,
      });
    } catch (error) {
      toast.error("Error", {
        description: getErrorMessage(error),
      });
    } finally {
      setUpdatingRoleMemberId(null);
    }
  };

  const confirmRoleChange = async () => {
    if (!pendingRoleChange) {
      return;
    }
    const { member, newRole } = pendingRoleChange;
    await applyRoleChange(member, newRole);
    setPendingRoleChange(null);
  };

  const members = membersData?.items || [];
  const ownerCount = members.filter((member) => member.role === "owner").length;
  const adminCount = members.filter((member) => member.role === "admin").length;
  const standardCount = members.filter((member) => member.role === "member").length;

  return (
    <PageShell className={shellClassName}>
      <PageHeader
        title="Members"
        description="Manage who has access to this organization."
        action={
          canManage && (
            <InviteMemberDialog
              orgName={activeOrganization?.name}
              onInvite={onInvite}
              isPending={inviteMutation.isPending}
            />
          )
        }
      />

      {!isLoadingMembers && members.length > 0 ? (
        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
          <div className="rounded-md border bg-card/70 px-4 py-3">
            <p className="text-xs uppercase tracking-wide text-muted-foreground">Total</p>
            <p className="mt-1 text-lg font-semibold tabular-nums">{members.length}</p>
          </div>
          <div className="rounded-md border bg-card/70 px-4 py-3">
            <p className="text-xs uppercase tracking-wide text-muted-foreground">Owners</p>
            <p className="mt-1 text-lg font-semibold tabular-nums">{ownerCount}</p>
          </div>
          <div className="rounded-md border bg-card/70 px-4 py-3">
            <p className="text-xs uppercase tracking-wide text-muted-foreground">Admins</p>
            <p className="mt-1 text-lg font-semibold tabular-nums">{adminCount}</p>
          </div>
          <div className="rounded-md border bg-card/70 px-4 py-3">
            <p className="text-xs uppercase tracking-wide text-muted-foreground">Members</p>
            <p className="mt-1 text-lg font-semibold tabular-nums">{standardCount}</p>
          </div>
        </div>
      ) : null}

      <div className="flex items-center justify-between">
        <Separator className="flex-1" />
        <Badge variant="outline" className="ml-3 h-7 px-2.5 text-xs text-muted-foreground">
          Organization members
        </Badge>
      </div>

      {isMembersError ? (
        <QueryError
          message="Failed to load members."
          onRetry={() => refetchMembers()}
        />
      ) : isLoadingMembers ? (
        <PageLoading message="Loading members..." />
      ) : members.length === 0 ? (
        <PageEmpty
          title="No members yet"
          description="Invite members to start collaborating in this organization."
        />
      ) : (
        <MembersTable
          members={members}
          currentUserId={currentUser?.id}
          onUpdateRole={(member, newRole) => {
            if (member.role === newRole) {
              return;
            }
            setPendingRoleChange({ member, newRole });
          }}
          onRemove={setMemberToRemove}
          canManage={canManage}
          roleActionsDisabled={updatingRoleMemberId !== null}
          updatingRoleMemberId={updatingRoleMemberId}
        />
      )}

      <AlertDialog
        open={!!memberToRemove}
        onOpenChange={(open) => !open && setMemberToRemove(null)}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>
              Remove {memberToRemove?.user_full_name || memberToRemove?.user_email} from organization?
            </AlertDialogTitle>
            <AlertDialogDescription>
              This will remove{" "}
              {memberToRemove?.user_full_name || memberToRemove?.user_email}{" "}
              from the organization. They will lose access to all projects
              immediately.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={confirmRemoveMember}
              disabled={removeMemberMutation.isPending}
              className="bg-destructive hover:bg-destructive/90"
            >
              {removeMemberMutation.isPending ? "Removing..." : "Remove Member"}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      <AlertDialog
        open={pendingRoleChange !== null}
        onOpenChange={(open) => !open && setPendingRoleChange(null)}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>
              Change role for {pendingRoleChange?.member.user_full_name || pendingRoleChange?.member.user_email}?
            </AlertDialogTitle>
            <AlertDialogDescription>
              This will update their access level to{" "}
              <span className="font-medium text-foreground">{pendingRoleChange?.newRole}</span>.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={confirmRoleChange}
              disabled={updateRoleMutation.isPending}
            >
              {updateRoleMutation.isPending ? "Updating..." : "Confirm role change"}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </PageShell>
  );
}
