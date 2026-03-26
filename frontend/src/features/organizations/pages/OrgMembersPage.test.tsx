import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { ReactNode } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import OrgMembersPage from "@/features/organizations/pages/OrgMembersPage";

const mockUpdateRoleMutateAsync = vi.fn();
const mockRemoveMemberMutateAsync = vi.fn();

const member = {
  id: "member-1",
  organization_id: "org-1",
  user_id: "user-2",
  user_full_name: "Jane Doe",
  user_email: "jane@example.com",
  role: "member" as const,
  joined_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
};

vi.mock("@/features/organizations/store/org-store", () => ({
  useOrgStore: (selector: (state: { activeOrgId: string }) => string) => selector({
    activeOrgId: "org-1",
  }),
}));

vi.mock("@/features/auth", () => ({
  useAuthStore: (selector: (state: { user: { id: string } }) => { id: string }) => selector({
    user: { id: "user-1" },
  }),
}));

vi.mock("@/features/organizations/hooks/useMyOrgRole", () => ({
  useMyOrgRole: () => ({ role: "owner" }),
}));

vi.mock("@/features/organizations/hooks/useOrganizations", () => ({
  useOrganization: () => ({ data: { id: "org-1", name: "Acme" } }),
  useOrgMembers: () => ({
    data: { items: [member] },
    isLoading: false,
    isError: false,
    refetch: vi.fn(),
  }),
  useInviteMember: () => ({
    mutateAsync: vi.fn(),
    isPending: false,
  }),
  useRemoveMember: () => ({
    mutateAsync: mockRemoveMemberMutateAsync,
    isPending: false,
  }),
  useUpdateMemberRole: () => ({
    mutateAsync: mockUpdateRoleMutateAsync,
    isPending: false,
  }),
}));

vi.mock("@/features/organizations/components/InviteMemberDialog", () => ({
  InviteMemberDialog: () => <button type="button">Invite Member</button>,
}));

vi.mock("@/features/organizations/components/MembersTable", () => ({
  MembersTable: ({
    onUpdateRole,
    onRemove,
  }: {
    onUpdateRole: (nextMember: typeof member, nextRole: "owner" | "admin" | "member") => void;
    onRemove: (nextMember: typeof member) => void;
  }) => (
    <div>
      <button
        type="button"
        onClick={() => onUpdateRole(member, "admin")}
      >
        Trigger role change
      </button>
      <button
        type="button"
        onClick={() => onRemove(member)}
      >
        Trigger remove member
      </button>
    </div>
  ),
}));

vi.mock("@/shared/components/layout/PageShell", () => ({
  PageShell: ({ children }: { children: ReactNode }) => <div>{children}</div>,
}));

vi.mock("@/shared/components/layout/PageHeader", () => ({
  PageHeader: ({ title, description, action }: { title: string; description: string; action?: ReactNode }) => (
    <div>
      <h1>{title}</h1>
      <p>{description}</p>
      {action}
    </div>
  ),
}));

vi.mock("@/shared/components/state/PageLoading", () => ({
  PageLoading: ({ message }: { message: string }) => <div>{message}</div>,
}));

vi.mock("@/shared/components/state/PageEmpty", () => ({
  PageEmpty: ({ title, description }: { title: string; description: string }) => (
    <div>
      <p>{title}</p>
      <p>{description}</p>
    </div>
  ),
}));

vi.mock("@/shared/ui/alert-dialog", () => ({
  AlertDialog: ({ open, children }: { open: boolean; children: ReactNode }) => (open ? <div>{children}</div> : null),
  AlertDialogContent: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  AlertDialogHeader: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  AlertDialogTitle: ({ children }: { children: ReactNode }) => <h2>{children}</h2>,
  AlertDialogDescription: ({ children }: { children: ReactNode }) => <p>{children}</p>,
  AlertDialogFooter: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  AlertDialogCancel: ({ children }: { children: ReactNode }) => <button type="button">{children}</button>,
  AlertDialogAction: ({
    children,
    onClick,
  }: {
    children: ReactNode;
    onClick?: () => void;
  }) => (
    <button type="button" onClick={onClick}>
      {children}
    </button>
  ),
}));

describe("OrgMembersPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("requires explicit confirmation before applying a role change", async () => {
    const user = userEvent.setup();
    mockUpdateRoleMutateAsync.mockResolvedValue({});

    render(<OrgMembersPage />);

    await user.click(screen.getByRole("button", { name: "Trigger role change" }));

    expect(screen.getByText("Change role for Jane Doe?")).toBeInTheDocument();
    expect(mockUpdateRoleMutateAsync).not.toHaveBeenCalled();

    await user.click(screen.getByRole("button", { name: "Confirm role change" }));

    expect(mockUpdateRoleMutateAsync).toHaveBeenCalledWith({
      memberId: "member-1",
      data: { role: "admin" },
    });
  });

  it("uses a member-specific removal confirmation title", async () => {
    const user = userEvent.setup();
    mockRemoveMemberMutateAsync.mockResolvedValue({});

    render(<OrgMembersPage />);

    await user.click(screen.getByRole("button", { name: "Trigger remove member" }));

    expect(
      screen.getByText("Remove Jane Doe from organization?"),
    ).toBeInTheDocument();
  });
});
