import { create } from "zustand";
import { persist } from "zustand/middleware";
import { organizationService } from "@/services/organization";
import type { Organization, OrgRole } from "@/types/organization";
import { useAuthStore } from "./auth-store";

interface OrgState {
  organizations: Organization[];
  activeOrganization: Organization | null;
  activeOrgId: string | null;
  currentRole: OrgRole | null;
  isLoading: boolean;
  error: string | null;

  fetchOrgs: () => Promise<void>;
  setActiveOrg: (orgId: string) => Promise<void>;
  clear: () => void;
}

export const useOrgStore = create<OrgState>()(
  persist(
    (set, get) => ({
      organizations: [],
      activeOrganization: null,
      activeOrgId: null,
      currentRole: null,
      isLoading: false,
      error: null,

      fetchOrgs: async () => {
        set({ isLoading: true, error: null });
        try {
          const response = await organizationService.list(1, 100);
          const orgs = response.items;
          const currentId = get().activeOrgId;

          let activeOrg: Organization | null = null;
          if (currentId) {
            activeOrg = orgs.find((o) => o.id === currentId) || null;
          }
          if (!activeOrg && orgs.length > 0) {
            activeOrg = orgs[0];
          }

          set({
            organizations: orgs,
            activeOrganization: activeOrg,
            activeOrgId: activeOrg?.id || null,
            isLoading: false,
          });

          if (activeOrg) {
            const user = useAuthStore.getState().user;
            if (user) {
              const membersRes = await organizationService.listMembers(
                activeOrg.id,
              );
              const me = membersRes.items.find((m) => m.user_id === user.id);
              set({ currentRole: me?.role || null });
            }
          } else {
            set({ currentRole: null });
          }
        } catch (error) {
          console.error("Failed to fetch organizations", error);
          set({ isLoading: false, error: "Failed to fetch organizations" });
        }
      },

      setActiveOrg: async (orgId: string) => {
        const org = get().organizations.find((o) => o.id === orgId) || null;
        // Reset role immediately when switching context
        set({
          activeOrganization: org,
          activeOrgId: orgId,
          currentRole: null,
        });

        if (org) {
          const user = useAuthStore.getState().user;
          if (user) {
            try {
              const membersRes = await organizationService.listMembers(org.id);
              const me = membersRes.items.find((m) => m.user_id === user.id);
              set({ currentRole: me?.role || null });
            } catch (e) {
              console.error("Failed to fetch role for new org", e);
            }
          }
        }
      },

      clear: () => {
        set({
          organizations: [],
          activeOrganization: null,
          activeOrgId: null,
          currentRole: null,
          error: null,
        });
      },
    }),
    {
      name: "sophikon-org-storage",
      partialize: (state) => ({ activeOrgId: state.activeOrgId }),
    },
  ),
);

useAuthStore.subscribe((state, prevState) => {
  if (state.token && !prevState.token) {
    void useOrgStore.getState().fetchOrgs();
  } else if (!state.token && prevState.token) {
    useOrgStore.getState().clear();
  }
});
