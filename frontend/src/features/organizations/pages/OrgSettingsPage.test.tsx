import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { ReactNode } from "react";
import { MemoryRouter } from "react-router";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { toast } from "sonner";

import OrgSettingsPage from "@/features/organizations/pages/OrgSettingsPage";

const mocks = vi.hoisted(() => ({
  navigate: vi.fn(),
  setActiveOrg: vi.fn(),
  clearOrg: vi.fn(),
  deleteOrgMutate: vi.fn(),
  activeOrganization: {
    id: "org-active",
    name: "Active Org",
    slug: "active-org",
    is_personal: false,
    created_at: "2026-03-24T00:00:00Z",
    updated_at: "2026-03-24T00:00:00Z",
  },
  organizationsData: {
    items: [
      {
        id: "org-active",
        name: "Active Org",
        slug: "active-org",
        is_personal: false,
        created_at: "2026-03-24T00:00:00Z",
        updated_at: "2026-03-24T00:00:00Z",
      },
      {
        id: "org-personal",
        name: "Personal Org",
        slug: "personal-org",
        is_personal: true,
        created_at: "2026-03-24T00:00:00Z",
        updated_at: "2026-03-24T00:00:00Z",
      },
    ],
  },
  refetch: vi.fn(),
  updateOrgMutateAsync: vi.fn(),
}));

vi.mock("react-router", async () => {
  const actual = await vi.importActual<typeof import("react-router")>("react-router");
  return {
    ...actual,
    useNavigate: () => mocks.navigate,
  };
});

vi.mock("sonner", () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
  },
}));

vi.mock("@/shared/ui/alert-dialog", () => ({
  AlertDialog: ({
    children,
    open,
  }: {
    children: ReactNode;
    open?: boolean;
    onOpenChange?: (open: boolean) => void;
  }) => <div>{open ? children : null}</div>,
  AlertDialogContent: ({
    children,
  }: {
    children: ReactNode;
    variant?: string;
  }) => <div role="alertdialog">{children}</div>,
  AlertDialogHeader: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  AlertDialogTitle: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  AlertDialogDescription: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  AlertDialogFooter: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  AlertDialogCancel: ({ children }: { children: ReactNode }) => (
    <button type="button">{children}</button>
  ),
  AlertDialogAction: ({
    children,
    onClick,
    disabled,
  }: {
    children: ReactNode;
    onClick?: () => void;
    disabled?: boolean;
    variant?: string;
  }) => (
    <button type="button" onClick={onClick} disabled={disabled}>
      {children}
    </button>
  ),
}));

vi.mock("@/shared/components/layout/PageShell", () => ({
  PageShell: ({ children }: { children: ReactNode; className?: string }) => <div>{children}</div>,
}));

vi.mock("@/shared/components/layout/PageHeader", () => ({
  PageHeader: ({
    title,
    description,
  }: {
    title: string;
    description?: string;
  }) => (
    <div>
      <h1>{title}</h1>
      {description ? <p>{description}</p> : null}
    </div>
  ),
}));

vi.mock("@/shared/components/state/PageLoading", () => ({
  PageLoading: ({ message }: { message: string }) => <div>{message}</div>,
}));

vi.mock("@/shared/components/QueryError", () => ({
  QueryError: ({ message }: { message: string; onRetry?: () => void }) => <div>{message}</div>,
}));

vi.mock("@/shared/ui/button", () => ({
  Button: ({
    children,
    onClick,
    disabled,
    type = "button",
  }: {
    children: ReactNode;
    onClick?: () => void;
    disabled?: boolean;
    type?: "button" | "submit" | "reset";
    variant?: string;
    size?: string;
    className?: string;
  }) => (
    <button type={type} onClick={onClick} disabled={disabled}>
      {children}
    </button>
  ),
}));

vi.mock("@/shared/ui/separator", () => ({
  Separator: () => <hr />,
}));

vi.mock("@/shared/ui/card", () => ({
  Card: ({ children }: { children: ReactNode; className?: string }) => <div>{children}</div>,
  CardHeader: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  CardTitle: ({ children }: { children: ReactNode; className?: string }) => <div>{children}</div>,
  CardDescription: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  CardContent: ({ children }: { children: ReactNode }) => <div>{children}</div>,
}));

vi.mock("@/shared/ui/form", () => ({
  Form: ({ children }: { children: ReactNode }) => <>{children}</>,
  FormField: ({
    render,
    name,
  }: {
    render: (props: {
      field: {
        name: string;
        value: string;
        onChange: () => void;
        onBlur: () => void;
        ref: () => void;
      };
    }) => ReactNode;
    name: string;
    control: unknown;
  }) =>
    render({
      field: {
        name,
        value: "",
        onChange: () => {},
        onBlur: () => {},
        ref: () => {},
      },
    }),
  FormItem: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  FormLabel: ({ children }: { children: ReactNode }) => <label>{children}</label>,
  FormControl: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  FormMessage: () => null,
}));

vi.mock("@/shared/ui/input", () => ({
  Input: ({
    placeholder,
    ...props
  }: {
    placeholder?: string;
    [key: string]: unknown;
  }) => <input placeholder={placeholder} {...props} />,
}));

vi.mock("@/features/organizations/store/org-store", () => ({
  useOrgStore: vi.fn((selector: (state: unknown) => unknown) =>
    selector({
      activeOrgId: "org-active",
      setActiveOrg: mocks.setActiveOrg,
      clear: mocks.clearOrg,
    })),
}));

vi.mock("@/features/organizations/hooks/useOrganizations", () => ({
  useOrganizations: vi.fn(() => ({
    data: mocks.organizationsData,
  })),
  useOrganization: vi.fn(() => ({
    data: mocks.activeOrganization,
    isLoading: false,
    isError: false,
    refetch: mocks.refetch,
  })),
  useUpdateOrganization: vi.fn(() => ({
    mutateAsync: mocks.updateOrgMutateAsync,
    isPending: false,
  })),
  useDeleteOrganization: vi.fn(() => ({
    mutate: mocks.deleteOrgMutate,
    isPending: false,
  })),
}));

describe("OrgSettingsPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    globalThis.ResizeObserver = class ResizeObserver {
      observe() {}
      unobserve() {}
      disconnect() {}
    };
  });

  it("falls back to the personal organization after deleting the active org", async () => {
    const user = userEvent.setup();
    mocks.deleteOrgMutate.mockImplementation(
      (_orgId: string, options?: { onSuccess?: () => void }) => {
        options?.onSuccess?.();
      },
    );

    render(
      <MemoryRouter>
        <OrgSettingsPage />
      </MemoryRouter>,
    );

    await user.click(screen.getByRole("button", { name: "Delete Organization" }));

    const deleteButtons = screen.getAllByRole("button", { name: "Delete Organization" });
    await user.click(deleteButtons[1]!);

    expect(mocks.deleteOrgMutate).toHaveBeenCalledWith(
      "org-active",
      expect.objectContaining({
        onSuccess: expect.any(Function),
        onError: expect.any(Function),
      }),
    );
    expect(mocks.setActiveOrg).toHaveBeenCalledWith("org-personal");
    expect(mocks.clearOrg).not.toHaveBeenCalled();
    expect(mocks.navigate).toHaveBeenCalledWith("/");
    expect(toast.success).toHaveBeenCalledWith("Organization deleted", {
      description: "The organization has been permanently deleted.",
    });
  });
});
