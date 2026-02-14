import type { OrgRole } from "@/types/organization";

export type { OrgRole };

export const ROLES: Record<OrgRole, string> = {
  owner: "Owner",
  admin: "Admin",
  member: "Member",
};

export const ROLE_OPTIONS = Object.entries(ROLES).map(([value, label]) => ({
  value: value as OrgRole,
  label,
}));

export function getRoleLabel(role: OrgRole): string {
  return ROLES[role] || role;
}

export function canManageMembers(role: OrgRole | null): boolean {
  return role === "owner" || role === "admin";
}

export function canManageSettings(role: OrgRole | null): boolean {
  return role === "owner" || role === "admin";
}

export function canDeleteOrg(role: OrgRole | null): boolean {
  return role === "owner";
}
