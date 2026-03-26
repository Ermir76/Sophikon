import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { MembersTable } from "@/features/organizations/components/MembersTable";

vi.mock("@/features/organizations/components/MemberActions", () => ({
  MemberActions: ({
    isRoleUpdatePending,
  }: {
    isRoleUpdatePending?: boolean;
  }) => (
    <button disabled={isRoleUpdatePending} type="button">
      Open menu
    </button>
  ),
}));

describe("MembersTable", () => {
  it("shows a stable pending state for the member being updated", () => {
    render(
      <MembersTable
        members={[
          {
            id: "member-1",
            organization_id: "org-1",
            user_id: "user-1",
            user_full_name: "Jane Doe",
            user_email: "jane@example.com",
            role: "member",
            joined_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
          },
        ]}
        currentUserId="user-2"
        onUpdateRole={vi.fn()}
        onRemove={vi.fn()}
        canManage
        updatingRoleMemberId="member-1"
      />,
    );

    expect(screen.getByRole("columnheader", { name: "Actions" })).toBeInTheDocument();
    expect(screen.getByText("Saving...")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Open menu" })).toBeDisabled();
  });
});
