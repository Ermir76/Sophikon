import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/shared/ui/table";
import { Loader2 } from "lucide-react";
import type { OrganizationMember, OrgRole } from "@/features/organizations/types";
import { MemberActions } from "./MemberActions";

interface MembersTableProps {
  members: OrganizationMember[];
  isLoading: boolean;
  currentUserId?: string;
  onUpdateRole: (member: OrganizationMember, newRole: OrgRole) => void;
  onRemove: (member: OrganizationMember) => void;
  canManage: boolean;
}

export function MembersTable({
  members,
  isLoading,
  currentUserId,
  onUpdateRole,
  onRemove,
  canManage,
}: MembersTableProps) {
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>User</TableHead>
          <TableHead>Role</TableHead>
          <TableHead className="w-[100px]"></TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {isLoading ? (
          <TableRow>
            <TableCell colSpan={3} className="h-24 text-center">
              <Loader2 className="mx-auto size-6 animate-spin" />
            </TableCell>
          </TableRow>
        ) : members.length === 0 ? (
          <TableRow>
            <TableCell colSpan={3} className="h-24 text-center">
              No members found.
            </TableCell>
          </TableRow>
        ) : (
          members.map((member) => (
            <TableRow key={member.id}>
              <TableCell>
                <div className="flex flex-col">
                  <span className="font-medium">
                    {member.user_full_name || "Unknown"}
                  </span>
                  <span className="text-xs text-muted-foreground">
                    {member.user_email || "No Email"}
                  </span>
                </div>
              </TableCell>
              <TableCell className="capitalize">{member.role}</TableCell>
              <TableCell>
                <MemberActions
                  member={member}
                  isCurrentUser={member.user_id === currentUserId}
                  onUpdateRole={onUpdateRole}
                  onRemove={onRemove}
                  canManage={canManage}
                />
              </TableCell>
            </TableRow>
          ))
        )}
      </TableBody>
    </Table>
  );
}
