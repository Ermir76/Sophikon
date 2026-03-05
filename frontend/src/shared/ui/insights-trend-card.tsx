import { Card, CardContent, CardHeader, CardTitle } from "@/shared/ui/card";
import {
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
  type ChartConfig,
} from "@/shared/ui/chart";
import type { TrendPoint } from "@/shared/types/insights";
import { CartesianGrid, Line, LineChart, XAxis, YAxis } from "recharts";

const chartConfig = {
  created: { label: "Created", color: "var(--chart-2)" },
  completed: { label: "Completed", color: "var(--chart-1)" },
  overdue: { label: "Overdue", color: "var(--destructive)" },
} satisfies ChartConfig;

interface InsightsTrendCardProps {
  title: string;
  data: TrendPoint[];
}

export function InsightsTrendCard({ title, data }: InsightsTrendCardProps) {
  return (
    <Card className="py-4">
      <CardHeader className="px-4">
        <CardTitle className="text-sm font-semibold">{title}</CardTitle>
      </CardHeader>
      <CardContent className="px-2">
        <ChartContainer config={chartConfig} className="h-[280px] w-full">
          <LineChart data={data} margin={{ left: 6, right: 10, top: 8, bottom: 4 }}>
            <CartesianGrid vertical={false} />
            <XAxis
              dataKey="date"
              tickLine={false}
              axisLine={false}
              minTickGap={24}
              tickFormatter={(v: string) => new Date(v).toLocaleDateString(undefined, { month: "short", day: "numeric" })}
            />
            <YAxis allowDecimals={false} width={28} />
            <ChartTooltip content={<ChartTooltipContent />} />
            <Line
              dataKey="created_tasks"
              name="created"
              stroke="var(--color-created)"
              strokeWidth={2}
              dot={false}
              type="monotone"
            />
            <Line
              dataKey="completed_tasks"
              name="completed"
              stroke="var(--color-completed)"
              strokeWidth={2}
              dot={false}
              type="monotone"
            />
            <Line
              dataKey="overdue_tasks"
              name="overdue"
              stroke="var(--color-overdue)"
              strokeWidth={2}
              dot={false}
              type="monotone"
            />
          </LineChart>
        </ChartContainer>
      </CardContent>
    </Card>
  );
}
