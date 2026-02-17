import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { type ReactNode } from "react";
import { useOrganizations, useOrganization } from "./useOrganizations";
import { useProjects } from "@/features/projects/hooks/useProjects";
import { useMyOrgRole } from "./useMyOrgRole";

// Mock services
vi.mock("@/features/organizations/api/organization.service", () => ({
    organizationService: {
        list: vi.fn(),
        get: vi.fn(),
        getMyMembership: vi.fn(),
    },
}));

vi.mock("@/features/projects/api/project.service", () => ({
    projectService: {
        list: vi.fn(),
    },
}));

vi.mock("@/features/organizations/store/org-store", () => ({
    useOrgStore: vi.fn((selector) => selector({ activeOrgId: "org-1" })),
}));

// Import implementations after mocking
import { organizationService } from "@/features/organizations/api/organization.service";
import { projectService } from "@/features/projects/api/project.service";

function createWrapper() {
    const qc = new QueryClient({
        defaultOptions: { queries: { retry: false } },
    });
    return ({ children }: { children: ReactNode }) => (
        <QueryClientProvider client= { qc } > { children } </QueryClientProvider>
  );
}

describe("Data Hooks", () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

    it("useOrganizations — fetches org list", async () => {
        const mockOrgs = [{ id: "1", name: "Org" }];
        (organizationService.list as any).mockResolvedValue(mockOrgs);

        const { result } = renderHook(() => useOrganizations(), { wrapper: createWrapper() });

        await waitFor(() => expect(result.current.isSuccess).toBe(true));
        expect(result.current.data).toEqual(mockOrgs);
    });

    it("useOrganization(id) — fetches single org, disabled when no id", async () => {
        const mockOrg = { id: "1", name: "Org" };
        (organizationService.get as any).mockResolvedValue(mockOrg);

        // Fetch with ID
        const { result, rerender } = renderHook((id) => useOrganization(id), {
            wrapper: createWrapper(),
            initialProps: "1",
        });

        await waitFor(() => expect(result.current.isSuccess).toBe(true));
        expect(result.current.data).toEqual(mockOrg);

        // Fetch with empty ID
        rerender("");
        expect(result.current.isPending).toBe(true); // Should be pending/disabled (or status 'pending' with fetchStatus 'idle')
        // We really want to ensure service.get wasn't called for ""
        expect(organizationService.get).toHaveBeenCalledTimes(1); // Only for "1"
    });

    it("useProjects — fetches projects scoped to activeOrgId", async () => {
        // activeOrgId is "org-1" from mock
        const mockProjs = [{ id: "p1", name: "Proj" }];
        (projectService.list as any).mockResolvedValue(mockProjs);

        const { result } = renderHook(() => useProjects(), { wrapper: createWrapper() });

        await waitFor(() => expect(result.current.isSuccess).toBe(true));
        expect(result.current.data).toEqual(mockProjs);
        expect(projectService.list).toHaveBeenCalledWith("org-1");
    });

    it("useMyOrgRole — returns current user's org role", async () => {
        // activeOrgId is "org-1"
        const mockMembership = { role: "admin" };
        (organizationService.getMyMembership as any).mockResolvedValue(mockMembership);

        // Why? Wait. `useMyOrgRole` implementation:
        // export function useMyOrgRole() {
        //   ... useQuery ...
        //   return { role: membership?.role || null, isLoading };
        // }
        // Wait, `useMyOrgRole.ts` imports `useOrgStore` and gets `activeOrgId`.
        // Then calls `organizationService.getMyMembership(activeOrgId)`.

        const { result } = renderHook(() => useMyOrgRole(), { wrapper: createWrapper() });

        // Since it returns an object { role, isLoading }, we wait for isLoading to be false?
        await waitFor(() => expect(result.current.isLoading).toBe(false));

        expect(result.current.role).toBe("admin");
        expect(organizationService.getMyMembership).toHaveBeenCalledWith("org-1");
    });
});
