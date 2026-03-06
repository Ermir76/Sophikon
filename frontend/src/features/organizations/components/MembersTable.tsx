import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/shared/ui/table";
import { Badge } from "@/shared/ui/badge";
import type { OrganizationMember, OrgRole } from "@/features/organizations/types";
import { MemberActions } from "./MemberActions";

interface MembersTableProps {
  members: OrganizationMember[];
  currentUserId?: string;
  onUpdateRole: (member: OrganizationMember, newRole: OrgRole) => void;
  onRemove: (member: OrganizationMember) => void;
  canManage: boolean;
}

export function MembersTable({
  members,
  currentUserId,
  onUpdateRole,
  onRemove,
  canManage,
}: MembersTableProps) {
  const getRoleBadgeClass = (role: OrgRole) => {
    if (role === "owner") return "border-destructive/45 bg-destructive/12 text-destructive";
    if (role === "admin") return "border-primary/45 bg-primary/12 text-primary";
    return "border-muted-foreground/30 bg-muted/35 text-muted-foreground";
  };

  return (
    <div className="overflow-hidden rounded-lg border bg-card/70">
      <Table>
        <TableHeader className="sticky top-0 z-20 bg-card/95 backdrop-blur supports-[backdrop-filter]:bg-card/85">
          <TableRow>
            <TableHead>User</TableHead>
            <TableHead>Role</TableHead>
            <TableHead className="w-[76px]"></TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {members.length === 0 ? (
            <TableRow>
              <TableCell colSpan={3} className="h-24 text-center">
                No members found.
              </TableCell>
            </TableRow>
          ) : (
            members.map((member) => (
              <TableRow key={member.id} className="h-11">
                <TableCell>
                  <div className="flex flex-col gap-0.5">
                    <span className="font-medium">
                      {member.user_full_name || "Unknown"}
                    </span>
                    <span className="text-xs text-muted-foreground">
                      {member.user_email || "No Email"}
                    </span>
                  </div>
                </TableCell>
                <TableCell>
                  <Badge variant="outline" className={getRoleBadgeClass(member.role)}>
                    {member.role}
                  </Badge>
                </TableCell>
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
    </div>
  );
}
