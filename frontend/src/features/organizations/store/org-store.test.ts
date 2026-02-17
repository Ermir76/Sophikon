import { describe, it, expect, beforeEach } from "vitest";
import { useOrgStore } from "./org-store";
import { useAuthStore } from "@/features/auth/store/auth-store";

describe("Org Store", () => {
    beforeEach(() => {
        localStorage.clear();
        useOrgStore.setState({ activeOrgId: null });
        useAuthStore.setState({ isAuthenticated: false, user: null });
    });

    it("should set active org id", () => {
        const store = useOrgStore.getState();
        store.setActiveOrg("org-123");
        expect(useOrgStore.getState().activeOrgId).toBe("org-123");
    });

    it("should clear active org id", () => {
        useOrgStore.setState({ activeOrgId: "org-123" });
        const store = useOrgStore.getState();
        store.clear();
        expect(useOrgStore.getState().activeOrgId).toBeNull();
    });

    it("should persist active org id to localStorage", () => {
        const store = useOrgStore.getState();
        store.setActiveOrg("org-123");

        const stored = localStorage.getItem("sophikon-org-storage");
        expect(stored).toBeTruthy();
        const parsed = JSON.parse(stored!);
        expect(parsed.state.activeOrgId).toBe("org-123");
    });

    it("should clear on auth logout", () => {
        // Setup authenticated state first and active org
        useAuthStore.setState({ isAuthenticated: true });
        useOrgStore.setState({ activeOrgId: "org-123" });

        // Simulate logout (isAuthenticated: true -> false)
        useAuthStore.setState({ isAuthenticated: false });

        expect(useOrgStore.getState().activeOrgId).toBeNull();
    });
});
