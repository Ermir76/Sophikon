import { parseISO } from "date-fns";
import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { InsightsTrendCard } from "@/shared/ui/insights-trend-card";

vi.mock("@/shared/ui/chart", () => ({
  ChartContainer: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  ChartTooltip: () => null,
  ChartTooltipContent: () => null,
}));

vi.mock("recharts", () => ({
  CartesianGrid: () => null,
  Line: () => null,
  LineChart: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  XAxis: ({ tickFormatter }: { tickFormatter: (value: string) => string }) => (
    <div data-testid="trend-tick">{tickFormatter("2026-04-02")}</div>
  ),
  YAxis: () => null,
}));

describe("InsightsTrendCard", () => {
  it("formats date-only trend buckets from local calendar dates", () => {
    render(
      <InsightsTrendCard
        title="Execution Trend"
        data={[
          {
            date: "2026-04-02",
            created_tasks: 1,
            completed_tasks: 0,
            overdue_tasks: 0,
          },
        ]}
      />,
    );

    expect(screen.getByTestId("trend-tick")).toHaveTextContent(
      parseISO("2026-04-02").toLocaleDateString(undefined, {
        month: "short",
        day: "numeric",
      }),
    );
  });
});
