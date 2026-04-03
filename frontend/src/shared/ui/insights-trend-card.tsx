import { parseISO } from "date-fns";
import { Card, CardContent, CardHeader, CardTitle } from "@/shared/ui/card";
import {
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
  type ChartConfig,
} from "@/shared/ui/chart";
import type { TrendPoint } from "@/shared/types/insights";
import { CartesianGrid, Line, LineChart, XAxis, YAxis } from "recharts";
import { cn } from "@/shared/lib/utils";

const chartConfig = {
  created: { label: "Created", color: "var(--chart-2)" },
  completed: { label: "Completed", color: "var(--chart-1)" },
  overdue: { label: "Overdue", color: "var(--destructive)" },
} satisfies ChartConfig;

interface InsightsTrendCardProps {
  title: string;
  data: TrendPoint[];
  className?: string;
  chartClassName?: string;
  contentClassName?: string;
}

export function InsightsTrendCard({
  title,
  data,
  className,
  chartClassName,
  contentClassName,
}: InsightsTrendCardProps) {
  return (
    <Card className={cn("py-4", className)}>
      <CardHeader className="px-4">
        <CardTitle className="text-sm font-semibold">{title}</CardTitle>
      </CardHeader>
      <CardContent className={cn("px-2", contentClassName)}>
        <ChartContainer config={chartConfig} className={cn("h-[280px] w-full", chartClassName)}>
          <LineChart data={data} margin={{ left: 6, right: 10, top: 8, bottom: 4 }}>
            <CartesianGrid vertical={false} stroke="var(--border)" strokeOpacity={0.45} />
            <XAxis
              dataKey="date"
              tickLine={false}
              axisLine={false}
              tick={{ fill: "var(--muted-foreground)", fontSize: 11 }}
              minTickGap={24}
              tickFormatter={(v: string) =>
                parseISO(v).toLocaleDateString(undefined, { month: "short", day: "numeric" })}
            />
            <YAxis allowDecimals={false} width={30} tick={{ fill: "var(--muted-foreground)", fontSize: 11 }} />
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
              strokeWidth={2.25}
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
