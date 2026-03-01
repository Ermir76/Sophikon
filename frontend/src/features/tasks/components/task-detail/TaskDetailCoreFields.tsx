import { Input } from "@/shared/ui/input";
import { Textarea } from "@/shared/ui/textarea";
import { ColorPicker } from "@/shared/components/ColorPicker";
import type { Task, TaskUpdate } from "@/features/tasks/types";

interface TaskDetailCoreFieldsProps {
    task: Task;
    localData: Partial<TaskUpdate>;
    setLocalData: (data: Partial<TaskUpdate>) => void;
    handleBlur: (field: keyof TaskUpdate) => void;
    onColorChange?: (color: string | null) => void;
}

export function TaskDetailCoreFields({
    task,
    localData,
    setLocalData,
    handleBlur,
    onColorChange,
}: TaskDetailCoreFieldsProps) {
    return (
        <div className="space-y-8 mt-2">
            <div className="grid grid-cols-2 gap-x-6 gap-y-8">
                {/* % Complete */}
                <div className="space-y-2.5">
                    <label htmlFor="percent_complete" className="text-xs font-semibold uppercase tracking-wider text-muted-foreground/80">
                        % Complete
                    </label>
                    <div className="relative flex items-center">
                        <Input
                            id="percent_complete"
                            type="number"
                            min={0}
                            max={100}
                            value={localData.percent_complete ?? 0}
                            onChange={(e) => setLocalData({ ...localData, percent_complete: Number(e.target.value) })}
                            onBlur={() => handleBlur("percent_complete")}
                            className="pr-8 bg-transparent transition-all border-border/60 focus-visible:border-primary focus-visible:ring-1 focus-visible:ring-primary/30"
                        />
                        <span className="absolute right-3 text-sm text-muted-foreground/50 pointer-events-none">%</span>
                    </div>
                </div>

                {/* Start Date */}
                <div className="space-y-2.5">
                    <label htmlFor="start_date" className="text-xs font-semibold uppercase tracking-wider text-muted-foreground/80">
                        Start Date
                    </label>
                    <Input
                        id="start_date"
                        type="date"
                        value={localData.start_date ?? ""}
                        onChange={(e) => setLocalData({ ...localData, start_date: e.target.value })}
                        onBlur={() => handleBlur("start_date")}
                        className="bg-transparent transition-all border-border/60 focus-visible:border-primary focus-visible:ring-1 focus-visible:ring-primary/30 text-foreground"
                    />
                </div>

                {/* Duration */}
                <div className="space-y-2.5 col-span-2 sm:col-span-1">
                    <label htmlFor="duration" className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground/80 hover:text-muted-foreground transition-colors">
                        Duration
                        <span className="text-[10px] font-medium normal-case bg-muted/60 px-1.5 py-0.5 rounded text-muted-foreground">mins</span>
                    </label>
                    <Input
                        id="duration"
                        type="number"
                        value={localData.duration ?? 0}
                        onChange={(e) => setLocalData({ ...localData, duration: Number(e.target.value) })}
                        onBlur={() => handleBlur("duration")}
                        disabled={task.is_summary}
                        className="bg-transparent transition-all border-border/60 focus-visible:border-primary focus-visible:ring-1 focus-visible:ring-primary/30 disabled:opacity-50 disabled:bg-muted/30"
                    />
                </div>

                {/* Color (summary tasks only) */}
                {task.is_summary && (
                    <div className="space-y-2.5">
                        <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground/80">
                            Gantt Color
                        </label>
                        <ColorPicker
                            value={task.color ?? null}
                            onChange={(color) => onColorChange?.(color)}
                        />
                    </div>
                )}
            </div>

            {/* Notes */}
            <div className="space-y-3 pt-2">
                <label htmlFor="notes" className="text-xs font-semibold uppercase tracking-wider text-muted-foreground/80">
                    Notes
                </label>
                <div className="relative group">
                    <Textarea
                        id="notes"
                        placeholder="Add task notes..."
                        value={localData.notes ?? ""}
                        onChange={(e) => setLocalData({ ...localData, notes: e.target.value })}
                        onBlur={() => handleBlur("notes")}
                        className="min-h-[140px] resize-y bg-transparent placeholder:text-muted-foreground/40 border-border/60 transition-all focus-visible:border-primary focus-visible:ring-1 focus-visible:ring-primary/30 leading-relaxed"
                    />
                </div>
            </div>
        </div>
    );
}
