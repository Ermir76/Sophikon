import { useState } from "react";
import { toast } from "sonner";

import { useAuthStore } from "@/features/auth";
import {
  InviteMemberDialog,
  MembersTable,
  useMyOrgRole,
  useOrgMembers,
  useOrgStore,
  useInviteMember,
  useOrganization,
  useRemoveMember,
  useUpdateMemberRole,
} from "@/features/organizations";
import type { InviteFormValues, OrganizationMember, OrgRole } from "@/features/organizations";
import { QueryError } from "@/shared/components/QueryError";
import { getErrorMessage } from "@/shared/lib/errors";
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
import { Badge } from "@/shared/ui/badge";

export function MembersSection() {
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

  const [memberToRemove, setMemberToRemove] = useState<OrganizationMember | null>(null);
  const [pendingRoleChange, setPendingRoleChange] = useState<{
    member: OrganizationMember;
    newRole: OrgRole;
  } | null>(null);
  const [updatingRoleMemberId, setUpdatingRoleMemberId] = useState<string | null>(null);

  if (!activeOrgId) {
    return (
      <section className="space-y-1">
        <h2 className="text-xl font-semibold text-foreground">Members</h2>
        <p className="text-sm text-muted-foreground">Select an organization to manage members.</p>
      </section>
    );
  }

  const members = membersData?.items ?? [];
  const ownerCount = members.filter((member) => member.role === "owner").length;
  const adminCount = members.filter((member) => member.role === "admin").length;
  const standardCount = members.filter((member) => member.role === "member").length;

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

  return (
    <section className="space-y-5">
      <div className="flex items-start justify-between gap-2">
        <h2 className="text-xl font-semibold text-foreground">Members</h2>
        {canManage ? (
          <InviteMemberDialog
            orgName={activeOrganization?.name}
            onInvite={onInvite}
            isPending={inviteMutation.isPending}
          />
        ) : null}
      </div>
      <p className="text-sm text-muted-foreground">Manage who has access to this organization.</p>
      <div className="space-y-4">
        {!isLoadingMembers && members.length > 0 ? (
          <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
            <div className="rounded-md border px-4 py-3">
              <p className="text-xs uppercase tracking-wide text-muted-foreground">Total</p>
              <p className="mt-1 text-lg font-semibold tabular-nums">{members.length}</p>
            </div>
            <div className="rounded-md border px-4 py-3">
              <p className="text-xs uppercase tracking-wide text-muted-foreground">Owners</p>
              <p className="mt-1 text-lg font-semibold tabular-nums">{ownerCount}</p>
            </div>
            <div className="rounded-md border px-4 py-3">
              <p className="text-xs uppercase tracking-wide text-muted-foreground">Admins</p>
              <p className="mt-1 text-lg font-semibold tabular-nums">{adminCount}</p>
            </div>
            <div className="rounded-md border px-4 py-3">
              <p className="text-xs uppercase tracking-wide text-muted-foreground">Members</p>
              <p className="mt-1 text-lg font-semibold tabular-nums">{standardCount}</p>
            </div>
          </div>
        ) : null}

        <Badge variant="outline" className="h-7 px-2.5 text-xs text-muted-foreground">
          Organization members
        </Badge>

        {isMembersError ? (
          <QueryError message="Failed to load members." onRetry={() => refetchMembers()} />
        ) : isLoadingMembers ? (
          <p className="text-sm text-muted-foreground">Loading members...</p>
        ) : members.length === 0 ? (
          <p className="text-sm text-muted-foreground">No members yet.</p>
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
      </div>

      <AlertDialog open={memberToRemove !== null} onOpenChange={(open) => !open && setMemberToRemove(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>
              Remove {memberToRemove?.user_full_name || memberToRemove?.user_email} from organization?
            </AlertDialogTitle>
            <AlertDialogDescription>
              This will remove the member from the organization and revoke project access immediately.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={async () => {
                if (!memberToRemove) {
                  return;
                }

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
              }}
              disabled={removeMemberMutation.isPending}
              className="bg-destructive hover:bg-destructive/90"
            >
              {removeMemberMutation.isPending ? "Removing..." : "Remove Member"}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      <AlertDialog open={pendingRoleChange !== null} onOpenChange={(open) => !open && setPendingRoleChange(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>
              Change role for {pendingRoleChange?.member.user_full_name || pendingRoleChange?.member.user_email}?
            </AlertDialogTitle>
            <AlertDialogDescription>
              This will update their access level to <span className="font-medium text-foreground">{pendingRoleChange?.newRole}</span>.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={async () => {
                if (!pendingRoleChange) {
                  return;
                }
                await applyRoleChange(pendingRoleChange.member, pendingRoleChange.newRole);
                setPendingRoleChange(null);
              }}
              disabled={updateRoleMutation.isPending}
            >
              {updateRoleMutation.isPending ? "Updating..." : "Confirm role change"}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </section>
  );
}
