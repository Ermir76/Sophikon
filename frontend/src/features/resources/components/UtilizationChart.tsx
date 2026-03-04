import { Loader2, BarChart3 } from "lucide-react";
import {
    BarChart,
    Bar,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    ReferenceLine,
    Legend,
    Cell,
} from "recharts";

export interface UtilizationChartProps {
    chartData: Record<string, unknown>[];
    resourceNames: string[];
    isLoading: boolean;
    resourceColors: string[];
    overAllocatedColor: string;
}

export function UtilizationChart({
    chartData,
    resourceNames,
    isLoading,
    resourceColors,
    overAllocatedColor,
}: UtilizationChartProps) {
    if (isLoading) {
        return (
            <div className="flex justify-center p-12">
                <Loader2 className="size-8 animate-spin text-muted-foreground" />
            </div>
        );
    }

    if (chartData.length === 0) {
        return (
            <div className="flex flex-col items-center justify-center rounded-md border border-dashed p-12 text-center animate-in fade-in-50">
                <div className="mx-auto flex size-12 items-center justify-center rounded-full bg-accent">
                    <BarChart3 className="size-6 text-muted-foreground" />
                </div>
                <h3 className="mt-4 text-lg font-semibold">No utilization data</h3>
                <p className="mb-4 mt-2 text-sm text-muted-foreground">
                    Assign resources to tasks to see their utilization here.
                </p>
            </div>
        );
    }

    return (
        <div className="rounded-lg border bg-card p-4">
            <ResponsiveContainer width="100%" height={400}>
                <BarChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" className="stroke-border/50" />
                    <XAxis
                        dataKey="dateLabel"
                        tick={{ fontSize: 12, fill: "hsl(var(--muted-foreground))" }}
                    />
                    <YAxis
                        tick={{ fontSize: 12, fill: "hsl(var(--muted-foreground))" }}
                        label={{
                            value: "Units",
                            angle: -90,
                            position: "insideLeft",
                            style: { fill: "hsl(var(--muted-foreground))", fontSize: 12 },
                        }}
                    />
                    <Tooltip
                        contentStyle={{
                            backgroundColor: "hsl(var(--card))",
                            border: "1px solid hsl(var(--border))",
                            borderRadius: "8px",
                            fontSize: "12px",
                        }}
                    />
                    <Legend />
                    <ReferenceLine
                        y={1}
                        stroke={overAllocatedColor}
                        strokeDasharray="4 4"
                        strokeWidth={2}
                        label={{
                            value: "Max (100%)",
                            position: "right",
                            style: { fill: overAllocatedColor, fontSize: 11 },
                        }}
                    />
                    {resourceNames.map((name: string, i: number) => (
                        <Bar
                            key={name}
                            dataKey={name}
                            stackId="utilization"
                            fill={resourceColors[i % resourceColors.length]}
                            radius={i === resourceNames.length - 1 ? [4, 4, 0, 0] : [0, 0, 0, 0]}
                        >
                            {chartData.map((entry, index) => (
                                <Cell
                                    key={`cell-${index}`}
                                    opacity={entry._isOverAllocated ? 1 : 0.85}
                                />
                            ))}
                        </Bar>
                    ))}
                </BarChart>
            </ResponsiveContainer>
        </div>
    );
}
