import { useOrgMembers } from "./useOrganizations";
import { useAuthStore } from "@/store/auth-store";
import { useOrgStore } from "@/store/org-store";

export function useMyOrgRole() {
  const activeOrgId = useOrgStore((state) => state.activeOrgId);
  const user = useAuthStore((state) => state.user);

  const { data: members, isLoading } = useOrgMembers(activeOrgId || "");

  if (!activeOrgId || !user || !members) {
    return { role: null, isLoading };
  }

  const me = members.items.find((m) => m.user_id === user.id);
  return { role: me?.role || null, isLoading };
}
