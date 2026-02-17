import { create } from "zustand";
import { persist } from "zustand/middleware";
import { useAuthStore } from "@/features/auth/store/auth-store";

interface OrgState {
  activeOrgId: string | null;

  setActiveOrg: (orgId: string) => void;
  clear: () => void;
}

export const useOrgStore = create<OrgState>()(
  persist(
    (set) => ({
      activeOrgId: null,

      setActiveOrg: (orgId: string) => {
        set({ activeOrgId: orgId });
      },

      clear: () => {
        set({
          activeOrgId: null,
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
  if (!state.isAuthenticated && prevState.isAuthenticated) {
    useOrgStore.getState().clear();
  }
});
