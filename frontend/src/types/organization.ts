export type OrgRole = "owner" | "admin" | "member";

export interface Organization {
  id: string;
  name: string;
  slug: string;
  is_personal: boolean;
  settings?: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface OrganizationMember {
  id: string;
  organization_id: string;
  user_id: string;
  role: OrgRole;
  joined_at: string;
  updated_at: string;
  user_email?: string;
  user_full_name?: string;
}

export interface OrganizationCreate {
  name: string;
  slug: string;
}

export interface OrganizationUpdate {
  name?: string;
  slug?: string;
  settings?: Record<string, any>;
}

export interface InviteMemberRequest {
  email: string;
  role: OrgRole;
}

export interface UpdateMemberRoleRequest {
  role: OrgRole;
}

export interface OrgMemberInvite {
  email: string;
  role: OrgRole;
}

export interface OrgMemberRoleUpdate {
  role: OrgRole;
}
