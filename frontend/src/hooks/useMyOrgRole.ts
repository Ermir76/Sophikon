import { useQuery } from "@tanstack/react-query";
import { organizationService } from "@/services/organization";
import { orgKeys } from "./useOrganizations";
import { useOrgStore } from "@/store/org-store";

export function useMyOrgRole() {
  const activeOrgId = useOrgStore((state) => state.activeOrgId);

  const { data: membership, isLoading } = useQuery({
    queryKey: orgKeys.myMembership(activeOrgId || ""),
    queryFn: () => organizationService.getMyMembership(activeOrgId || ""),
    enabled: !!activeOrgId,
  });

  return { role: membership?.role || null, isLoading };
}
