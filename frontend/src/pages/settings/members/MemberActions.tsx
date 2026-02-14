import { MoreHorizontal } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
  DropdownMenuSub,
  DropdownMenuSubTrigger,
  DropdownMenuSubContent,
  DropdownMenuRadioGroup,
  DropdownMenuRadioItem,
} from "@/components/ui/dropdown-menu";
import type { OrganizationMember, OrgRole } from "@/types/organization";
import { ROLE_OPTIONS } from "@/lib/roles";

interface MemberActionsProps {
  member: OrganizationMember;
  isCurrentUser: boolean;
  onUpdateRole: (member: OrganizationMember, newRole: OrgRole) => void;
  onRemove: (member: OrganizationMember) => void;
}

export function MemberActions({
  member,
  isCurrentUser,
  onUpdateRole,
  onRemove,
}: MemberActionsProps) {
  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" className="size-8 p-0">
          <span className="sr-only">Open menu</span>
          <MoreHorizontal className="size-4" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        <DropdownMenuLabel>Actions</DropdownMenuLabel>
        <DropdownMenuItem
          onClick={() => {
            if (member.user_email) {
              navigator.clipboard.writeText(member.user_email);
              toast.success("Email copied to clipboard");
            }
          }}
        >
          Copy Email
        </DropdownMenuItem>
        <DropdownMenuSeparator />

        <DropdownMenuSub>
          <DropdownMenuSubTrigger>Change Role</DropdownMenuSubTrigger>
          <DropdownMenuSubContent>
            <DropdownMenuRadioGroup
              value={member.role}
              onValueChange={(val) => onUpdateRole(member, val as OrgRole)}
            >
              {ROLE_OPTIONS.map((role) => (
                <DropdownMenuRadioItem key={role.value} value={role.value}>
                  {role.label}
                </DropdownMenuRadioItem>
              ))}
            </DropdownMenuRadioGroup>
          </DropdownMenuSubContent>
        </DropdownMenuSub>

        <DropdownMenuItem
          className="text-destructive"
          onClick={() => onRemove(member)}
          disabled={isCurrentUser}
        >
          Remove Member
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
