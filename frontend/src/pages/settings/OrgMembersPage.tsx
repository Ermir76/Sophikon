import { useState } from "react";
import { toast } from "sonner";
import { Separator } from "@/components/ui/separator";
import { Card, CardContent } from "@/components/ui/card";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { useOrgStore } from "@/store/org-store";
import { useAuthStore } from "@/store/auth-store";
import type { OrganizationMember, OrgRole } from "@/types/organization";
import {
  useOrgMembers,
  useInviteMember,
  useRemoveMember,
  useUpdateMemberRole,
  useOrganization,
} from "@/hooks/useOrganizations";
import { QueryError } from "@/components/QueryError";
import { MembersTable } from "./members/MembersTable";
import {
  InviteMemberDialog,
  type InviteFormValues,
} from "./members/InviteMemberDialog";

export default function OrgMembersPage() {
  const activeOrgId = useOrgStore((state) => state.activeOrgId);
  const currentUser = useAuthStore((state) => state.user);

  const { data: activeOrganization } = useOrganization(activeOrgId || "");
  const {
    data: membersData,
    isLoading: isLoadingMembers,
    isError: isMembersError,
    refetch: refetchMembers,
  } = useOrgMembers(activeOrgId || "");

  const inviteMutation = useInviteMember(activeOrgId || "");
  const removeMemberMutation = useRemoveMember(activeOrgId || "");
  const updateRoleMutation = useUpdateMemberRole(activeOrgId || "");

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
        description: "Failed to invite member.",
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
        description: "Failed to remove member.",
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
        description: "Failed to update member role.",
      });
    }
  };

  const members = membersData?.items || [];

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-2xl font-medium">Members</h3>
          <p className="text-sm text-muted-foreground">
            Manage who has access to this organization.
          </p>
        </div>
        <InviteMemberDialog
          orgName={activeOrganization?.name}
          onInvite={onInvite}
          isPending={inviteMutation.isPending}
        />
      </div>

      <Separator />

      {isMembersError ? (
        <QueryError
          message="Failed to load members."
          onRetry={() => refetchMembers()}
        />
      ) : (
        <Card>
          <CardContent className="p-0">
            <MembersTable
              members={members}
              isLoading={isLoadingMembers}
              currentUserId={currentUser?.id}
              onUpdateRole={onUpdateRole}
              onRemove={setMemberToRemove}
            />
          </CardContent>
        </Card>
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
    </div>
  );
}
