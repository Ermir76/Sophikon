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

  const onUpdateRole = async (member: OrganizationMember, newRole: OrgRole) => {
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
    }
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
        <div className="grid gap-2 sm:grid-cols-2 xl:grid-cols-4">
          <div className="rounded-md border bg-card/70 px-3 py-2">
            <p className="text-[10px] uppercase tracking-wide text-muted-foreground">Total</p>
            <p className="mt-1 text-lg font-semibold tabular-nums">{members.length}</p>
          </div>
          <div className="rounded-md border bg-card/70 px-3 py-2">
            <p className="text-[10px] uppercase tracking-wide text-muted-foreground">Owners</p>
            <p className="mt-1 text-lg font-semibold tabular-nums text-destructive">{ownerCount}</p>
          </div>
          <div className="rounded-md border bg-card/70 px-3 py-2">
            <p className="text-[10px] uppercase tracking-wide text-muted-foreground">Admins</p>
            <p className="mt-1 text-lg font-semibold tabular-nums text-primary">{adminCount}</p>
          </div>
          <div className="rounded-md border bg-card/70 px-3 py-2">
            <p className="text-[10px] uppercase tracking-wide text-muted-foreground">Members</p>
            <p className="mt-1 text-lg font-semibold tabular-nums text-muted-foreground">{standardCount}</p>
          </div>
        </div>
      ) : null}

      <div className="flex items-center justify-between">
        <Separator className="flex-1" />
        <Badge variant="outline" className="ml-3 h-7 px-2.5 text-[11px] text-muted-foreground">
          Access list
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
          onUpdateRole={onUpdateRole}
          onRemove={setMemberToRemove}
          canManage={canManage}
        />
      )}

      <AlertDialog
        open={!!memberToRemove}
        onOpenChange={(open) => !open && setMemberToRemove(null)}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Are you sure?</AlertDialogTitle>
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
    </PageShell>
  );
}
