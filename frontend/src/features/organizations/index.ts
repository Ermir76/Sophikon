// Public API for the `organizations` feature
export { OrgSwitcher } from './components/OrgSwitcher';
export { MembersTable } from './components/MembersTable';
export { InviteMemberDialog } from './components/InviteMemberDialog';
export type { InviteFormValues } from './components/InviteMemberDialog';

export {
  useOrganizations,
  useOrganization,
  useUpdateOrganization,
  useDeleteOrganization,
  useOrgMembers,
  useInviteMember,
  useRemoveMember,
  useUpdateMemberRole,
  orgKeys,
} from './hooks/useOrganizations';
export { useMyOrgRole } from './hooks/useMyOrgRole';

export { useOrgStore } from './store/org-store';
export * from './types';
