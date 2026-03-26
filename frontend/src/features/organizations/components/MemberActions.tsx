import { Loader2, MoreHorizontal } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/shared/ui/button";
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
} from "@/shared/ui/dropdown-menu";
import type { OrganizationMember, OrgRole } from "@/features/organizations/types";
import { ROLE_OPTIONS } from "@/shared/lib/roles";

interface MemberActionsProps {
  member: OrganizationMember;
  isCurrentUser: boolean;
  onUpdateRole: (member: OrganizationMember, newRole: OrgRole) => void;
  onRemove: (member: OrganizationMember) => void;
  canManage: boolean;
  actionsDisabled?: boolean;
  isRoleUpdatePending?: boolean;
}

export function MemberActions({
  member,
  isCurrentUser,
  onUpdateRole,
  onRemove,
  canManage,
  actionsDisabled = false,
  isRoleUpdatePending = false,
}: MemberActionsProps) {
  const isDisabled = actionsDisabled || isRoleUpdatePending;

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant="ghost"
          size="icon"
          className="size-9 p-0"
          disabled={isDisabled}
        >
          <span className="sr-only">
            {isRoleUpdatePending
              ? `Saving role for ${member.user_full_name || member.user_email}`
              : `Open actions for ${member.user_full_name || member.user_email}`}
          </span>
          {isRoleUpdatePending ? (
            <Loader2 className="size-4 animate-spin" />
          ) : (
            <MoreHorizontal className="size-4" />
          )}
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

        {canManage && (
          <>
            <DropdownMenuSeparator />

            <DropdownMenuSub>
              <DropdownMenuSubTrigger>Change role</DropdownMenuSubTrigger>
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
              Remove from organization
            </DropdownMenuItem>
          </>
        )}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
