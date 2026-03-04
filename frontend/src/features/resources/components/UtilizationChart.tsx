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
    resourceColors: string[];
    overAllocatedColor: string;
}

export function UtilizationChart({
    chartData,
    resourceNames,
    resourceColors,
    overAllocatedColor,
}: UtilizationChartProps) {
    return (
        <div className="rounded-lg border bg-card p-4">
            <ResponsiveContainer width="100%" height={400}>
                <BarChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" className="stroke-border/50" />
                    <XAxis
                        dataKey="dateLabel"
                        tick={{ fontSize: 12, fill: "var(--muted-foreground)" }}
                    />
                    <YAxis
                        tick={{ fontSize: 12, fill: "var(--muted-foreground)" }}
                        label={{
                            value: "Units",
                            angle: -90,
                            position: "insideLeft",
                            style: { fill: "var(--muted-foreground)", fontSize: 12 },
                        }}
                    />
                    <Tooltip
                        contentStyle={{
                            backgroundColor: "var(--card)",
                            border: "1px solid var(--border)",
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
