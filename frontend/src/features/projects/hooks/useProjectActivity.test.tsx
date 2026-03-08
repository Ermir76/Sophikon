import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { renderHook, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { useProjectActivity } from "@/features/projects/hooks/useProjectActivity";

vi.mock("@/features/projects/api/project-activity.service", () => ({
  projectActivityService: {
    list: vi.fn(),
  },
}));

import { projectActivityService } from "@/features/projects/api/project-activity.service";

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });

  return ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
}

describe("useProjectActivity", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("fetches project activity with the default overview filters", async () => {
    vi.mocked(projectActivityService.list).mockResolvedValue({
      items: [],
      total: 0,
      page: 1,
      per_page: 20,
      total_pages: 0,
    });

    const { result } = renderHook(() => useProjectActivity("project-1"), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(projectActivityService.list).toHaveBeenCalledWith("project-1", {
      page: 1,
      per_page: 20,
      user_id: undefined,
      entity_type: undefined,
      action: undefined,
    });
  });
});
