import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import { beforeEach, describe, expect, it, vi } from "vitest";

import SettingsPage from "@/features/settings/pages/SettingsPage";

const mocks = vi.hoisted(() => ({
  role: "admin" as "admin" | "owner" | "member" | null,
}));

vi.mock("@/features/settings/hooks/useActiveSection", () => ({
  useActiveSection: vi.fn(() => "profile"),
}));

vi.mock("@/features/organizations", () => ({
  useMyOrgRole: vi.fn(() => ({
    role: mocks.role,
    isLoading: false,
  })),
}));

vi.mock("@/features/settings/components/sections/ProfileSection", () => ({
  ProfileSection: () => <section><h2>Profile</h2></section>,
}));

vi.mock("@/features/settings/components/sections/SecuritySection", () => ({
  SecuritySection: () => <section><h2>Security</h2></section>,
}));

vi.mock("@/features/settings/components/sections/NotificationsSection", () => ({
  NotificationsSection: () => <section><h2>Notifications</h2></section>,
}));

vi.mock("@/features/settings/components/sections/AiPreferencesSection", () => ({
  AiPreferencesSection: () => <section><h2>AI Preferences</h2></section>,
}));

vi.mock("@/features/settings/components/sections/GeneralSection", () => ({
  GeneralSection: () => (
    <section>
      <h2>General</h2>
      <p>Select an organization to manage organization settings.</p>
    </section>
  ),
}));

vi.mock("@/features/settings/components/sections/MembersSection", () => ({
  MembersSection: () => (
    <section>
      <h2>Members</h2>
      <p>Select an organization to manage members.</p>
    </section>
  ),
}));

vi.mock("@/features/settings/components/sections/BillingSection", () => ({
  BillingSection: () => <section><h2>Billing</h2></section>,
}));

describe("SettingsPage", () => {
  beforeEach(() => {
    mocks.role = "admin";
    Element.prototype.scrollIntoView = vi.fn();
  });

  function renderSettingsPage() {
    return render(
      <MemoryRouter>
        <SettingsPage />
      </MemoryRouter>,
    );
  }

  it("renders the anchor nav and core settings sections", () => {
    renderSettingsPage();

    expect(screen.getAllByRole("navigation", { name: "Settings sections" }).length).toBeGreaterThan(0);
    expect(screen.getByRole("heading", { name: "Profile" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Security" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Notifications" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "AI Preferences" })).toBeInTheDocument();
  });

  it("shows org section empty states when admin routes include org sections", () => {
    renderSettingsPage();

    expect(screen.getByText("Select an organization to manage organization settings.")).toBeInTheDocument();
    expect(screen.getByText("Select an organization to manage members.")).toBeInTheDocument();
  });

  it("hides general and members sections for non-admin users", () => {
    mocks.role = "member";

    renderSettingsPage();

    expect(screen.queryByRole("heading", { name: "General" })).not.toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: "Members" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "General" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Members" })).not.toBeInTheDocument();
  });
});
